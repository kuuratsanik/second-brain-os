#!/usr/bin/env python3
"""Check the external http(s) links in resources/*.md and docs/**/*.md. Stdlib only.

Advisory: link rot is worth knowing about, but a flaky host must not block a
change, so the exit code is 0 unless --strict is given.

    python3 tools/check_external_links.py             # report; exit 0
    python3 tools/check_external_links.py --strict    # exit 1 if any URL is broken
    python3 tools/check_external_links.py --json      # machine-readable report
    python3 tools/check_external_links.py --selftest  # local server, no internet

Each distinct URL is checked once, with HEAD and a GET fallback when the host
answers 405 or 403, and once more after a timeout or a 5xx. Broken means a 4xx
other than 401, 403 and 429 (those mean "blocked", not "gone"), a DNS failure,
or a 5xx that repeated. A 401, 403 or 429 answer, or a proxy that refuses the
host, is counted as blocked, not broken. A redirect that leaves the host is listed separately;
a timeout is listed as inconclusive. URLs inside code fences or inline code
are examples and are skipped, as are example.* and localhost.
"""
import argparse
import glob
import http.server
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (compatible; second-brain-os-linkcheck/1.0; "
      "+https://github.com/kuuratsanik/second-brain-os)")
URL = re.compile(r"https?://[^\s<>\"'`\]\[{}|\\^]+")
SKIP_HOSTS = ("example.com", "example.org", "example.net", "localhost", "127.0.0.1")
OK_BLOCKED = (401, 403, 429)
WORKERS = 8
MAX_HOPS = 5


# ---- finding URLs -----------------------------------------------------------

def clean(url):
    """Trim trailing prose punctuation and an unbalanced closing parenthesis."""
    while url and url[-1] in ".,;:!?*_'\"":
        url = url[:-1]
    while url.endswith(")") and url.count(")") > url.count("("):
        url = url[:-1]
    return url


def skipped(url):
    host = (urlsplit(url).hostname or "").lower()
    return not host or any(host == h or host.endswith("." + h) for h in SKIP_HOSTS)


def urls_in(text):
    """Yield (line_number, url) outside fenced code and inline code."""
    fence = None
    for n, line in enumerate(text.split("\n"), 1):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            fence = m.group(1)[0] if fence is None else (None if m.group(1)[0] == fence else fence)
            continue
        if fence:
            continue
        for u in URL.findall(re.sub(r"`+[^`]*`+", "", line)):
            u = clean(u)
            if not skipped(u):
                yield n, u


def collect(root=ROOT):
    """{url: [(relative file, line), ...]} for every cited external URL."""
    files = sorted(glob.glob(os.path.join(root, "resources", "*.md")) +
                   glob.glob(os.path.join(root, "docs", "**", "*.md"), recursive=True))
    cites = {}
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        for n, u in urls_in(text):
            cites.setdefault(u, []).append((rel, n))
    return cites


# ---- checking one URL -------------------------------------------------------

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None  # surface the 3xx as an HTTPError so the caller can follow it


def make_opener(use_env_proxy=True):
    handlers = [NoRedirect()]
    if not use_env_proxy:
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)


def fetch_once(opener, url, method, timeout):
    """(status, location) for one request. Raises URLError/OSError on failure."""
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": UA, "Accept": "text/html,*/*;q=0.8"})
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location") if e.headers else None
        e.close()
        return e.code, loc


def is_timeout(exc):
    r = getattr(exc, "reason", exc)
    return isinstance(r, (socket.timeout, TimeoutError)) or "timed out" in str(r)


def is_dns(exc):
    return isinstance(getattr(exc, "reason", exc), socket.gaierror)


def probe(opener, url, timeout):
    """Follow one URL to its end. Returns (state, detail, final_url).
    state: ok, broken, blocked or timeout."""
    cur, hops = url, 0
    while True:
        status = None
        for attempt in (1, 2):
            try:
                status, loc = fetch_once(opener, cur, "HEAD", timeout)
                if status in (405, 403, 501):
                    status, loc = fetch_once(opener, cur, "GET", timeout)
            except (urllib.error.URLError, OSError) as e:
                if "Tunnel connection failed" in str(e):  # an outbound proxy refused the host
                    return "blocked", "refused by proxy", cur
                if is_dns(e):
                    return "broken", "DNS failure", cur
                if attempt == 2:
                    if is_timeout(e):
                        return "timeout", "timed out twice", cur
                    return "broken", f"connection failed: {getattr(e, 'reason', e)}", cur
                continue
            if status >= 500 and attempt == 1:
                continue
            break
        if 300 <= status < 400 and loc:
            hops += 1
            if hops > MAX_HOPS:
                return "broken", "too many redirects", cur
            cur = urljoin(cur, loc)
            continue
        if status in OK_BLOCKED:
            return "blocked", f"HTTP {status}", cur
        if status >= 400:
            return "broken", f"HTTP {status}", cur
        return "ok", f"HTTP {status}", cur


def host_of(u):
    h = (urlsplit(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def check_all(cites, timeout=15, opener=None, workers=WORKERS):
    opener = opener or make_opener()
    urls = sorted(cites)
    with ThreadPoolExecutor(max_workers=min(workers, WORKERS)) as ex:
        results = list(ex.map(lambda u: probe(opener, u, timeout), urls))
    report = {"checked": len(urls), "broken": [], "moved_host": [], "inconclusive": [],
              "blocked": sum(1 for r in results if r[0] == "blocked")}
    for u, (state, detail, final) in zip(urls, results):
        where = [f"{f}:{n}" for f, n in cites[u]]
        if state == "broken":
            report["broken"].append({"url": u, "detail": detail, "cited": where})
        elif state == "timeout":
            report["inconclusive"].append({"url": u, "detail": detail, "cited": where})
        elif host_of(final) != host_of(u):
            report["moved_host"].append({"url": u, "final": final, "cited": where})
    return report


def render(rep):
    out = [f"{rep['checked']} distinct external URLs checked: {len(rep['broken'])} broken, "
           f"{len(rep['moved_host'])} redirect to another host, "
           f"{len(rep['inconclusive'])} inconclusive, {rep['blocked']} blocked (401, 403, 429 or a proxy)"]
    for title, key, fmt in (
            ("Broken", "broken", lambda r: f"{r['url']}  ({r['detail']})"),
            ("Redirect to a different host", "moved_host", lambda r: f"{r['url']}  ->  {r['final']}"),
            ("Inconclusive (timeout)", "inconclusive", lambda r: f"{r['url']}  ({r['detail']})")):
        if rep[key]:
            out += ["", f"{title}:"]
            for r in rep[key]:
                out.append(f"  {fmt(r)}")
                out += [f"      {c}" for c in r["cited"]]
    return "\n".join(out)


# ---- selftest ---------------------------------------------------------------

def selftest():
    hits = {}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _do(self, head):
            path = self.path
            hits[path] = hits.get(path, 0) + 1
            code, hdr = 200, {}
            if path == "/missing":
                code = 404
            elif path == "/redir":
                code, hdr = 302, {"Location": "http://localhost:%d/ok" % self.server.server_port}
            elif path == "/samehost":
                code, hdr = 301, {"Location": "/ok"}
            elif path == "/slow":
                time.sleep(2.5)
            elif path == "/nohead" and head:
                code = 405
            elif path == "/blocked":
                code = 403
            elif path == "/flaky" and hits[path] == 1:
                code = 503
            elif path == "/down":
                code = 500
            self.send_response(code)
            for k, v in hdr.items():
                self.send_header(k, v)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_HEAD(self):
            self._do(True)

        def do_GET(self):
            self._do(False)

    class S(http.server.ThreadingHTTPServer):
        daemon_threads = True

    srv = S(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    opener = make_opener(use_env_proxy=False)
    failures = []

    def expect(name, cond):
        if not cond:
            failures.append(name)

    def run(path, timeout=1):
        return probe(opener, base + path, timeout)

    expect("200", run("/ok")[0] == "ok")
    expect("404", run("/missing")[:2] == ("broken", "HTTP 404"))
    expect("redirect to other host", run("/redir")[0] == "ok" and host_of(run("/redir")[2]) == "localhost")
    expect("redirect on same host", host_of(run("/samehost")[2]) == "127.0.0.1")
    expect("timeout", run("/slow")[0] == "timeout")
    expect("HEAD 405 falls back to GET", run("/nohead")[0] == "ok")
    expect("403 is blocked, not broken", run("/blocked")[0] == "blocked")
    expect("5xx retried once", run("/flaky")[0] == "ok" and hits["/flaky"] == 2)
    expect("repeated 5xx broken", run("/down")[0] == "broken" and hits["/down"] >= 2)

    real = fetch_once

    def dns(*a):
        raise urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
    globals()["fetch_once"] = dns
    try:
        expect("DNS failure broken", probe(opener, "http://nope.invalid/", 1)[:2] == ("broken", "DNS failure"))
    finally:
        globals()["fetch_once"] = real

    cites = {base + p: [("docs/x.md", i)] for i, p in enumerate(["/ok", "/missing", "/redir", "/slow"], 1)}
    rep = check_all(cites, timeout=1, opener=opener)
    expect("report counts", (rep["checked"], len(rep["broken"]), len(rep["moved_host"]),
                             len(rep["inconclusive"])) == (4, 1, 1, 1))
    expect("report cites file:line", rep["broken"][0]["cited"] == ["docs/x.md:2"])

    text = ("See [a](https://a.test/x_(y)). Also https://b.test/p, and `https://c.test/code`.\n"
            "```\nhttps://d.test/fenced\n```\nhttp://localhost:3000/x https://example.com/y\n"
            "<https://e.test/z>.\n")
    found = list(urls_in(text))
    expect("url extraction", found == [(1, "https://a.test/x_(y)"), (1, "https://b.test/p"),
                                       (6, "https://e.test/z")])
    srv.shutdown()
    if failures:
        print("selftest FAILED: " + ", ".join(failures))
        return 1
    print("selftest: ok")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if any URL is broken")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true", help="test the checker on a local server")
    ap.add_argument("--timeout", type=float, default=15, help="seconds per request (default 15)")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    rep = check_all(collect(), timeout=args.timeout)
    print(json.dumps(rep, indent=2) if args.json else render(rep))
    sys.exit(1 if args.strict and rep["broken"] else 0)


if __name__ == "__main__":
    main()
