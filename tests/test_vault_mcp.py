"""vault_mcp.py driven as a subprocess over stdio, as an MCP client would."""
import hashlib
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import unittest

from tests.fixture import BODY, SCRIPTS, VaultCase, run_script, write

SERVER = os.path.join(SCRIPTS, "vault_mcp.py")
CANARY = "zebracanary"  # a word that must never leave a restricted page
INIT = {"protocolVersion": "2025-11-25", "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"}}
MODERN_META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
               "io.modelcontextprotocol/clientCapabilities": {},
               "io.modelcontextprotocol/clientInfo": {"name": "test", "version": "0"}}


class Client:
    """One server process. `lines` keeps every raw line the server wrote to stdout."""

    def __init__(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        self.p = subprocess.Popen([sys.executable, SERVER, *map(str, args)], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.lines, self.q, self.next_id = [], queue.Queue(), 1
        self.err = []
        threading.Thread(target=self._pump, daemon=True).start()
        threading.Thread(target=lambda: self.err.append(self.p.stderr.read()), daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            self.lines.append(line)
            self.q.put(line)
        self.q.put(None)

    def raw(self, data):
        self.p.stdin.write(data if data.endswith(b"\n") else data + b"\n")
        self.p.stdin.flush()

    def send(self, obj):
        self.raw(json.dumps(obj).encode("utf-8"))

    def recv(self, timeout=20):
        line = self.q.get(timeout=timeout)
        return None if line is None else json.loads(line)

    def silent(self, wait=0.5):
        """True if the server sends nothing in `wait` seconds."""
        try:
            self.q.get(timeout=wait)
            return False
        except queue.Empty:
            return True

    def rpc(self, method, params=None, id_=None):
        id_ = id_ if id_ is not None else self.next_id
        if isinstance(id_, int):
            self.next_id = max(self.next_id, id_ + 1)
        msg = {"jsonrpc": "2.0", "id": id_, "method": method}
        if params is not None:
            msg["params"] = params
        self.send(msg)
        resp = self.recv()
        assert resp is not None and resp.get("id") == id_, resp
        return resp

    def handshake(self):
        r = self.rpc("initialize", INIT)
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return r

    def call(self, name, **args):
        return self.rpc("tools/call", {"name": name, "arguments": args})

    def tool(self, name, **args):
        """(isError, parsed JSON or text) of a tool call."""
        r = self.call(name, **args)
        res = r["result"]
        text = res["content"][0]["text"]
        if res["isError"]:
            return True, text
        return False, json.loads(text)

    def close(self):
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.p.stdout.close()
        self.p.stderr.close()
        return self.p.returncode


def page(front, body=None):
    return f"---\n{front}\n---\n# T\n{body or BODY}\n"


class McpCase(VaultCase):
    def setUp(self):
        super().setUp()
        write(self.vault, "wiki/private.md", page("type: concept\nsensitivity: private", f"{BODY} privateword"))
        write(self.vault, "wiki/secret.md", page("type: concept\nsensitivity: restricted\ntitle: Alpha",
                                                 f"{BODY} {CANARY} plainword [[alpha]]"))
        write(self.vault, "wiki/secret2.md", page("type: concept\nSensitivity : Restricted", f"{BODY} {CANARY} capitalword"))
        write(self.vault, "wiki/secret3.md", page("type: concept\nsensitivity: confidential", f"{BODY} {CANARY} unrecognizedword"))
        write(self.vault, "wiki/secret4.md", page('type: concept\nsensitivity: "restricted"', f"{BODY} {CANARY} quotedword"))
        write(self.vault, "wiki/linker.md", page("type: concept", f"{BODY} [[secret]] [[Missing Here]]"))
        self.clients = []

    def tearDown(self):
        for c in self.clients:
            c.close()

    def start(self, *extra, handshake=True):
        c = Client(self.vault, *extra)
        self.clients.append(c)
        if handshake:
            c.handshake()
        return c


class Protocol(McpCase):
    def test_initialize_echoes_supported_version(self):
        for ver in ("2025-11-25", "2025-06-18"):
            c = self.start(handshake=False)
            r = c.rpc("initialize", dict(INIT, protocolVersion=ver))["result"]
            self.assertEqual(r["protocolVersion"], ver)

    def test_initialize_unknown_version_gets_latest_supported(self):
        for ver in ("1999-01-01", "2026-07-28", "2025-03-26", "2024-11-05", "2099-12-31", ""):
            c = self.start(handshake=False)
            r = c.rpc("initialize", dict(INIT, protocolVersion=ver))
            if ver == "":
                self.assertEqual(r["error"]["code"], -32602)
            else:
                self.assertEqual(r["result"]["protocolVersion"], "2025-11-25")

    def test_initialize_advertises_only_tools(self):
        r = self.start(handshake=False).rpc("initialize", INIT)["result"]
        self.assertEqual(r["capabilities"], {"tools": {}})
        self.assertEqual(r["serverInfo"]["name"], "second-brain-vault")
        self.assertIsInstance(r["serverInfo"]["version"], str)

    def test_initialize_bad_params(self):
        c = self.start(handshake=False)
        for params in ({}, {"protocolVersion": 5, "capabilities": {}, "clientInfo": {}},
                       {"protocolVersion": "2025-11-25", "clientInfo": {}},
                       {"protocolVersion": "2025-11-25", "capabilities": {}}, []):
            r = c.rpc("initialize", params)
            self.assertEqual(r["error"]["code"], -32602, params)

    def test_tools_before_initialize_refused(self):
        c = self.start(handshake=False)
        self.assertEqual(c.rpc("tools/list")["error"]["code"], -32600)
        self.assertEqual(c.rpc("tools/call", {"name": "health"})["error"]["code"], -32600)
        self.assertEqual(c.rpc("ping")["result"], {})

    def test_initialized_notification_gets_no_reply_and_ping_works(self):
        c = self.start(handshake=False)
        c.rpc("initialize", INIT)
        c.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertTrue(c.silent())
        self.assertEqual(c.rpc("ping"), {"jsonrpc": "2.0", "id": 2, "result": {}})

    def test_ping_keeps_string_and_integer_ids(self):
        c = self.start()
        self.assertEqual(c.rpc("ping", id_="abc")["id"], "abc")
        self.assertEqual(c.rpc("ping", id_=0)["id"], 0)

    def test_unknown_method_and_notification(self):
        c = self.start()
        r = c.rpc("resources/list")
        self.assertEqual(r["error"]["code"], -32601)
        self.assertEqual(c.rpc("prompts/list")["error"]["code"], -32601)
        self.assertEqual(c.rpc("tools/nope")["error"]["code"], -32601)
        c.send({"jsonrpc": "2.0", "method": "notifications/whatever", "params": {"a": 1}})
        c.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}})
        c.send({"jsonrpc": "2.0", "method": "no/such/method"})  # no id: never answered
        self.assertTrue(c.silent())
        self.assertEqual(c.rpc("ping")["result"], {})

    def test_malformed_input(self):
        c = self.start()
        for raw in (b"{not json", b'{"jsonrpc":"2.0","id":1,"method":', b"\xff\xfe\x00", b"nul\x00l", b"[1,2"):
            c.raw(raw)
            r = c.recv()
            self.assertEqual(r["error"]["code"], -32700, raw)
            self.assertIsNone(r["id"])
        for obj in (5, "x", None, [], {"id": 1, "method": "ping"}, {"jsonrpc": "1.0", "id": 1, "method": "ping"},
                    [{"jsonrpc": "2.0", "id": 1, "method": "ping"}],
                    {"jsonrpc": "2.0", "id": None, "method": "ping"},
                    {"jsonrpc": "2.0", "id": True, "method": "ping"},
                    {"jsonrpc": "2.0", "id": [1], "method": "ping"}):
            c.send(obj)
            r = c.recv()
            self.assertEqual(r["error"]["code"], -32600, obj)
            self.assertIsNone(r["id"], obj)
        c.send({"jsonrpc": "2.0", "id": 5, "method": "ping", "params": [1]})
        self.assertEqual(c.recv()["error"]["code"], -32602)
        c.send({"jsonrpc": "2.0", "id": 6, "method": 7})  # the id is readable, so it is echoed
        r = c.recv()
        self.assertEqual((r["id"], r["error"]["code"]), (6, -32600))
        c.raw(b"")  # blank lines are ignored
        c.send({"jsonrpc": "2.0", "id": 9, "result": {}})  # a response from the client is ignored
        self.assertTrue(c.silent())
        self.assertEqual(c.rpc("ping")["result"], {})

    def test_oversized_message_does_not_stop_the_server(self):
        c = self.start()
        c.raw(b"x" * (4 * 1024 * 1024 + 100))
        self.assertEqual(c.recv()["error"]["code"], -32600)
        self.assertEqual(c.rpc("ping")["result"], {})

    def test_crlf_line_endings_accepted(self):
        c = self.start()
        c.raw(b'{"jsonrpc":"2.0","id":77,"method":"ping"}\r\n')
        self.assertEqual(c.recv()["id"], 77)

    def test_exits_zero_when_stdin_closes(self):
        self.assertEqual(self.start().close(), 0)

    def test_stdout_is_protocol_only(self):
        dead = socket.socket()
        dead.bind(("127.0.0.1", 0))
        port = dead.getsockname()[1]
        dead.close()
        c = self.start("--embed-url", f"http://127.0.0.1:{port}")
        c.raw(b"garbage")
        c.recv()
        c.tool("search", query="alpha")
        c.tool("health")
        c.tool("read_page", path="../x.md")
        c.call("nope")
        c.rpc("tools/list")
        c.close()
        self.assertGreater(len(c.lines), 5)
        for line in c.lines:
            self.assertTrue(line.endswith(b"\n"))
            msg = json.loads(line)  # every line is one JSON value
            self.assertEqual(msg["jsonrpc"], "2.0")
            self.assertTrue("result" in msg or "error" in msg)
        self.assertIn(b"vault_mcp", b"".join(c.err))  # logs went to stderr instead


class ModernEra(McpCase):
    def req(self, c, method, params=None, meta=None):
        p = dict(params or {})
        p["_meta"] = MODERN_META if meta is None else meta
        return c.rpc(method, p)

    def test_discover(self):
        c = self.start(handshake=False)
        r = self.req(c, "server/discover")["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertEqual(r["supportedVersions"], ["2026-07-28"])
        self.assertEqual(r["capabilities"], {"tools": {}})
        self.assertGreaterEqual(r["ttlMs"], 0)
        self.assertIn(r["cacheScope"], ("public", "private"))
        self.assertEqual(r["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "second-brain-vault")

    def test_tools_without_handshake(self):
        c = self.start(handshake=False)
        r = self.req(c, "tools/list")["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertEqual(len(r["tools"]), 7)
        self.assertIn("ttlMs", r)
        r = self.req(c, "tools/call", {"name": "health", "arguments": {}})["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertFalse(r["isError"])

    def test_unsupported_version(self):
        c = self.start(handshake=False)
        meta = dict(MODERN_META, **{"io.modelcontextprotocol/protocolVersion": "1900-01-01"})
        r = self.req(c, "tools/list", meta=meta)["error"]
        self.assertEqual(r["code"], -32022)
        self.assertEqual(r["data"], {"supported": ["2026-07-28"], "requested": "1900-01-01"})

    def test_missing_required_meta(self):
        c = self.start(handshake=False)
        no_caps = {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}
        no_ver = {"io.modelcontextprotocol/clientCapabilities": {}}
        for meta in (no_caps, no_ver, dict(MODERN_META, **{"io.modelcontextprotocol/clientCapabilities": 3})):
            self.assertEqual(self.req(c, "tools/list", meta=meta)["error"]["code"], -32602, meta)
        self.assertEqual(c.rpc("server/discover")["error"]["code"], -32602)  # no _meta at all

    def test_ping_and_initialize_are_gone(self):
        c = self.start(handshake=False)
        self.assertEqual(self.req(c, "ping")["error"]["code"], -32601)
        self.assertEqual(self.req(c, "initialize", dict(INIT))["error"]["code"], -32601)

    def test_tool_failure_is_a_result(self):
        c = self.start(handshake=False)
        r = self.req(c, "tools/call", {"name": "read_page", "arguments": {"path": "../x.md"}})["result"]
        self.assertTrue(r["isError"])
        self.assertEqual(r["resultType"], "complete")


class ToolList(McpCase):
    def test_schemas(self):
        tools = self.start().rpc("tools/list")["result"]["tools"]
        self.assertEqual({t["name"] for t in tools},
                         {"search", "read_page", "backlinks", "stale", "duplicates", "health", "lifecycle_status"})
        for t in tools:
            s = t["inputSchema"]
            self.assertEqual(s["type"], "object", t["name"])
            self.assertIs(s["additionalProperties"], False, t["name"])
            self.assertTrue(t["description"] and t["title"])
            self.assertIs(t["annotations"]["readOnlyHint"], True)
            self.assertIs(t["annotations"]["destructiveHint"], False)
            for req in s.get("required", []):
                self.assertIn(req, s["properties"])
            for prop in s.get("properties", {}).values():
                self.assertIn(prop["type"], ("string", "integer"))
                self.assertTrue(prop["description"])
            self.assertRegex(t["name"], r"^[A-Za-z0-9_.-]{1,128}$")
        by = {t["name"]: t["inputSchema"] for t in tools}
        self.assertEqual(by["search"]["required"], ["query"])
        self.assertEqual(by["read_page"]["required"], ["path"])
        self.assertEqual(by["backlinks"]["required"], ["path"])
        self.assertNotIn("required", by["stale"])
        for name in ("duplicates", "health", "lifecycle_status"):
            self.assertEqual(by[name], {"type": "object", "additionalProperties": False})

    def test_no_write_tools(self):
        names = {t["name"] for t in self.start().rpc("tools/list")["result"]["tools"]}
        for bad in ("write", "edit", "delete", "create", "update", "append", "move", "run", "exec"):
            self.assertFalse([n for n in names if bad in n.lower()], bad)

    def test_cursor_rejected(self):
        self.assertEqual(self.start().rpc("tools/list", {"cursor": "x"})["error"]["code"], -32602)

    def test_list_is_stable(self):
        c = self.start()
        self.assertEqual(c.rpc("tools/list")["result"], c.rpc("tools/list")["result"])


class CallProtocol(McpCase):
    def test_unknown_tool_is_a_protocol_error(self):
        r = self.start().call("nope")
        self.assertEqual(r["error"]["code"], -32602)
        self.assertIn("Unknown tool", r["error"]["message"])

    def test_bad_call_params(self):
        c = self.start()
        for params in ({}, {"name": 5}, {"name": ["search"]}):
            self.assertEqual(c.rpc("tools/call", params)["error"]["code"], -32602, params)

    def test_bad_arguments_are_tool_errors(self):
        c = self.start()
        for name, args in (("search", {}), ("search", {"query": 5}), ("search", {"query": ""}),
                           ("search", {"query": "a", "limit": 0}), ("search", {"query": "a", "limit": 999}),
                           ("search", {"query": "a", "limit": "3"}), ("search", {"query": "a", "limit": True}),
                           ("search", {"query": "a", "extra": 1}), ("search", {"query": "x" * 1001}),
                           ("search", {"query": "   "}),
                           ("read_page", {}), ("read_page", {"path": 7}), ("read_page", {"path": ""}),
                           ("backlinks", {}), ("stale", {"days": -1}), ("stale", {"days": 1.5}),
                           ("health", {"x": 1}), ("lifecycle_status", {"x": 1})):
            err, text = c.tool(name, **args)
            self.assertTrue(err, (name, args))
            self.assertIsInstance(text, str)
        r = c.rpc("tools/call", {"name": "search", "arguments": "nope"})
        self.assertTrue(r["result"]["isError"])
        r = c.rpc("tools/call", {"name": "health"})  # arguments may be omitted
        self.assertFalse(r["result"]["isError"])

    def test_result_shape(self):
        r = self.start().call("health")["result"]
        self.assertEqual(set(r), {"content", "isError"})
        self.assertEqual(r["content"][0]["type"], "text")


class Search(McpCase):
    def test_hits_with_citations(self):
        err, d = self.start().tool("search", query="alpha")
        self.assertFalse(err)
        self.assertEqual(d["mode"], "bm25")
        self.assertEqual(d["hits"][0]["path"], "wiki/alpha.md")
        for h in d["hits"]:
            self.assertEqual(h["citation"], f"{h['path']}:{h['line']}")
            self.assertGreaterEqual(h["line"], 1)
        direct = json.loads(run_script("vault_search.py", self.vault, "alpha", "--json").stdout)
        self.assertEqual([h["path"] for h in d["hits"]], [h["path"] for h in direct["hits"]])

    def test_limit_and_no_hits(self):
        c = self.start()
        self.assertEqual(c.tool("search", query="alpha", limit=1)[1]["count"], 1)
        self.assertEqual(c.tool("search", query="qqqqnothing")[1], {"query": "qqqqnothing", "mode": "bm25",
                                                                    "count": 0, "hits": []})

    def test_private_flagged_restricted_hidden(self):
        c = self.start()
        d = c.tool("search", query="privateword")[1]
        self.assertEqual([h["path"] for h in d["hits"]], ["wiki/private.md"])
        self.assertTrue(d["hits"][0]["private"])
        # each word sits in a page body the search would find if the page were not refused
        direct = json.loads(run_script("vault_search.py", self.vault, "plainword", "--include-restricted", "--json").stdout)
        self.assertEqual(direct["count"], 1)  # the control: the word is searchable
        for q in (CANARY, "plainword", "capitalword", "unrecognizedword", "quotedword"):
            self.assertEqual(c.tool("search", query=q)[1]["count"], 0, q)

    def test_index_refreshes_on_change(self):
        c = self.start()
        self.assertEqual(c.tool("search", query="newtopicword")[1]["count"], 0)
        p = write(self.vault, "wiki/new.md", page("type: concept", f"{BODY} newtopicword"))
        self.assertEqual(c.tool("search", query="newtopicword")[1]["count"], 1)
        # an edit that makes the page restricted removes it from the next search
        write(self.vault, "wiki/new.md", page("type: concept\nsensitivity: restricted", f"{BODY} newtopicword changed"))
        st = os.stat(p)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        self.assertEqual(c.tool("search", query="newtopicword")[1]["count"], 0)
        os.remove(p)
        self.assertEqual(c.tool("search", query="newtopicword")[1]["count"], 0)

    def test_unreachable_embed_server_falls_back(self):
        dead = socket.socket()
        dead.bind(("127.0.0.1", 0))
        port = dead.getsockname()[1]
        dead.close()
        c = self.start("--embed-url", f"http://127.0.0.1:{port}")
        d = c.tool("search", query="alpha")[1]
        self.assertEqual(d["mode"], "bm25")
        self.assertTrue(d["hits"])

    def test_symlinked_file_outside_vault_is_not_indexed(self):
        outside = os.path.join(self.tmp, "outside.md")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write(f"# Out\n{BODY} outsideword\n")
        symlink_or_skip(outside, os.path.join(self.vault, "wiki", "link.md"))
        c = self.start()
        self.assertEqual(c.tool("search", query="outsideword")[1]["count"], 0)
        self.assertNotIn("wiki/link.md", json.dumps(c.tool("health")[1]))


def symlink_or_skip(target, link, directory=False):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError, AttributeError):
        raise unittest.SkipTest("cannot create symlinks here") from None


class ReadPage(McpCase):
    def test_returns_text_and_frontmatter(self):
        err, d = self.start().tool("read_page", path="wiki/beta.md")
        self.assertFalse(err)
        self.assertEqual(d["path"], "wiki/beta.md")
        self.assertEqual(d["frontmatter"], {"type": "entity", "aliases": ["Bee", "Beta page"]})
        self.assertTrue(d["text"].startswith("---\ntype: entity"))
        self.assertIn("# Beta", d["text"])
        self.assertEqual(d["sensitivity"], "normal")
        self.assertFalse(d["private"])
        self.assertFalse(d["truncated"])
        # line numbers from search citations point at the same line of `text`
        hit = self.start().tool("search", query="beta")[1]["hits"][0]
        self.assertEqual(hit["path"], "wiki/beta.md")
        self.assertIn("Beta", d["text"].split("\n")[hit["line"] - 1])

    def test_crlf_and_bom_pages(self):
        c = self.start()
        d = c.tool("read_page", path="wiki/gamma.md")[1]
        self.assertEqual(d["frontmatter"], {"type": "person"})
        self.assertNotIn("\r", d["text"])
        d = c.tool("read_page", path="wiki/bom.md")[1]
        self.assertFalse(d["text"].startswith("\ufeff"))
        self.assertEqual(d["frontmatter"]["aliases"], ["Bom alias"])

    def test_path_spellings_that_stay_inside(self):
        c = self.start()
        for p in ("wiki/beta.md", "./wiki/beta.md", "wiki//beta.md", "wiki\\beta.md", "wiki/./beta.md"):
            err, d = c.tool("read_page", path=p)
            self.assertFalse(err, p)
            self.assertEqual(d["path"], "wiki/beta.md")

    def test_private_is_flagged(self):
        d = self.start().tool("read_page", path="wiki/private.md")[1]
        self.assertTrue(d["private"])
        self.assertEqual(d["sensitivity"], "private")
        self.assertIn("private", d["notice"])
        self.assertIn("privateword", d["text"])

    def test_restricted_is_refused(self):
        c = self.start()
        for name in ("secret", "secret2", "secret3", "secret4"):
            err, text = c.tool("read_page", path=f"wiki/{name}.md")
            self.assertTrue(err, name)
            self.assertIn("restricted", text)
            self.assertNotIn(CANARY, text)
        err, text = c.tool("read_page", path="wiki/secret.md")
        self.assertEqual(text.split(":")[0], "Refused")

    def test_missing_and_non_markdown(self):
        c = self.start()
        err, text = c.tool("read_page", path="wiki/nothere.md")
        self.assertTrue(err)
        self.assertIn("No such page", text)
        write(self.vault, "wiki/data.txt", "plain\n")
        write(self.vault, "wiki/.env", "KEY=1\n")
        for p in ("wiki/data.txt", "wiki/.env", "wiki", "wiki/"):
            self.assertTrue(c.tool("read_page", path=p)[0], p)
        self.assertTrue(c.tool("read_page", path="wiki/alpha.md/")[0] is False)  # a trailing slash is ignored

    def test_large_page_is_truncated(self):
        write(self.vault, "wiki/big.md", "# Big\n" + "word " * 100000 + "\n")
        d = self.start().tool("read_page", path="wiki/big.md")[1]
        self.assertTrue(d["truncated"])
        self.assertEqual(len(d["text"]), 200000)


class Traversal(McpCase):
    REFUSED = "outside the vault or in a protected location"

    def refused(self, c, path, msg=None):
        err, text = c.tool("read_page", path=path)
        self.assertTrue(err, path)
        self.assertIn(msg or self.REFUSED, text, path)
        return text

    def test_dotdot_and_absolute(self):
        c = self.start()
        outside = os.path.join(self.tmp, "outside.md")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("# Out\noutsideword\n")
        for p in ("../outside.md", "wiki/../../outside.md", "wiki/../../../../etc/passwd", "..", "../",
                  "..\\outside.md", "wiki\\..\\..\\outside.md", "wiki/..", "./../outside.md",
                  outside, "/etc/passwd", "//server/share/x.md", "\\\\server\\share\\x.md", "\\windows\\x.md",
                  "C:\\Windows\\win.ini", "c:/x.md", "C:x.md", os.path.join(self.vault, "wiki", "alpha.md")):
            text = self.refused(c, p)
            self.assertNotIn("outsideword", text)
            self.assertNotIn(self.tmp, text)  # no absolute path in the message
        for p in ("wiki/alpha.md\x00.txt", "wiki/alpha.md\n", "wiki/al\x01pha.md"):
            self.refused(c, p)

    def test_windows_special_names(self):
        c = self.start()
        for p in ("wiki/alpha.md::$DATA", "wiki/alpha.md:stream", "wiki/alpha.md.", "wiki/alpha.md ",
                  "wiki/al?pha.md", "wiki/*.md", "wiki/<a>.md", 'wiki/"a".md', "wiki/a|b.md"):
            self.refused(c, p)

    def test_protected_folders(self):
        write(self.vault, ".git/config", "[core]\n")
        write(self.vault, ".git/notes.md", f"# git\n{BODY}\n")
        write(self.vault, ".claude/skills/x.md", f"# skill\n{BODY}\n")
        write(self.vault, ".claude/CLAUDE.md", f"# rules\n{BODY}\n")
        write(self.vault, ".obsidian/workspace.md", f"# w\n{BODY}\n")
        write(self.vault, ".cache/embeddings.md", f"# e\n{BODY}\n")
        write(self.vault, "wiki/.hidden.md", f"# h\n{BODY}\n")
        write(self.vault, "wiki/.git/x.md", f"# g\n{BODY}\n")
        c = self.start()
        for p in (".git/config", ".git/notes.md", ".git/HEAD", ".claude/skills/x.md", ".claude/CLAUDE.md",
                  ".obsidian/workspace.md", ".cache/embeddings.md", "wiki/.hidden.md", "wiki/.git/x.md",
                  ".GIT/notes.md", ".Claude/CLAUDE.md", "journal/day.md", "Journal/day.md", "JOURNAL/day.md",
                  "wiki/../.git/notes.md", ".git/../.git/notes.md", ".git\\notes.md"):
            self.refused(c, p)

    def test_raw_needs_the_flag(self):
        write(self.vault, "raw/clip.md", f"# Clip\n{BODY} rawword\n")
        write(self.vault, "raw/restricted.md", page("sensitivity: restricted", BODY))
        c = self.start()
        for p in ("raw/clip.md", "RAW/clip.md", "Raw/clip.md", "raw/source.md", "./raw/clip.md", "wiki/../raw/clip.md"):
            self.refused(c, p)
        c = self.start("--allow-raw")
        d = c.tool("read_page", path="raw/clip.md")[1]
        self.assertIn("rawword", d["text"])
        # the flag opens raw/ only: restricted pages in it, journal/ and dot folders stay closed
        self.assertIn("restricted", c.tool("read_page", path="raw/restricted.md")[1])
        for p in ("journal/day.md", ".git/config", ".claude/x.md"):
            self.refused(c, p)

    def test_symlink_to_outside_file(self):
        outside = os.path.join(self.tmp, "outside.md")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("# Out\noutsideword\n")
        symlink_or_skip(outside, os.path.join(self.vault, "wiki", "escape.md"))
        text = self.refused(self.start(), "wiki/escape.md")
        self.assertNotIn("outsideword", text)

    def test_symlink_to_outside_directory(self):
        outdir = os.path.join(self.tmp, "outdir")
        os.makedirs(outdir)
        with open(os.path.join(outdir, "page.md"), "w", encoding="utf-8") as fh:
            fh.write("# Out\noutsideword\n")
        symlink_or_skip(outdir, os.path.join(self.vault, "wiki", "outlink"), directory=True)
        c = self.start()
        self.refused(c, "wiki/outlink/page.md")
        self.assertEqual(c.tool("search", query="outsideword")[1]["count"], 0)

    def test_symlink_into_protected_folders(self):
        write(self.vault, ".git/notes.md", f"# git\n{BODY} gitword\n")
        write(self.vault, "journal/entry.md", f"# j\n{BODY} journalword\n")
        symlink_or_skip(os.path.join(self.vault, ".git", "notes.md"), os.path.join(self.vault, "wiki", "g.md"))
        symlink_or_skip(os.path.join(self.vault, "journal"), os.path.join(self.vault, "wiki", "jl"), directory=True)
        symlink_or_skip("../journal/entry.md", os.path.join(self.vault, "wiki", "je.md"))
        c = self.start()
        for p in ("wiki/g.md", "wiki/jl/entry.md", "wiki/je.md"):
            self.refused(c, p)
        for q in ("gitword", "journalword"):
            self.assertEqual(c.tool("search", query=q)[1]["count"], 0)

    def test_hardlinks_are_refused(self):
        write(self.vault, "wiki/hl-src.md", f"# H\n{BODY} hardlinkword\n")
        try:
            os.link(os.path.join(self.vault, "wiki", "hl-src.md"), os.path.join(self.vault, "wiki", "hl-copy.md"))
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("cannot create hard links here")
        c = self.start()
        for p in ("wiki/hl-src.md", "wiki/hl-copy.md"):
            self.refused(c, p)
        self.assertEqual(c.tool("search", query="hardlinkword")[1]["count"], 0)

    def test_symlink_inside_vault_is_allowed(self):
        symlink_or_skip(os.path.join(self.vault, "wiki", "beta.md"), os.path.join(self.vault, "wiki", "beta-link.md"))
        err, d = self.start().tool("read_page", path="wiki/beta-link.md")
        self.assertFalse(err)
        self.assertIn("# Beta", d["text"])

    def test_symlink_to_restricted_page_still_refused(self):
        symlink_or_skip(os.path.join(self.vault, "wiki", "secret.md"), os.path.join(self.vault, "wiki", "peek.md"))
        err, text = self.start().tool("read_page", path="wiki/peek.md")
        self.assertTrue(err)
        self.assertNotIn(CANARY, text)

    def test_vault_given_as_a_symlink(self):
        link = os.path.join(self.tmp, "vault-link")
        symlink_or_skip(self.vault, link, directory=True)
        c = Client(link)
        self.clients.append(c)
        c.handshake()
        self.assertFalse(c.tool("read_page", path="wiki/beta.md")[0])
        self.refused(c, "../vault/wiki/beta.md")


class Backlinks(McpCase):
    def test_backlinks(self):
        err, d = self.start().tool("backlinks", path="wiki/alpha.md")
        self.assertFalse(err)
        self.assertEqual([b["path"] for b in d["backlinks"] if not b.get("restricted")],
                         ["index.md", "wiki/beta.md", "wiki/gamma.md"])
        self.assertEqual(d["count"], 4)

    def test_restricted_source_is_path_only(self):
        d = self.start().tool("backlinks", path="wiki/alpha.md")[1]
        entry = [b for b in d["backlinks"] if b["path"] == "wiki/secret.md"]
        self.assertEqual(entry, [{"path": "wiki/secret.md", "restricted": True}])

    def test_alias_and_anchor_links_resolve(self):
        d = self.start().tool("backlinks", path="wiki/bom.md")[1]
        self.assertEqual([b["path"] for b in d["backlinks"]], ["index.md"])

    def test_restricted_target_refused(self):
        err, text = self.start().tool("backlinks", path="wiki/secret.md")
        self.assertTrue(err)
        self.assertIn("restricted", text)

    def test_not_a_counted_page(self):
        c = self.start()
        for p in ("wiki/README.md", "README.md", "templates/page.md", "archive/old.md", "wiki/none.md"):
            self.assertTrue(c.tool("backlinks", path=p)[0], p)

    def test_traversal_refused(self):
        c = self.start()
        for p in ("../x.md", "/etc/passwd", ".git/config", "raw/source.md", "journal/day.md"):
            err, text = c.tool("backlinks", path=p)
            self.assertTrue(err, p)


class DashboardTools(McpCase):
    def dash(self, *extra):
        p = run_script("dashboard.py", self.vault, "--json", *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_stale_matches_dashboard(self):
        write(self.vault, "wiki/old.md", page("type: concept\nupdated: 2020-01-01"))
        c = self.start()
        err, d = c.tool("stale", days=365)
        self.assertFalse(err)
        want = self.dash("--stale-days", "365")["stale"]
        self.assertEqual(d["pages"], want)
        self.assertEqual(d["days"], 365)
        self.assertIn("wiki/old.md", [p["page"] for p in d["pages"]])
        self.assertEqual(c.tool("stale")[1]["days"], 90)
        self.assertEqual(c.tool("stale", days=0)[1]["count"] >= 1, True)

    def test_duplicates_match_dashboard_and_hide_restricted_names(self):
        write(self.vault, "wiki/dup-a.md", page("type: concept\ntitle: Same Name"))
        write(self.vault, "wiki/dup-b.md", page("type: concept\ntitle: same-name"))
        write(self.vault, "wiki/zzsecret.md", page("type: concept\nSensitivity: restricted\ntitle: Hidden Title"))
        write(self.vault, "wiki/zzsecret-b.md", page("type: concept\ntitle: hidden title"))
        c = self.start()
        d = c.tool("duplicates")[1]
        names = {g["name"]: g["pages"] for g in d["groups"]}
        self.assertEqual(names["samename"], ["wiki/dup-a.md", "wiki/dup-b.md"])
        self.assertNotIn("hiddentitle", names)
        self.assertEqual(names["(restricted)"], ["wiki/zzsecret-b.md", "wiki/zzsecret.md"])
        self.assertNotIn("hiddentitle", json.dumps(d))

    def test_health_matches_dashboard(self):
        d = self.start().tool("health")[1]
        want = self.dash()
        for key in ("counts", "lifecycle", "folders", "most_linked", "needs_owner_open", "orphans", "stubs"):
            if key == "counts":
                self.assertEqual({k: v for k, v in d[key].items() if k != "restricted"},
                                 {k: v for k, v in want[key].items() if k != "restricted"})
            elif key in ("orphans", "stubs"):
                self.assertEqual(d[key], want[key])
            else:
                self.assertEqual(d[key], want[key])
        self.assertEqual(d["counts"]["restricted"], 4)  # secret, secret2, secret3 (unrecognised), secret4

    def test_health_hides_targets_of_restricted_pages(self):
        write(self.vault, "wiki/s5.md", page("type: concept\nSensitivity: restricted", f"{BODY} [[Hidden Target Name]]"))
        d = self.start().tool("health")[1]
        self.assertNotIn("Hidden Target Name", json.dumps(d))
        self.assertIn({"page": "wiki/s5.md", "target": None}, d["broken"])
        self.assertIn({"page": "wiki/linker.md", "target": "Missing Here"}, d["broken"])

    def test_lifecycle_matches_dashboard_funnel(self):
        for name, status, kind in (("i1", "new", "idea"), ("i2", "considering", "idea"), ("p1", "planned", "experiment"),
                                   ("e1", "active", "experiment"), ("e2", "reviewing", "experiment"),
                                   ("a1", "adopted", "experiment"), ("d1", "dropped", "idea"),
                                   ("x1", "promoted", "idea"), ("o1", "weird", "experiment"),
                                   ("l1", "idea", "note")):
            write(self.vault, f"wiki/{name}.md", page(f"type: {kind}\nstatus: {status}"))
        write(self.vault, "wiki/hid.md", page("type: idea\nstatus: new\nsensitivity: restricted", f"{BODY} {CANARY}"))
        d = self.start().tool("lifecycle_status")[1]
        want = self.dash()["lifecycle"]
        self.assertEqual({k: v["count"] for k, v in d["stages"].items()}, {k: v for k, v in want["stages"].items()})
        self.assertEqual(d["promoted"], want["promoted"])
        self.assertEqual(d["other"], want["other"])
        idea = {p["path"]: p for p in d["stages"]["idea"]["pages"]}
        self.assertEqual(sorted(idea), ["wiki/hid.md", "wiki/i1.md", "wiki/i2.md", "wiki/l1.md"])
        self.assertEqual(idea["wiki/i1.md"], {"path": "wiki/i1.md", "title": "i1", "status": "new"})
        self.assertEqual(idea["wiki/hid.md"], {"path": "wiki/hid.md", "restricted": True})
        self.assertEqual(d["statuses"]["idea"], ["new", "considering", "idea"])

    def test_restricted_bodies_never_appear_in_any_tool(self):
        write(self.vault, "wiki/s6.md", page("type: idea\nstatus: new\nsensitivity: restricted\nupdated: 2019-05-05",
                                             f"{BODY} {CANARY}"))
        c = self.start()
        outputs = []
        for name, args in (("search", {"query": "secret"}), ("search", {"query": "alpha"}),
                           ("read_page", {"path": "wiki/secret.md"}), ("read_page", {"path": "wiki/linker.md"}),
                           ("backlinks", {"path": "wiki/alpha.md"}), ("backlinks", {"path": "wiki/secret.md"}),
                           ("stale", {"days": 0}), ("duplicates", {}), ("health", {}), ("lifecycle_status", {})):
            outputs.append(json.dumps(c.call(name, **args)))
        self.assertFalse([o[:80] for o in outputs if CANARY in o])


class ReadOnly(McpCase):
    def snapshot(self):
        out = {}
        for dirpath, dirnames, names in os.walk(self.vault):
            for n in sorted(names + dirnames):
                p = os.path.join(dirpath, n)
                if os.path.isfile(p):
                    with open(p, "rb") as fh:
                        out[os.path.relpath(p, self.vault)] = (hashlib.sha256(fh.read()).hexdigest(),
                                                               os.stat(p).st_mtime_ns)
                else:
                    out[os.path.relpath(p, self.vault)] = None
        return out

    def test_nothing_in_the_vault_changes(self):
        before = self.snapshot()
        c = self.start()
        for name, args in (("search", {"query": "alpha"}), ("read_page", {"path": "wiki/alpha.md"}),
                           ("backlinks", {"path": "wiki/alpha.md"}), ("stale", {"days": 1}), ("duplicates", {}),
                           ("health", {}), ("lifecycle_status", {}), ("read_page", {"path": "../x"})):
            c.call(name, **args)
        c.close()
        self.assertEqual(self.snapshot(), before)

    def test_source_has_no_write_calls(self):
        with open(SERVER, encoding="utf-8") as fh:
            src = fh.read()
        for needle in ("os.remove", "os.unlink", "os.rename", "os.replace", "shutil", "os.makedirs", "os.mkdir",
                       "open(path, \"w", "'w'", "\"w\"", "\"a\"", "\"wb\"", "chmod", "subprocess"):
            body = src.split('"""', 2)[2]  # skip the module docstring
            self.assertNotIn(needle, body.replace('fdopen(proto_fd, "wb")', ""), needle)


class Cli(unittest.TestCase):
    def test_bad_vault(self):
        p = subprocess.run([sys.executable, SERVER, os.path.join(os.path.dirname(SERVER), "no-such-dir")],
                           capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, "")
        self.assertIn("not a directory", p.stderr)

    def test_usage(self):
        p = subprocess.run([sys.executable, SERVER], capture_output=True, text=True, timeout=30,
                           stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")

    def test_remote_embed_url_needs_the_flag(self):
        p = subprocess.run([sys.executable, SERVER, SCRIPTS, "--embed-url", "http://example.com:8080"],
                           capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("--allow-remote-embed", p.stderr)

    def test_empty_vault(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            c = Client(d)
            try:
                c.handshake()
                self.assertEqual(c.tool("search", query="x")[1]["count"], 0)
                self.assertEqual(c.tool("health")[1]["counts"]["pages"], 0)
            finally:
                c.close()


if __name__ == "__main__":
    unittest.main()
