#!/usr/bin/env python3
"""Check the external http(s) links in resources/*.md and docs/**/*.md. Stdlib only.

Advisory: link rot is worth knowing about, but a flaky host must not block a
change, so the exit code is 0 unless --strict is given.

    python3 tools/check_external_links.py             # report; exit 0
    python3 tools/check_external_links.py --strict    # exit 1 if any URL is broken
    python3 tools/check_external_links.py --json      # machine-readable report
    python3 tools/check_external_links.py --markdown  # report for a job summary
    python3 tools/check_external_links.py --selftest  # local server, no internet

Each distinct URL is checked once, with HEAD and a GET fallback when the host
answers 405, 403 or 501, and once more after a timeout, a 5xx or a DNS failure.
Non-ASCII paths and hosts are percent- and IDNA-encoded first (the stdlib codec
is IDNA2003, so a host with an eszett is sent with "ss"). The report lists:

  broken        a 4xx other than 401, 403 and 429, a DNS failure that repeated,
                a 5xx that repeated, a refused connection, a 3xx with no Location
  redirected    the final URL is on a different host
  downgraded    an https URL that ends on plain http
  blocked       401, 403 or 429, or an outbound proxy refusing the host: the
                link may be fine, so check these by hand
  inconclusive  timeouts, protocol errors, and anything not reached within the
                overall --budget

Only "broken" counts for --strict. URLs inside code fences or inline code are
examples and are skipped, as are example.* and localhost. Fences are recognised
at up to three spaces of indent, as in CommonMark; a fence nested inside a list
item, and indented (4-space or tab) code blocks, are not, so URLs there are
checked like prose.
"""
import argparse
import glob
import http.client
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeout
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (compatible; second-brain-os-linkcheck/1.0; "
      "+https://github.com/kuuratsanik/second-brain-os)")
URL = re.compile(r"https?://[^\s<>\"'`\]\[{}|\\^]+")
SKIP_HOSTS = ("example.com", "example.org", "example.net", "localhost", "127.0.0.1")
OK_BLOCKED = (401, 403, 429)
WORKERS = 8
MAX_HOPS = 5
BUDGET = 600  # seconds for the whole run


# ---- finding URLs -----------------------------------------------------------

def clean(url, before=""):
    """Trim trailing prose punctuation and an unbalanced closing parenthesis.
    A trailing `_` or `*` is dropped only when the same character sits right
    before the URL, which makes it Markdown emphasis rather than part of the URL."""
    depth = 0
    for i, c in enumerate(url):  # cut at the first unbalanced ")": the end of a [text](url)
        depth += (c == "(") - (c == ")")
        if depth < 0:
            url = url[:i]
            break
    while url:
        c = url[-1]
        if c in ".,;:!?'\"" or (c in "_*" and before.endswith(c)):
            url = url[:-1]
        elif c == ")" and url.count(")") > url.count("("):
            url = url[:-1]
        else:
            break
    return url


def skipped(url):
    host = (urlsplit(url).hostname or "").lower()
    return not host or any(host == h or host.endswith("." + h) for h in SKIP_HOSTS)


FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def code_flags(lines):
    """Yield (line, in_code) following CommonMark: a fence opens with a run of at
    least three backticks or tildes and closes only on the same character, at
    least as many, with nothing after it. A longer fence can hold shorter ones."""
    fence = None  # (char, length)
    for line in lines:
        m = FENCE.match(line)
        if fence is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)))
                yield line, True
                continue
            yield line, False
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] \
                    and not m.group(2).strip():
                fence = None
            yield line, True


def urls_in(text):
    """Yield (line_number, url) outside fenced code and inline code."""
    for n, (line, code) in enumerate(code_flags(text.split("\n")), 1):
        if code:
            continue
        line = re.sub(r"`+[^`]*`+", lambda m: " " * len(m.group(0)), line)
        for m in URL.finditer(line):
            u = clean(m.group(0), line[max(0, m.start() - 1):m.start()])
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

def encode_url(url):
    """ASCII-only form of a URL: IDNA host, percent-encoded path and query.
    Existing %XX escapes are kept; the fragment is dropped (never sent)."""
    sp = urlsplit(url)
    userinfo, at, hostport = sp.netloc.rpartition("@")
    if not hostport.startswith("["):
        host, colon, port = hostport.partition(":")
        try:
            host.encode("ascii")
        except UnicodeEncodeError:
            try:
                host = host.encode("idna").decode("ascii")
            except UnicodeError:
                pass
        hostport = host + colon + port
    safe = "/%:@!$&'()*+,;=-._~"
    return urlunsplit((sp.scheme, userinfo + at + hostport, quote(sp.path, safe=safe),
                       quote(sp.query, safe=safe + "?"), ""))


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
        if loc:
            try:  # http.client reads headers as latin-1; hosts send raw UTF-8
                loc = loc.encode("latin-1").decode("utf-8")
            except UnicodeError:
                pass
        e.close()
        return e.code, loc


def is_timeout(exc):
    r = getattr(exc, "reason", exc)
    return isinstance(r, (socket.timeout, TimeoutError)) or "timed out" in str(r)


def is_dns(exc):
    return isinstance(getattr(exc, "reason", exc), socket.gaierror)


def probe(opener, url, timeout):
    """Follow one URL to its end. Returns (state, detail, final_url); state is
    ok, broken, blocked, timeout or error. Never raises."""
    try:
        return _probe(opener, url, timeout)
    except (http.client.InvalidURL, ValueError) as e:
        return "broken", f"invalid URL: {e}", url
    except Exception as e:  # one odd host must not abort the whole report
        return "error", f"{type(e).__name__}: {e}", url


def _probe(opener, url, timeout):
    cur, hops = url, 0
    while True:
        status = loc = None
        for attempt in (1, 2):
            try:
                target = encode_url(cur)
                status, loc = fetch_once(opener, target, "HEAD", timeout)
                if status in (405, 403, 501):
                    status, loc = fetch_once(opener, target, "GET", timeout)
            except http.client.InvalidURL:
                raise
            except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
                if "Tunnel connection failed" in str(e):  # an outbound proxy refused the host
                    return "blocked", "refused by proxy", cur
                if attempt == 1:
                    continue
                if is_dns(e):
                    return "broken", "DNS failure", cur
                if is_timeout(e):
                    return "timeout", "timed out twice", cur
                if isinstance(e, http.client.HTTPException):
                    return "error", f"protocol error: {type(e).__name__}", cur
                return "broken", f"connection failed: {getattr(e, 'reason', e)}", cur
            if status >= 500 and attempt == 1:
                continue
            break
        if 300 <= status < 400:
            if not loc:
                return "broken", f"HTTP {status} without Location", cur
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


def check_all(cites, timeout=15, opener=None, workers=WORKERS, budget=BUDGET):
    """Check every URL; whatever is not finished within `budget` seconds in
    total is reported as inconclusive."""
    opener = opener or make_opener()
    urls = sorted(cites)
    results = {}
    ex = ThreadPoolExecutor(max_workers=min(workers, WORKERS))
    futs = {ex.submit(probe, opener, u, timeout): u for u in urls}
    try:
        for f in as_completed(futs, timeout=budget):
            results[futs[f]] = f.result()
    except FuturesTimeout:
        pass
    ex.shutdown(wait=False, cancel_futures=True)
    report = {"checked": len(urls), "broken": [], "moved_host": [], "downgraded": [],
              "blocked": [], "inconclusive": []}
    for u in urls:
        state, detail, final = results.get(
            u, ("timeout", "not reached within the time budget", u))
        item = {"url": u, "cited": [f"{f}:{n}" for f, n in cites[u]]}
        if state == "broken":
            report["broken"].append(dict(item, detail=detail))
        elif state == "blocked":
            report["blocked"].append(dict(item, detail=detail))
        elif state in ("timeout", "error"):
            report["inconclusive"].append(dict(item, detail=detail))
        else:
            if host_of(final) != host_of(u):
                report["moved_host"].append(dict(item, final=final))
            if u.startswith("https:") and final.startswith("http:"):
                report["downgraded"].append(dict(item, final=final))
    return report


SECTIONS = (
    ("Broken", "broken", lambda r: f"{r['url']}  ({r['detail']})"),
    ("Redirect to a different host", "moved_host", lambda r: f"{r['url']}  ->  {r['final']}"),
    ("Downgraded from https to http", "downgraded", lambda r: f"{r['url']}  ->  {r['final']}"),
    ("Inconclusive", "inconclusive", lambda r: f"{r['url']}  ({r['detail']})"),
    ("Blocked (check by hand)", "blocked", lambda r: f"{r['url']}  ({r['detail']})"),
)


def summary_line(rep):
    return (f"{rep['checked']} distinct external URLs checked: {len(rep['broken'])} broken, "
            f"{len(rep['moved_host'])} redirect to another host, "
            f"{len(rep['downgraded'])} downgraded to http, "
            f"{len(rep['inconclusive'])} inconclusive, {len(rep['blocked'])} blocked")


def md_text(t):
    """Make server-supplied text safe inside a markdown code span."""
    return t.replace("`", "%60").replace("<", "&lt;")


def render(rep, markdown=False):
    out = [summary_line(rep)]
    for title, key, fmt in SECTIONS:
        rows = rep[key]
        if not rows:
            continue
        if markdown:
            fold = len(rows) > 10
            out += ["", f"### {title} ({len(rows)})", ""]
            if fold:
                out += ["<details><summary>show</summary>", ""]
            for r in rows:
                out.append(f"- `{md_text(fmt(r))}`")
                out += [f"  - {c}" for c in r["cited"]]
            if fold:
                out += ["", "</details>"]
        else:
            out += ["", f"{title}:"]
            for r in rows:
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
            if path == "/rawloc":  # a raw UTF-8 Location header
                self.wfile.write(b"HTTP/1.1 302 Found\r\nLocation: /\xc3\xbcber\r\n"
                                 b"Content-Length: 0\r\n\r\n")
                return
            if path.startswith("/%C3%BCber") or path.startswith("/\xfcber"):
                code = 200 if path == "/%C3%BCber" else 400
            elif path == "/badstatus":
                self.wfile.write(b"garbage\r\n\r\n")
                return
            elif path == "/missing":
                code = 404
            elif path == "/redir":
                code, hdr = 302, {"Location": "http://localhost:%d/ok" % self.server.server_port}
            elif path == "/samehost":
                code, hdr = 301, {"Location": "/ok"}
            elif path == "/noloc":
                code = 302
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
            elif path.startswith("/%C3%9Cbung") and path != "/%C3%9Cbung/%C3%A9?q=%C3%BC":
                code = 400  # the checker sent something other than the encoded form
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
    expect("3xx without Location", run("/noloc")[:2] == ("broken", "HTTP 302 without Location"))
    expect("timeout", run("/slow")[0] == "timeout")
    expect("HEAD 405 falls back to GET", run("/nohead")[0] == "ok")
    expect("403 is blocked, not broken", run("/blocked")[0] == "blocked")
    expect("5xx retried once", run("/flaky")[0] == "ok" and hits["/flaky"] == 2)
    expect("repeated 5xx broken", run("/down")[0] == "broken" and hits["/down"] >= 2)
    expect("bad status line is inconclusive", run("/badstatus")[0] == "error")
    st, _, fin = run("/rawloc")
    expect("raw UTF-8 Location is decoded", st == "ok" and fin == base + "/\u00fcber")
    expect("non-ASCII path is encoded", run("/Übung/é?q=ü")[0] == "ok")
    expect("encode_url wikipedia",
           encode_url("https://de.wikipedia.org/wiki/Übung") == "https://de.wikipedia.org/wiki/%C3%9Cbung")
    expect("encode_url idna host", encode_url("https://bücher.example/straße#x")
           == "https://xn--bcher-kva.example/stra%C3%9Fe")
    expect("encode_url keeps escapes", encode_url("https://a.test/a%20b?x=1&y=%2F") == "https://a.test/a%20b?x=1&y=%2F")

    real = fetch_once
    calls = []

    def patch(fn):
        globals()["fetch_once"] = fn

    try:
        def dns(*a):
            calls.append(1)
            raise urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
        patch(dns)
        expect("DNS failure broken after one retry",
               probe(opener, "http://nope.invalid/", 1)[:2] == ("broken", "DNS failure") and len(calls) == 2)

        def boom(*a):
            raise RuntimeError("unexpected")
        patch(boom)
        expect("unexpected exception is contained", probe(opener, "http://x.test/", 1)[0] == "error")

        def bad(*a):
            raise ValueError("nope")
        patch(bad)
        expect("ValueError is broken", probe(opener, "http://x.test/", 1)[0] == "broken")
    finally:
        patch(real)

    cites = {base + p: [("docs/x.md", i)] for i, p in enumerate(
        ["/ok", "/missing", "/redir", "/slow", "/blocked"], 1)}
    rep = check_all(cites, timeout=1, opener=opener)
    expect("report counts", (rep["checked"], len(rep["broken"]), len(rep["moved_host"]),
                             len(rep["inconclusive"]), len(rep["blocked"])) == (5, 1, 1, 1, 1))
    expect("report cites file:line", rep["broken"][0]["cited"] == ["docs/x.md:2"])
    expect("blocked is listed", rep["blocked"][0]["url"].endswith("/blocked"))
    evil = {"checked": 1, "broken": [], "downgraded": [], "blocked": [], "inconclusive": [],
            "moved_host": [{"url": "https://a.test/", "final": "https://b.test/`x<img>",
                            "cited": ["a.md:1"]}]}
    md = render(evil, markdown=True)
    expect("markdown escapes backtick and <", "`x" not in md and "<img" not in md
           and "%60x&lt;img>" in md)
    expect("markdown report", "### Blocked (check by hand) (1)" in render(rep, markdown=True))
    t0 = time.time()
    short = check_all({base + "/slow": [("a.md", 1)], base + "/ok": [("a.md", 2)]},
                      timeout=5, opener=opener, budget=0.5)
    expect("budget leaves the rest inconclusive",
           [r["url"][-5:] for r in short["inconclusive"]] == ["/slow"] and time.time() - t0 < 2)
    def downgrade(opener_, url, method, timeout):
        return (301, "http://a.test/p") if url.startswith("https:") else (200, None)
    globals()["fetch_once"] = downgrade
    try:
        dg = check_all({"https://a.test/p": [("a.md", 1)]}, opener=opener)
    finally:
        globals()["fetch_once"] = real
    expect("https to http downgrade is reported", len(dg["downgraded"]) == 1 and not dg["broken"])
    srv.shutdown()

    text = ("See [a](https://a.test/x_(y)). Also https://b.test/p, and `https://c.test/code`.\n"
            "```\nhttps://d.test/fenced\n```\nhttp://localhost:3000/x https://example.com/y\n"
            "<https://e.test/z>. *https://f.test/em* _https://g.test/u_ https://h.test/a_b_\n"
            "````\n```dataview\nhttps://i.test/nested\n```\nhttps://j.test/still-code\n````\n"
            "https://k.test/after\n~~~\nhttps://l.test/tilde\n````\nhttps://m.test/in-tilde\n~~~\n"
            "https://n.test/end\n")
    found = [u for _, u in urls_in(text)]
    expect("link followed by emphasis", [u for _, u in urls_in("**[x](https://o.test/p)** and (https://q.test/r)")]
           == ["https://o.test/p", "https://q.test/r"])
    expect("url extraction", found == [
        "https://a.test/x_(y)", "https://b.test/p", "https://e.test/z", "https://f.test/em",
        "https://g.test/u", "https://h.test/a_b_", "https://k.test/after", "https://n.test/end"])
    if failures:
        print("selftest FAILED: " + ", ".join(failures))
        return 1
    print("selftest: ok")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if any URL is broken")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--markdown", action="store_true", help="markdown report for a job summary")
    ap.add_argument("--selftest", action="store_true", help="test the checker on a local server")
    ap.add_argument("--timeout", type=float, default=15, help="seconds per request (default 15)")
    ap.add_argument("--budget", type=float, default=BUDGET,
                    help="seconds for the whole run (default %d)" % BUDGET)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    rep = check_all(collect(), timeout=args.timeout, budget=args.budget)
    print(json.dumps(rep, indent=2) if args.json else render(rep, args.markdown))
    sys.stdout.flush()
    sys.stderr.flush()
    # leave at once: after the budget, up to 8 workers may still be mid-request
    os._exit(1 if args.strict and rep["broken"] else 0)


if __name__ == "__main__":
    main()
