#!/usr/bin/env python3
"""Time a long prompt prefix on a running llama-server: cold, warm, and restored from disk.

Usage:
    python3 tools/bench_kv_slots.py [--url http://127.0.0.1:8080] [-n 5]
                                    [--slot 0] [--filename kv-bench.bin]
                                    [--words 3000 | --prompt-file FILE]
                                    [--n-predict 8] [--no-nonce] [--api-key KEY] [--json]
    python3 tools/bench_kv_slots.py --selftest

The server must run with `--slot-save-path DIR` (slot save and restore are
disabled without it); the slots endpoint is on by default per the README, so
do not pass `--no-slots`. The prefix must fit the server's context (`-c`),
with room for `--n-predict` tokens; the default 3000 words is several
thousand tokens. Per repetition it measures the
time to the first streamed token (TTFT), and reads `timings.cache_n` (prompt
tokens reused from the cache) and `timings.prompt_n` (prompt tokens processed)
from the last streamed event, for three states:

  cold      the slot is erased and the prompt starts with a one-off nonce line,
            so neither the slot nor a server-side RAM prompt cache can match;
  warm      the same prefix is already in the slot, from a priming request;
  restored  the slot is erased with POST /slots/{id}?action=erase, then loaded
            with ?action=restore from the file saved at the start; the restore
            time is reported on its own and is not in the TTFT.

It prints a markdown table with the median and p90 of each column. With a small
`-n` the p90 is close to the maximum; use `-n 10` or more for a figure you
would quote. The saved file stays in `--slot-save-path` afterwards.

Endpoints and field names (`/completion` with `stream`, `id_slot`,
`cache_prompt`, `n_predict`; `/slots/{id_slot}?action=save|restore|erase` with
`filename`; `timings.cache_n`, `timings.prompt_n`, `timings.prompt_ms`) are from
tools/server/README.md in ggml-org/llama.cpp on master, fetched 6 October 2026:
https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
The README documents `timings` in its OpenAI-compatible section and
`tokens_cached` / `tokens_evaluated` for `/completion`; this tool reads
`timings` from the final `/completion` event and falls back to `tokens_cached`
(cache_n only) when `timings` is absent. Check the README of the version you
run. Standard library only.
"""
import argparse
import json
import random
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request

STATES = ("cold", "warm", "restored")


class BenchError(Exception):
    pass


def percentile(values, pct):
    """Linear-interpolation percentile (the same method as numpy's default)."""
    xs = sorted(values)
    if not xs:
        return None
    k = (len(xs) - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def make_prefix(words):
    """A deterministic filler prefix of about `words` words (a few tokens per word)."""
    rng = random.Random(1234)
    vocab = ["vault", "note", "link", "source", "index", "tag", "page", "raw", "wiki", "claim",
             "review", "lint", "alias", "orphan", "journal", "output", "project", "decision"]
    out = []
    for i in range(words):
        out.append(rng.choice(vocab) if i % 12 else f"Section {i // 12}.")
    return "You are the maintenance agent for a markdown vault. Reference text follows.\n" + " ".join(out) + "\n"


class Client:
    def __init__(self, base, api_key=None, timeout=600.0):
        self.base = base.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = "Bearer " + api_key
        self.timeout = timeout

    def _open(self, path, body):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode("utf-8"),
                                     headers=self.headers, method="POST")
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise BenchError(f"POST {path} -> HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, OSError) as e:
            raise BenchError(f"POST {path} failed: {getattr(e, 'reason', e)}") from e

    def slot_action(self, slot, action, filename=None):
        body = {"filename": filename} if filename else {}
        t0 = time.perf_counter()
        with self._open(f"/slots/{slot}?action={action}", body) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
        data["_wall_ms"] = (time.perf_counter() - t0) * 1000.0
        return data

    def complete(self, prompt, slot, n_predict):
        """Stream one completion. Returns (ttft_ms, cache_n, prompt_n, prompt_ms)."""
        body = {"prompt": prompt, "n_predict": n_predict, "stream": True, "cache_prompt": True,
                "id_slot": slot, "temperature": 0}
        t0 = time.perf_counter()
        first = None
        last = {}
        with self._open("/completion", body) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    ev = json.loads(payload)
                except ValueError:
                    continue
                now = time.perf_counter()
                if first is None or (first[1] is False and ev.get("content")):
                    first = (now, bool(ev.get("content")))
                last = ev
        if first is None:
            raise BenchError("no streamed events from /completion")
        timings = last.get("timings") or {}
        cache_n = timings.get("cache_n", last.get("tokens_cached"))
        return ((first[0] - t0) * 1000.0, cache_n, timings.get("prompt_n"), timings.get("prompt_ms"))


def run(client, prefix, n, slot, filename, n_predict, nonce=True, log=None):
    """Return {state: {"ttft": [...], "cache_n": [...], "prompt_n": [...], "prompt_ms": [...], "restore_ms": [...]}}."""
    def say(msg):
        if log:
            log(msg)

    rows = {s: {"ttft": [], "cache_n": [], "prompt_n": [], "prompt_ms": [], "restore_ms": []} for s in STATES}

    def record(state, result):
        ttft, cache_n, prompt_n, prompt_ms = result
        r = rows[state]
        r["ttft"].append(ttft)
        for key, val in (("cache_n", cache_n), ("prompt_n", prompt_n), ("prompt_ms", prompt_ms)):
            if val is not None:
                r[key].append(float(val))

    say("setup: erase, process the prefix, save the slot")
    client.slot_action(slot, "erase")
    client.complete(prefix, slot, 1)
    saved = client.slot_action(slot, "save", filename)
    say(f"saved {saved.get('n_saved')} tokens, {saved.get('n_written')} bytes")

    for i in range(1, n + 1):
        say(f"repetition {i}/{n}")
        # cold: empty slot, and a nonce first line so no cached prefix can match
        client.slot_action(slot, "erase")
        cold_prompt = (f"[bench run {random.getrandbits(48):x}]\n" + prefix) if nonce else prefix
        record("cold", client.complete(cold_prompt, slot, n_predict))
        # warm: prime the slot with the prefix, then measure the same prefix again
        client.slot_action(slot, "erase")
        client.complete(prefix, slot, 1)
        record("warm", client.complete(prefix, slot, n_predict))
        # restored: erase, restore from disk, then measure
        client.slot_action(slot, "erase")
        restored = client.slot_action(slot, "restore", filename)
        ms = (restored.get("timings") or {}).get("restore_ms", restored["_wall_ms"])
        rows["restored"]["restore_ms"].append(float(ms))
        record("restored", client.complete(prefix, slot, n_predict))
    return rows


def _fmt(values, pct=None, digits=0):
    if not values:
        return "n/a"
    v = statistics.median(values) if pct is None else percentile(values, pct)
    return f"{v:,.{digits}f}"


def table(rows, n):
    head = ("| State | TTFT median (ms) | TTFT p90 (ms) | cache_n median | prompt_n median "
            "| prompt_ms median | restore_ms median |")
    lines = [head, "|---|---:|---:|---:|---:|---:|---:|"]
    for s in STATES:
        r = rows[s]
        lines.append(f"| {s} | {_fmt(r['ttft'])} | {_fmt(r['ttft'], 90)} | {_fmt(r['cache_n'])} "
                     f"| {_fmt(r['prompt_n'])} | {_fmt(r['prompt_ms'], None, 1)} "
                     f"| {_fmt(r['restore_ms'], None, 1) if s == 'restored' else '-'} |")
    lines.append("")
    lines.append(f"n = {n} repetitions per state. TTFT is time to the first streamed token with `n_predict` small; "
                 "restore time is reported separately and not included in the restored TTFT.")
    return "\n".join(lines)


# ---- selftest -------------------------------------------------------------

def _fake_server():
    """A fake llama-server: one slot, word-level prefix cache, save, restore, erase."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    state = {"cached": [], "files": {}, "save_path": True}
    lock = threading.Lock()

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *a):
            pass

        def _json(self, code, obj):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            url = urlparse(self.path)
            with lock:
                if url.path.startswith("/slots/"):
                    action = parse_qs(url.query).get("action", [""])[0]
                    if action == "erase":
                        n = len(state["cached"])
                        state["cached"] = []
                        return self._json(200, {"id_slot": 0, "n_erased": n})
                    if action == "save":
                        state["files"][body["filename"]] = list(state["cached"])
                        return self._json(200, {"id_slot": 0, "filename": body["filename"],
                                                "n_saved": len(state["cached"]), "n_written": 4 * len(state["cached"]),
                                                "timings": {"save_ms": 1.5}})
                    if action == "restore":
                        if body.get("filename") not in state["files"]:
                            return self._json(400, {"error": {"message": "file not found"}})
                        state["cached"] = list(state["files"][body["filename"]])
                        return self._json(200, {"id_slot": 0, "filename": body["filename"],
                                                "n_restored": len(state["cached"]),
                                                "timings": {"restore_ms": 2.5}})
                    return self._json(404, {"error": "unknown action"})
                if url.path == "/completion":
                    toks = body["prompt"].split()
                    common = 0
                    for a, b in zip(state["cached"], toks):
                        if a != b:
                            break
                        common += 1
                    common = min(common, len(toks) - 1)
                    prompt_n = len(toks) - common
                    state["cached"] = toks
                else:
                    return self._json(404, {"error": "not found"})
            time.sleep(0.0004 * prompt_n)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b'data: {"content":"ok","stop":false}\n\n')
            self.wfile.flush()
            final = {"content": "", "stop": True, "tokens_cached": common,
                     "timings": {"cache_n": common, "prompt_n": prompt_n, "prompt_ms": 0.4 * prompt_n}}
            self.wfile.write(b"data: " + json.dumps(final).encode() + b"\n\n")

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def selftest():
    failures = []

    def check(label, ok, detail=""):
        if not ok:
            failures.append(f"{label} {detail}".strip())

    check("percentile p50", percentile([1, 2, 3, 4, 5], 50) == 3)
    check("percentile p90", abs(percentile([1, 2, 3, 4, 5], 90) - 4.6) < 1e-9)
    check("percentile one value", percentile([7], 90) == 7)
    check("percentile empty", percentile([], 90) is None)
    check("prefix is deterministic", make_prefix(50) == make_prefix(50))

    srv = _fake_server()
    try:
        client = Client(f"http://127.0.0.1:{srv.server_address[1]}", timeout=30)
        prefix = make_prefix(300)
        total = len((prefix).split())
        rows = run(client, prefix, 3, 0, "kv-bench.bin", 4)
        cold, warm, rest = rows["cold"], rows["warm"], rows["restored"]
        check("three TTFTs per state", all(len(rows[s]["ttft"]) == 3 for s in STATES))
        check("cold cache_n is 0", max(cold["cache_n"]) == 0, str(cold["cache_n"]))
        check("warm reuses the prefix", min(warm["cache_n"]) >= total - 1, str(warm["cache_n"]))
        check("restored reuses the prefix", min(rest["cache_n"]) >= total - 1, str(rest["cache_n"]))
        check("cold processes the prompt", min(cold["prompt_n"]) >= total, str(cold["prompt_n"]))
        check("warm processes one token", max(warm["prompt_n"]) == 1, str(warm["prompt_n"]))
        check("cold TTFT above warm", statistics.median(cold["ttft"]) > statistics.median(warm["ttft"]) + 20,
              f"{cold['ttft']} vs {warm['ttft']}")
        check("restore_ms recorded", rest["restore_ms"] == [2.5, 2.5, 2.5], str(rest["restore_ms"]))
        out = table(rows, 3)
        check("table has a row per state", all(f"| {s} |" in out for s in STATES), out)
        check("table header", out.startswith("| State | TTFT median (ms) | TTFT p90 (ms) |"))
        try:
            client.slot_action(0, "restore", "missing.bin")
            check("restore of a missing file raises", False)
        except BenchError as e:
            check("restore error names the status", "HTTP 400" in str(e), str(e))
    finally:
        srv.shutdown()
        srv.server_close()

    dead = Client("http://127.0.0.1:9", timeout=2)
    try:
        dead.complete("x", 0, 1)
        check("connection failure raises", False)
    except BenchError:
        pass

    for f in failures:
        print("FAIL", f)
    print("selftest:", "FAILED" if failures else "ok")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default="http://127.0.0.1:8080", help="llama-server base URL")
    ap.add_argument("-n", "--repeat", type=int, default=5, help="repetitions per state (default 5)")
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--filename", default="kv-bench.bin", help="file name inside --slot-save-path")
    ap.add_argument("--words", type=int, default=3000, help="size of the generated prefix, in words")
    ap.add_argument("--prompt-file", help="use this file's text as the prefix instead of generated text")
    ap.add_argument("--n-predict", type=int, default=8)
    ap.add_argument("--no-nonce", action="store_true", help="do not add a nonce line to the cold prompt")
    ap.add_argument("--api-key")
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--json", action="store_true", help="print the raw per-run numbers as JSON")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.repeat < 1:
        ap.error("-n must be at least 1")
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as fh:
            prefix = fh.read()
    else:
        prefix = make_prefix(args.words)
    client = Client(args.url, args.api_key, args.timeout)
    try:
        rows = run(client, prefix, args.repeat, args.slot, args.filename, args.n_predict,
                   nonce=not args.no_nonce, log=lambda m: print(m, file=sys.stderr))
    except BenchError as e:
        print(f"bench_kv_slots: {e}", file=sys.stderr)
        if "slots/" in str(e) and "HTTP" in str(e):
            print("Slot save and restore need llama-server started with --slot-save-path DIR "
                  "and slots not disabled.", file=sys.stderr)
        return 2
    print(json.dumps(rows, indent=2) if args.json else table(rows, args.repeat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
