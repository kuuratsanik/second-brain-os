#!/usr/bin/env python3
"""Read-only MCP server for a second-brain vault, over stdio.

Usage:
    python3 vault_mcp.py /path/to/vault [--embed-url URL] [--allow-raw]

Speaks the Model Context Protocol over standard input and output: JSON-RPC
2.0, one message per line. Nothing but protocol messages is written to stdout;
logs go to stderr. No dependencies; Python 3.9 or newer; Windows too.

Tools (all read-only): search, read_page, backlinks, stale, duplicates, health,
lifecycle_status. There is no write tool. The server never modifies the vault,
except that `--embed-url` lets vault_search.py keep its embedding cache in
VAULT/.cache/embeddings.json.

Protocol: implemented from the MCP specification, latest dated revision 2026-07-28,
fetched 2026-10-06 from the specification source in the
modelcontextprotocol/modelcontextprotocol repository on GitHub
(docs/specification/2026-07-28/, raw files; modelcontextprotocol.io itself was
blocked from the build environment). Pages used: changelog, basic/index,
basic/versioning, basic/transports/stdio, server/discover, server/tools and
server/utilities/caching. The previous revision, 2025-11-25, was read from the
same place (basic/lifecycle, basic/transports, basic/utilities/ping,
server/tools).

The 2026-07-28 revision removed the `initialize` handshake and `ping`, so this
server is dual-era, as basic/versioning allows:

* Modern (2026-07-28): a request whose params._meta carries
  `io.modelcontextprotocol/protocolVersion` is served on its own. Supported:
  `server/discover`, `tools/list`, `tools/call`. Results carry
  `resultType: "complete"` and the server identity in `_meta`; `tools/list` and
  `server/discover` carry `ttlMs` and `cacheScope`. An unknown version gets
  UnsupportedProtocolVersion (-32022) with data.supported and data.requested; a
  missing required `_meta` field gets -32602. `ping` is not part of this
  revision, so it is an unknown method there.
* Legacy (2025-11-25, 2025-06-18, 2025-03-26, 2024-11-05): `initialize`
  negotiates the version (the requested one if supported, else the latest the
  server supports, 2025-11-25), then `notifications/initialized`, `ping`,
  `tools/list`, `tools/call`. Only the `tools` capability is advertised, with no
  `listChanged`, since the tool list never changes. A `tools/*` request before
  `initialize` is refused with -32600.

Errors: -32700 parse error, -32600 invalid request (also batches, which the
spec dropped in 2025-06-18), -32601 unknown method, -32602 bad params (also an
unknown tool name, as the tools page shows), -32603 internal error. A tool that
fails, including bad arguments, returns a normal result with `isError: true`.

Security limits (a local, single-user threat model; the client launches this
process with the user's own rights):

* `read_page` takes a vault-relative `.md` path. It refuses absolute paths, drive
  letters, `..`, characters that Windows reads specially (`:` `<` `>` `"` `|`
  `?` `*`, trailing dot or space), and any path whose real location, after
  symlinks, is outside the vault. It refuses every dot-folder (`.git`,
  `.claude`, `.obsidian`, `.cache`), `journal/`, and `raw/` unless
  `--allow-raw` is given. Names are compared case-insensitively and again on
  the resolved path, and each ancestor is compared by file identity with the
  protected top-level folders (case-insensitive file systems, 8.3 names).
* Pages marked `sensitivity: restricted`, or with a sensitivity value this
  script does not recognise (fail closed), are never returned: not by
  read_page, not in search results, not in the text of any other tool. Only
  their paths can appear in lists, as in dashboard.py. `private` pages are
  returned and flagged.
* Files reachable only through a symlink that leaves the vault are not indexed.
* Output is capped (page text 200000 characters; lists 200 entries).

Exit codes: 0 when stdin closes, 1 for a bad vault path, 2 for a usage error.
"""
import argparse
import json
import os
import re
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import link_check as lc  # noqa: E402
import vault_search as vs  # noqa: E402
import dashboard as db  # noqa: E402

SERVER_NAME = "second-brain-vault"
SERVER_VERSION = "1.0.0"

MODERN_VERSIONS = ("2026-07-28",)
LEGACY_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPS = "io.modelcontextprotocol/clientCapabilities"
META_CLIENT = "io.modelcontextprotocol/clientInfo"
META_SERVER = "io.modelcontextprotocol/serverInfo"

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND = -32700, -32600, -32601
INVALID_PARAMS, INTERNAL_ERROR, UNSUPPORTED_VERSION = -32602, -32603, -32022

INSTRUCTIONS = (
    "Read-only access to a second-brain vault of markdown pages. Use `search` first, "
    "then `read_page` for the pages that matter, and cite claims as path:line. "
    "Pages marked sensitivity: restricted are refused. Pages marked private are "
    "returned with private: true; do not send their content to other services."
)

MAX_LINE = 4 * 1024 * 1024      # one incoming message
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 200000
MAX_LIST = 200
CACHE_TTL_MS = 60000

DENY = "Refused: the path is outside the vault or in a protected location."
HIDDEN_ALWAYS = {"journal"}
BAD_CHARS = set('<>:"|?*')


class ToolError(Exception):
    """A failure to report to the model as a tool result with isError."""


def log(msg):
    try:
        sys.stderr.write(f"vault_mcp: {msg}\n")
        sys.stderr.flush()
    except (OSError, ValueError):
        pass


# ---------------------------------------------------------------- sensitivity

_SENS = re.compile(r"^[ \t]*sensitivity[ \t]*:[ \t]*(.*)$", re.I | re.M)
ALLOWED_LEVELS = ("", "normal", "public", "private")


def sensitivity_level(text):
    """The most restrictive `sensitivity:` value in the frontmatter, lowercased.
    Tolerant on purpose: key in any case, spaces before the colon, indented or
    repeated keys. 'restricted' and any unrecognised value are refused."""
    front = lc._front(text)
    levels = [lc._scalar(m.group(1)).strip().lower() for m in _SENS.finditer(front)]
    if not levels:
        return ""
    if "restricted" in levels:
        return "restricted"
    for v in levels:
        if v not in ALLOWED_LEVELS:
            return "unrecognized"
    return "private" if "private" in levels else levels[0]


def is_refused(text):
    return sensitivity_level(text) not in ALLOWED_LEVELS


def parse_front(text):
    """Frontmatter as a dict of strings and lists of strings. Not a YAML parser:
    top-level `key: value`, flow lists and block lists, which is what vaults use."""
    front = lc._front(text)
    out = {}
    lines = front.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z0-9_][\w .-]*?)[ \t]*:[ \t]*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key, rest = m.group(1), lc._PROP.sub("", m.group(2).strip())
        if rest.startswith("["):
            joined = "\n".join([rest[1:]] + lines[i:])
            out[key] = [x for x in (lc._scalar(s) for s in lc._flow_items(joined)) if x]
        elif rest and not rest.startswith("#"):
            out[key] = lc._scalar(rest)
        else:
            items = []
            while i < len(lines):
                b = re.match(r"^[ \t]*-[ \t]+(.*)$", lines[i])
                if not b:
                    if lines[i].strip() and not lines[i].lstrip().startswith("#"):
                        break
                    i += 1
                    continue
                items.append(lc._scalar(b.group(1)))
                i += 1
            out[key] = items if items else ""
    return out


# ---------------------------------------------------------------- vault access


class Vault:
    def __init__(self, path, allow_raw=False, embed_url=None):
        self.path = os.path.abspath(path)
        self.root = os.path.realpath(path)
        self.allow_raw = allow_raw
        self.embed_url = embed_url
        self._snap = None
        self._protected = [os.path.join(self.root, d) for d in
                           (".git", ".claude", "journal") + (() if allow_raw else ("raw",))]

    # -- paths

    def _denied(self, parts):
        for p in parts:
            low = p.casefold()
            if low.startswith(".") or low in HIDDEN_ALWAYS or (low == "raw" and not self.allow_raw):
                return True
        return False

    def inside(self, real):
        try:
            return os.path.commonpath([self.root, real]) == self.root
        except ValueError:  # another drive
            return False

    def real_ok(self, path):
        """True if `path` resolves, after symlinks, to a place inside the vault
        that read_page would also allow."""
        real = os.path.realpath(path)
        if not self.inside(real):
            return False
        rel = os.path.relpath(real, self.root)
        parts = [x for x in rel.replace("\\", "/").split("/") if x]
        if not parts or self._denied(parts):
            return False
        anc = os.path.dirname(real)
        while self.inside(anc) and anc != self.root:
            for prot in self._protected:
                try:
                    if os.path.exists(prot) and os.path.samefile(anc, prot):
                        return False
                except OSError:
                    pass
            anc = os.path.dirname(anc)
        return True

    def resolve_page(self, rel):
        """(real path, vault-relative posix path) for a page the caller may read,
        or ToolError. Every refusal that is about the location uses one message."""
        if not isinstance(rel, str) or not rel.strip():
            raise ToolError("path must be a non-empty string")
        if len(rel) > 1024 or any(ord(c) < 32 for c in rel):
            raise ToolError(DENY)
        p = rel.replace("\\", "/")
        if p.startswith("/") or re.match(r"^[A-Za-z]:", p):
            raise ToolError(DENY)
        parts = [x for x in p.split("/") if x not in ("", ".")]
        if not parts or ".." in parts:
            raise ToolError(DENY)
        for part in parts:
            if BAD_CHARS & set(part) or part[-1] in ". ":
                raise ToolError(DENY)
        if self._denied(parts):
            raise ToolError(DENY)
        if not parts[-1].lower().endswith(".md"):
            raise ToolError("Only markdown pages (.md) can be read.")
        real = os.path.realpath(os.path.join(self.root, *parts))
        if not self.real_ok(real):
            raise ToolError(DENY)
        if not os.path.isfile(real):
            raise ToolError(f"No such page: {'/'.join(parts)}")
        return real, "/".join(parts)

    # -- reading

    def read_text(self, real):
        try:
            with open(real, "rb") as fh:
                data = fh.read(MAX_PAGE_BYTES + 1)
        except OSError as e:
            raise ToolError(f"Could not read the page ({e.__class__.__name__}).")
        truncated = len(data) > MAX_PAGE_BYTES
        text = data[:MAX_PAGE_BYTES].decode("utf-8-sig", errors="replace")
        # Same newline handling as link_check.collect (text mode), so line numbers match.
        return text.replace("\r\n", "\n").replace("\r", "\n"), truncated

    def collect(self, vault=None, skip=None):
        """link_check.collect, minus files that resolve outside the vault or into
        a protected folder through a symlink. Installed over lc.collect so that
        dashboard.gather gets the same protection."""
        pages = {}
        for dirpath, dirnames, filenames in os.walk(self.path):
            lc.prune(dirnames, skip)
            for name in filenames:
                if not lc.is_page(name):
                    continue
                path = os.path.join(dirpath, name)
                if not self.real_ok(path):
                    log(f"skipping {os.path.relpath(path, self.path)}: resolves outside the vault")
                    continue
                try:
                    with open(path, encoding="utf-8-sig", errors="replace") as fh:
                        pages[path] = fh.read(MAX_PAGE_BYTES)
                except OSError as e:
                    log(f"skipping {os.path.relpath(path, self.path)}: {e.__class__.__name__}")
        return pages

    def rel(self, path):
        return os.path.relpath(path, self.path).replace(os.sep, "/")

    def signature(self):
        sig = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            lc.prune(dirnames)
            for name in filenames:
                if lc.is_page(name):
                    path = os.path.join(dirpath, name)
                    try:
                        st = os.stat(path)
                    except OSError:
                        continue
                    sig.append((path, st.st_mtime_ns, st.st_size))
        sig.sort()
        return tuple(sig)

    def snapshot(self):
        """Pages, search index and link graph, rebuilt when a page's mtime or size
        changes or a page is added or removed."""
        sig = self.signature()
        if self._snap is not None and self._snap["sig"] == sig:
            return self._snap
        pages = self.collect()
        refused = {p for p, t in pages.items() if is_refused(t)}
        index = vs.Index([vs.Page(self.path, p, t) for p, t in sorted(pages.items(), key=lambda kv: self.rel(kv[0]))
                          if p not in refused])
        outbound, inbound, broken = lc.link_graph(self.path, pages)
        self._snap = {"sig": sig, "pages": pages, "refused": refused, "index": index,
                      "inbound": inbound, "by_rel": {self.rel(p): p for p in pages}}
        return self._snap


# ---------------------------------------------------------------- tools


def cap(items):
    return items[:MAX_LIST], len(items) > MAX_LIST


def scrub_dashboard(data, refused_rel):
    """The dashboard data with no title, link target or name taken from a refused
    page (dashboard.py does this for pages it recognises as restricted; this also
    covers the stricter test used here)."""
    for b in data["broken"]:
        if b["page"] in refused_rel:
            b["target"] = None
    for g in data["duplicates"]:
        if any(p in refused_rel for p in g["pages"]):
            g["name"] = "(restricted)"
    data["counts"]["restricted"] = len(refused_rel)
    return data


class Tools:
    def __init__(self, vault):
        self.v = vault
        lc.collect = vault.collect  # see Vault.collect
        self.table = {
            "search": self.search, "read_page": self.read_page, "backlinks": self.backlinks,
            "stale": self.stale, "duplicates": self.duplicates, "health": self.health,
            "lifecycle_status": self.lifecycle_status,
        }

    def dashboard(self, days=90):
        snap = self.v.snapshot()
        refused_rel = {self.v.rel(p) for p in snap["refused"]}
        data = db.gather(self.v.path, days)
        return scrub_dashboard(data, refused_rel)

    def search(self, a):
        q = a["query"].strip()
        if not q:
            raise ToolError("query must not be empty")
        limit = int(a.get("limit", 10))
        snap = self.v.snapshot()
        info = {}
        kwargs = {"index": snap["index"], "info": info, "warn": lambda m: log(f"search: {m}")}
        try:
            hits = vs.search(self.v.path, q, limit=limit,
                             embed_url=self.v.embed_url, **kwargs)
        except Exception as e:  # an embedding failure must not break plain search
            if not self.v.embed_url:
                raise
            log(f"search: embedding step failed ({e.__class__.__name__}); using BM25")
            info.clear()
            hits = vs.search(self.v.path, q, limit=limit, **kwargs)
        out = []
        for h in hits:
            h = dict(h)
            h["citation"] = f"{h['path']}:{h['line']}"
            h["private"] = h.get("sensitivity") == "private"
            out.append(h)
        return {"query": q, "mode": info.get("mode", "bm25"), "count": len(out), "hits": out}

    def read_page(self, a):
        real, rel = self.v.resolve_page(a["path"])
        text, truncated = self.v.read_text(real)
        level = sensitivity_level(text)
        if level == "restricted":
            raise ToolError(f"Refused: {rel} is marked sensitivity: restricted. "
                            "This server does not return restricted pages; ask the owner to open it directly.")
        if level not in ALLOWED_LEVELS:
            raise ToolError(f"Refused: {rel} has a sensitivity value this server does not recognise "
                            "(expected normal, private or restricted), so it is treated as restricted.")
        if len(text) > MAX_TEXT_CHARS:
            text, truncated = text[:MAX_TEXT_CHARS], True
        out = {"path": rel, "title": lc._field(text, "title") or os.path.splitext(os.path.basename(rel))[0],
               "sensitivity": level or "normal", "private": level == "private",
               "frontmatter": parse_front(text), "lines": text.count("\n") + 1,
               "truncated": truncated, "text": text}
        if level == "private":
            out["notice"] = "This page is private. Do not send its content to other services."
        return out

    def backlinks(self, a):
        real, rel = self.v.resolve_page(a["path"])
        snap = self.v.snapshot()
        target = snap["by_rel"].get(rel)
        if target is None:
            raise ToolError(f"{rel} is not in the link graph (archive, raw, journal, templates, "
                            "output, README.md and CLAUDE.md are not counted as pages).")
        if target in snap["refused"]:
            raise ToolError(f"Refused: {rel} is marked sensitivity: restricted.")
        links = []
        for src in sorted(snap["inbound"].get(target, ()), key=self.v.rel):
            if src in snap["refused"]:
                links.append({"path": self.v.rel(src), "restricted": True})
            else:
                links.append({"path": self.v.rel(src), "title": lc.title_of(src, snap["pages"][src])})
        return {"path": rel, "count": len(links), "backlinks": links}

    def stale(self, a):
        days = int(a.get("days", 90))
        d = self.dashboard(days)
        items, cut = cap(d["stale"])
        return {"as_of": d["as_of"], "days": days, "count": len(d["stale"]), "truncated": cut, "pages": items}

    def duplicates(self, a):
        d = self.dashboard()
        items, cut = cap(d["duplicates"])
        return {"as_of": d["as_of"], "count": len(d["duplicates"]), "truncated": cut, "groups": items}

    def health(self, a):
        d = self.dashboard()
        out = {"vault": d["vault"], "as_of": d["as_of"], "counts": d["counts"], "lifecycle": d["lifecycle"],
               "folders": d["folders"], "most_linked": d["most_linked"],
               "needs_owner_open": d["needs_owner_open"]}
        for key in ("broken", "orphans", "stubs"):
            out[key], out[key + "_truncated"] = cap(d[key])
        return out

    def lifecycle_status(self, a):
        snap = self.v.snapshot()
        stage_of = {s: name for name, statuses in db.FUNNEL for s in statuses}
        stages = {name: [] for name, _ in db.FUNNEL}
        promoted, other = 0, {}
        for path in sorted(snap["pages"], key=self.v.rel):
            text = snap["pages"][path]
            status = lc._field(text, "status").strip().lower()
            kind = lc._field(text, "type").strip().lower()
            if not status:
                continue
            literal = status in ("idea", "plan", "experiment")
            if kind not in db.LIFECYCLE_TYPES and not literal:
                continue
            if status in stage_of:
                entry = {"path": self.v.rel(path)}
                if path in snap["refused"]:
                    entry["restricted"] = True
                else:
                    entry.update(title=lc.title_of(path, text), status=status)
                stages[stage_of[status]].append(entry)
            elif kind in db.LIFECYCLE_TYPES:
                if status == "promoted":
                    promoted += 1
                else:
                    other[status] = other.get(status, 0) + 1
        out = {"stages": {}, "promoted": promoted, "other": dict(sorted(other.items())),
               "statuses": {name: list(sts) for name, sts in db.FUNNEL}}
        for name, _ in db.FUNNEL:
            out["stages"][name], cut = cap(stages[name])
            out["stages"][name] = {"count": len(stages[name]), "truncated": cut, "pages": out["stages"][name]}
        return out


def _s(desc, **kw):
    d = {"type": "string", "description": desc}
    d.update(kw)
    return d


def _i(desc, **kw):
    d = {"type": "integer", "description": desc}
    d.update(kw)
    return d


def _schema(props=None, required=()):
    s = {"type": "object", "additionalProperties": False}
    if props:
        s["properties"] = props
    if required:
        s["required"] = list(required)
    return s


ANNOTATIONS = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOL_DEFS = [
    ("search", "Search the vault",
     "Ranked search over the vault's pages (BM25, title above aliases above headings above body). Each hit has "
     "path, title, score, line, snippet and a citation as path:line. Restricted pages are not searched.",
     _schema({"query": _s("Words to search for.", minLength=1, maxLength=1000),
              "limit": _i("Maximum hits, default 10.", minimum=1, maximum=50)}, ["query"])),
    ("read_page", "Read a vault page",
     "Return one page: its text (with the frontmatter, so line numbers match search citations) and the parsed "
     "frontmatter. Refuses paths outside the vault, hidden folders, journal/ and raw/ and restricted pages. "
     "Private pages are returned with private: true.",
     _schema({"path": _s("Vault-relative path to a .md file, for example wiki/concepts/learning-plan.md.",
                         minLength=1, maxLength=1024)}, ["path"])),
    ("backlinks", "List pages linking to a page",
     "Pages that link to the given page with a wikilink, from the same link graph as link_check.py.",
     _schema({"path": _s("Vault-relative path to a .md page.", minLength=1, maxLength=1024)}, ["path"])),
    ("stale", "List stale pages",
     "Pages not updated for more than `days` days, oldest first (by updated:, then created:, then file date).",
     _schema({"days": _i("Age threshold in days, default 90.", minimum=0, maximum=36500)})),
    ("duplicates", "List duplicate page groups",
     "Groups of pages that share a name once punctuation is ignored, or share an alias.", _schema()),
    ("health", "Vault health summary",
     "Counts of pages, links, broken links, orphans, stubs and restricted pages, the lists behind them, pages "
     "per folder, the most linked pages and the open needs-owner items. Same data as dashboard.py --json.",
     _schema()),
    ("lifecycle_status", "Pages by lifecycle stage",
     "Idea and experiment pages grouped by funnel stage (idea, plan, experiment, adopted, dropped), with the "
     "status values that map to each stage.", _schema()),
]
TOOLS = [{"name": n, "title": t, "description": d, "inputSchema": s, "annotations": dict(ANNOTATIONS)}
         for n, t, d, s in TOOL_DEFS]
SCHEMAS = {t["name"]: t["inputSchema"] for t in TOOLS}


def validate_args(schema, args):
    """Check `args` against the small subset of JSON Schema these tools use.
    Returns an error string, or None."""
    if not isinstance(args, dict):
        return "arguments must be an object"
    props = schema.get("properties", {})
    for key in schema.get("required", ()):
        if key not in args:
            return f"missing required argument: {key}"
    for key, val in args.items():
        if key not in props:
            return f"unknown argument: {key}"
        p = props[key]
        if p["type"] == "string":
            if not isinstance(val, str):
                return f"{key} must be a string"
            if len(val) < p.get("minLength", 0):
                return f"{key} must not be empty"
            if len(val) > p.get("maxLength", 1 << 30):
                return f"{key} is too long (maximum {p['maxLength']} characters)"
        elif p["type"] == "integer":
            if isinstance(val, bool) or not (isinstance(val, int) or (isinstance(val, float) and val.is_integer())):
                return f"{key} must be an integer"
            if not p.get("minimum", -(1 << 62)) <= val <= p.get("maximum", 1 << 62):
                return f"{key} must be between {p.get('minimum')} and {p.get('maximum')}"
    return None


# ---------------------------------------------------------------- protocol


class Server:
    def __init__(self, vault):
        self.tools = Tools(vault)
        self.initialized = False  # legacy era: initialize has been answered

    # -- helpers

    @staticmethod
    def err(id_, code, message, data=None):
        e = {"code": code, "message": message}
        if data is not None:
            e["data"] = data
        return {"jsonrpc": "2.0", "id": id_, "error": e}

    @staticmethod
    def ok(id_, result):
        return {"jsonrpc": "2.0", "id": id_, "result": result}

    @staticmethod
    def server_info():
        return {"name": SERVER_NAME, "title": "Second brain vault (read-only)", "version": SERVER_VERSION}

    # -- dispatch

    def handle(self, msg):
        """One decoded message in, one response dict or None out."""
        if isinstance(msg, list):
            return self.err(None, INVALID_REQUEST, "Batch requests are not supported")
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            return self.err(None, INVALID_REQUEST, "Not a JSON-RPC 2.0 message")
        if "method" not in msg:
            return None  # a response from the client; this server sends no requests
        method = msg["method"]
        is_request = "id" in msg
        id_ = msg.get("id")
        if is_request and (isinstance(id_, bool) or not isinstance(id_, (str, int))):
            return self.err(None, INVALID_REQUEST, "id must be a string or an integer")
        if not isinstance(method, str):
            return self.err(id_ if is_request else None, INVALID_REQUEST, "method must be a string")
        params = msg.get("params")
        if params is not None and not isinstance(params, dict):
            return self.err(id_, INVALID_PARAMS, "params must be an object") if is_request else None
        params = params or {}
        if not is_request:
            if method == "notifications/initialized":
                self.initialized = True
            return None
        try:
            return self.request(id_, method, params)
        except Exception:
            log("internal error:\n" + traceback.format_exc())
            return self.err(id_, INTERNAL_ERROR, "Internal error")

    def request(self, id_, method, params):
        meta = params.get("_meta")
        modern = isinstance(meta, dict) and (META_VERSION in meta or META_CAPS in meta)
        if modern:
            bad = self.check_modern_meta(meta)
            if bad:
                return self.err(id_, *bad)
            if method == "server/discover":
                return self.ok(id_, self.modern({
                    "supportedVersions": list(MODERN_VERSIONS + LEGACY_VERSIONS),
                    "capabilities": {"tools": {}}, "instructions": INSTRUCTIONS,
                    "ttlMs": CACHE_TTL_MS, "cacheScope": "public"}))
            if method == "tools/list":
                return self.tools_list(id_, params, True)
            if method == "tools/call":
                return self.tools_call(id_, params, True)
            return self.err(id_, METHOD_NOT_FOUND, f"Method not found: {method}")

        if method == "initialize":
            return self.initialize(id_, params)
        if method == "ping":
            return self.ok(id_, {})
        if method == "server/discover":
            return self.err(id_, INVALID_PARAMS, f"Missing required _meta field: {META_VERSION}")
        if method in ("tools/list", "tools/call"):
            if not self.initialized:
                return self.err(id_, INVALID_REQUEST, "Server not initialized: send initialize first")
            return (self.tools_list if method == "tools/list" else self.tools_call)(id_, params, False)
        return self.err(id_, METHOD_NOT_FOUND, f"Method not found: {method}")

    @staticmethod
    def check_modern_meta(meta):
        ver = meta.get(META_VERSION)
        if not isinstance(ver, str) or not ver:
            return INVALID_PARAMS, f"Missing required _meta field: {META_VERSION}"
        if not isinstance(meta.get(META_CAPS), dict):
            return INVALID_PARAMS, f"Missing required _meta field: {META_CAPS}"
        if ver not in MODERN_VERSIONS:
            return UNSUPPORTED_VERSION, "Unsupported protocol version", {
                "supported": list(MODERN_VERSIONS), "requested": ver}
        return None

    @staticmethod
    def modern(result):
        result = dict(result)
        result["resultType"] = "complete"
        result["_meta"] = {META_SERVER: {"name": SERVER_NAME, "version": SERVER_VERSION}}
        return result

    def initialize(self, id_, params):
        ver = params.get("protocolVersion")
        if not isinstance(ver, str) or not ver:
            return self.err(id_, INVALID_PARAMS, "protocolVersion must be a string")
        if not isinstance(params.get("capabilities"), dict):
            return self.err(id_, INVALID_PARAMS, "capabilities must be an object")
        if not isinstance(params.get("clientInfo"), dict):
            return self.err(id_, INVALID_PARAMS, "clientInfo must be an object")
        self.initialized = True
        return self.ok(id_, {
            "protocolVersion": ver if ver in LEGACY_VERSIONS else LEGACY_VERSIONS[0],
            "capabilities": {"tools": {}},
            "serverInfo": self.server_info(),
            "instructions": INSTRUCTIONS})

    def tools_list(self, id_, params, modern):
        if "cursor" in params:
            return self.err(id_, INVALID_PARAMS, "Invalid cursor: this server returns every tool in one page")
        result = {"tools": TOOLS}
        if modern:
            result.update(ttlMs=CACHE_TTL_MS, cacheScope="public")
            result = self.modern(result)
        return self.ok(id_, result)

    def tools_call(self, id_, params, modern):
        name = params.get("name")
        if not isinstance(name, str):
            return self.err(id_, INVALID_PARAMS, "name must be a string")
        if name not in SCHEMAS:
            return self.err(id_, INVALID_PARAMS, f"Unknown tool: {name[:100]}")
        args = params.get("arguments")
        args = {} if args is None else args
        text, is_error = None, False
        problem = validate_args(SCHEMAS[name], args)
        if problem:
            text, is_error = f"Invalid arguments: {problem}", True
        else:
            try:
                text = json.dumps(self.tools.table[name](args), ensure_ascii=False, separators=(",", ":"))
            except ToolError as e:
                text, is_error = str(e), True
            except Exception:
                log(f"tool {name} failed:\n" + traceback.format_exc())
                text, is_error = "The tool failed unexpectedly; see the server's stderr.", True
        result = {"content": [{"type": "text", "text": text}], "isError": is_error}
        return self.ok(id_, self.modern(result) if modern else result)


def serve(server, inp, out):
    """Read newline-delimited JSON-RPC from `inp` (binary), write to `out` (binary)."""
    def send(resp):
        data = json.dumps(resp, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"
        out.write(data)
        out.flush()

    while True:
        line = inp.readline(MAX_LINE + 1)
        if not line:
            return
        if len(line) > MAX_LINE and not line.endswith(b"\n"):
            while True:  # drop the rest of the oversized message
                chunk = inp.readline(65536)
                if not chunk or chunk.endswith(b"\n"):
                    break
            send(Server.err(None, INVALID_REQUEST, "Message too large"))
            continue
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line.decode("utf-8-sig"))
        except (ValueError, RecursionError):
            send(Server.err(None, PARSE_ERROR, "Parse error"))
            continue
        resp = server.handle(msg)
        if resp is not None:
            send(resp)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only MCP server for a second-brain vault (stdio).")
    ap.add_argument("vault")
    ap.add_argument("--embed-url", metavar="URL",
                    help="llama.cpp embedding server for hybrid search (see vault_search.py)")
    ap.add_argument("--allow-raw", action="store_true", help="let read_page read files under raw/")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.vault):
        sys.stderr.write(f"not a directory: {args.vault}\n")
        return 1
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    # Keep stdout for protocol messages only: a private copy of the descriptor
    # carries them, and fd 1 (and sys.stdout) now point at stderr, so a stray
    # print() or a library writing to stdout cannot corrupt the stream.
    try:
        proto_fd = os.dup(1)
        os.dup2(2, 1)
        out = os.fdopen(proto_fd, "wb")
    except OSError:
        out = sys.stdout.buffer
    sys.stdout = sys.stderr
    inp = sys.stdin.buffer

    server = Server(Vault(args.vault, allow_raw=args.allow_raw, embed_url=args.embed_url))
    log(f"serving {os.path.basename(server.tools.v.path)} read-only"
        + (" (raw/ readable)" if args.allow_raw else ""))
    try:
        serve(server, inp, out)
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    except OSError as e:
        log(f"stdio closed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
