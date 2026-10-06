#!/usr/bin/env python3
"""Search a second-brain vault: BM25 by default, optional embeddings.

Usage:
    python3 vault_search.py /path/to/vault "query" [--limit N] [--json]
        [--include-archive] [--include-restricted]
        [--embed-url URL] [--embed-cache PATH]

Ranks pages title > aliases > h2 headings > body and prints `path:line`, so an
answer can cite the line. Unicode is NFC plus casefold; diacritics must match
(`õppimine` finds `õppimine`), and a folded fallback lets `oppimine` find it at
a lower score. Pages with `sensitivity: restricted` are left out unless
`--include-restricted`.

With `--embed-url` (a llama.cpp `llama-server` started with `--embedding`) the
ranking is hybrid: BM25 and cosine similarity fused by reciprocal rank fusion.
Chunk vectors are cached by content hash, so only changed chunks are embedded.
If the server cannot be reached the script warns on stderr and uses BM25.

No dependencies. Reads only, except for the embedding cache. Exit codes: 0
(with or without hits), 1 for a bad vault path, 2 for a usage error.

From Python: `search(vault, query, limit=10, ...)` returns the list of hits.
"""
import argparse
import array
import base64
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from operator import mul

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import link_check as lc  # noqa: E402  (shared page walk, frontmatter and skip dirs)

# BM25 parameters and the weight of a term occurrence by field.
K1, B = 1.2, 0.75
WEIGHTS = {"title": 8.0, "alias": 5.0, "h2": 3.0, "body": 1.0}
FOLDED_FACTOR = 0.6  # a folded-diacritics match scores this fraction of an exact one
SNIPPET = 200
CHUNK_CHARS = 600
BATCH = 16
RRF_K = 60

_WORD = re.compile(r"\w+")


def norm(s):
    """NFC plus casefold."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFC", s).casefold())


def fold(s):
    """Drop diacritics: `õppimine` becomes `oppimine`."""
    d = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn"))


def tokens(s):
    return _WORD.findall(norm(s))


# ---------------------------------------------------------------- pages


def front_of(text):
    """(frontmatter text, number of lines the block takes). The block ends at the
    closing `---` line, the same one link_check reads."""
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not m or m.start() != 0:
        return "", 0
    return m.group(1), m.group(0).count("\n") + 1


def sensitivity_of(text):
    return lc._field(text, "sensitivity").strip().lower() or "normal"


class Page:
    def __init__(self, vault, path, text):
        self.path = os.path.relpath(path, vault).replace(os.sep, "/")
        self.sensitivity = sensitivity_of(text)
        front, n_front = front_of(text)
        self.lines = text.split("\n")
        self.body_from = n_front  # index of the first line after the frontmatter
        stem = os.path.splitext(os.path.basename(path))[0]
        h1 = next((m.group(1).strip() for m in (re.match(r"#[ \t]+(.+)", ln) for ln in self.lines[n_front:]) if m), "")
        self.title = lc._field(text, "title") or h1 or stem
        self.aliases = lc.aliases_of(text)
        fields = {"title": f"{self.title} {stem}", "alias": " ".join(self.aliases), "h2": [], "body": []}
        in_fence = False
        for ln in self.lines[n_front:]:
            if ln.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
            elif not in_fence and re.match(r"##[ \t]+\S", ln):
                fields["h2"].append(ln.lstrip("#").strip())
            fields["body"].append(ln)
        fields["h2"] = " ".join(fields["h2"])
        fields["body"] = "\n".join(fields["body"])
        self.fields = fields


class Index:
    """BM25F-style index over pages. Build once, query many times."""

    def __init__(self, pages):
        self.pages = pages
        self.exact = {}   # term -> {doc: weighted tf}
        self.folded = {}
        self.dl = []
        for i, p in enumerate(pages):
            length = 0.0
            ex, fo = {}, {}
            for name, text in p.fields.items():
                w = WEIGHTS[name]
                for t in tokens(text):
                    ex[t] = ex.get(t, 0.0) + w
                    f = fold(t)
                    fo[f] = fo.get(f, 0.0) + w
                    length += w
            self.dl.append(length)
            for t, v in ex.items():
                self.exact.setdefault(t, {})[i] = v
            for t, v in fo.items():
                self.folded.setdefault(t, {})[i] = v
        n = len(pages)
        self.avgdl = (sum(self.dl) / n) if n else 1.0

    def _term_scores(self, postings, term, scores, only_missing_from=None, factor=1.0):
        post = postings.get(term)
        if not post:
            return
        n = len(self.pages)
        idf = math.log(1 + (n - len(post) + 0.5) / (len(post) + 0.5))
        for d, tf in post.items():
            if only_missing_from is not None and d in only_missing_from:
                continue
            denom = tf + K1 * (1 - B + B * self.dl[d] / self.avgdl)
            scores[d] = scores.get(d, 0.0) + factor * idf * tf * (K1 + 1) / denom

    def rank(self, query):
        """[(doc, score)] best first, ties by path."""
        scores = {}
        for t in dict.fromkeys(tokens(query)):
            hit_exact = self.exact.get(t, {})
            self._term_scores(self.exact, t, scores)
            self._term_scores(self.folded, fold(t), scores, only_missing_from=hit_exact, factor=FOLDED_FACTOR)
        return sorted(scores.items(), key=lambda kv: (-kv[1], self.pages[kv[0]].path))


def build_index(vault, include_archive=False, include_restricted=False):
    skip = set(lc.SKIP_DIRS)
    if include_archive:
        skip.discard("archive")
    pages = []
    texts = lc.collect(vault, skip)
    for path in sorted(texts, key=lambda p: os.path.relpath(p, vault).replace(os.sep, "/")):
        page = Page(vault, path, texts[path])
        if page.sensitivity == "restricted" and not include_restricted:
            continue
        pages.append(page)
    return Index(pages)


# ---------------------------------------------------------------- hits


def best_line(page, query):
    """(1-based line, snippet) of the line with the most distinct query terms,
    then the most occurrences, then the earliest. A page that matches only in its
    title or aliases points at the `title:` or `aliases:` line, else line 1."""
    q = dict.fromkeys(tokens(query))
    qf = {fold(t) for t in q}
    best, best_key = None, (0, 0)
    for i in range(page.body_from, len(page.lines)):
        toks = tokens(page.lines[i])
        if not toks:
            continue
        exact = {t for t in toks if t in q}
        folded = {fold(t) for t in toks} & qf
        distinct = max(len(exact), len(folded))
        if not distinct:
            continue
        key = (distinct, sum(1 for t in toks if t in q or fold(t) in qf))
        if key > best_key:
            best, best_key = i, key
    if best is None:
        best = 0
        for i in range(min(page.body_from, len(page.lines))):
            if re.match(r"(title|aliases):", page.lines[i]) and (
                    {fold(t) for t in tokens(page.lines[i])} & qf):
                best = i
                break
    return best + 1, snippet(page.lines, best, q, qf)


def snippet(lines, i, q, qf):
    """About SNIPPET characters starting at line i, centred on the first match
    when the line is longer than that."""
    first = " ".join(lines[i].split())
    off = 0
    for m in _WORD.finditer(norm(first)):
        if m.group(0) in q or fold(m.group(0)) in qf:
            off = m.start()
            break
    text = first
    j = i + 1
    while len(text) < SNIPPET and j < len(lines):
        more = " ".join(lines[j].split())
        if more:
            text += " " + more
        j += 1
    start = 0
    if off > SNIPPET // 3:
        start = max(0, off - SNIPPET // 3)
        start = text.rfind(" ", 0, start) + 1 or start
    out = text[start:start + SNIPPET].strip()
    return ("..." if start else "") + out + ("..." if start + SNIPPET < len(text) else "")


def make_hit(page, score, query, line=None, snip=None):
    if line is None:
        line, snip = best_line(page, query)
    return {"path": page.path, "title": page.title, "score": round(score, 4), "line": line,
            "snippet": snip, "sensitivity": page.sensitivity}


# ---------------------------------------------------------------- embeddings
# Endpoint: llama.cpp tools/server/README.md, "POST /v1/embeddings: OpenAI-compatible
# embeddings API" (fetched 2026-10-06 from
# https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
# Request: {"input": ["text", ...], "model": "...", "encoding_format": "float"}.
# Response (OpenAI shape): {"model": ..., "data": [{"index": i, "embedding": [...]}]}.
# The server must run with an embedding model and a pooling other than `none`,
# and the vectors come back normalised with the Euclidean norm. The non-OpenAI
# `/embedding` endpoint (request {"content": ...}) is not used.


class EmbedError(Exception):
    pass


def embed_endpoint(url):
    u = url.rstrip("/")
    if u.endswith(("/v1/embeddings", "/embeddings")):
        return u
    return u + "/v1/embeddings"


def _is_loopback(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1") or host.startswith("127.")


def embed_texts(url, texts, timeout=60):
    """One request for `texts`; returns (model, [vector]) in input order."""
    body = json.dumps({"input": texts, "model": "embedding", "encoding_format": "float"}).encode("utf-8")
    req = urllib.request.Request(embed_endpoint(url), data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer no-key"})
    # A system proxy must not sit between this script and a server on the same machine.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if _is_loopback(url) \
        else urllib.request.build_opener()
    try:
        with opener.open(req, timeout=timeout) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
        data = sorted(doc["data"], key=lambda d: d["index"])
        vecs = [[float(x) for x in d["embedding"]] for d in data]
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as e:
        raise EmbedError(str(getattr(e, "reason", e)) or type(e).__name__) from e
    if len(vecs) != len(texts) or not all(vecs) or len({len(v) for v in vecs}) != 1:
        raise EmbedError("unexpected response from the embedding server")
    return str(doc.get("model", "")), vecs


def chunk_page(page):
    """[(start line index, text)] of about CHUNK_CHARS characters, split on blank
    lines where possible. Each text starts with the page title."""
    chunks, cur, cur_len, start = [], [], 0, None

    def flush():
        nonlocal cur, cur_len, start
        if cur:
            chunks.append((start, page.title + "\n" + "\n".join(cur)))
        cur, cur_len, start = [], 0, None

    for i in range(page.body_from, len(page.lines)):
        ln = page.lines[i].rstrip()
        if not ln.strip():
            if cur_len >= CHUNK_CHARS // 2:
                flush()
            continue
        if cur_len + len(ln) > CHUNK_CHARS and cur:
            flush()
        while len(ln) > CHUNK_CHARS:  # one very long line
            if cur:
                flush()
            chunks.append((i, page.title + "\n" + ln[:CHUNK_CHARS]))
            ln = ln[CHUNK_CHARS:]
        if ln:
            if start is None:
                start = i
            cur.append(ln)
            cur_len += len(ln) + 1
    flush()
    return chunks


def chunk_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pack(vec):
    a = array.array("f", vec)
    if sys.byteorder == "big":
        a.byteswap()
    return base64.b64encode(a.tobytes()).decode("ascii")


def _unpack(s):
    a = array.array("f")
    a.frombytes(base64.b64decode(s))
    if sys.byteorder == "big":
        a.byteswap()
    return a


def load_cache(path, model_hint=None):
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("version") != 1:
            return {"model": "", "vectors": {}}
        return {"model": doc.get("model", ""), "vectors": doc.get("vectors", {})}
    except (OSError, ValueError, AttributeError):
        return {"model": "", "vectors": {}}


def save_cache(path, cache, keep):
    """Write only the vectors of `keep` (the current chunk hashes), atomically."""
    doc = {"version": 1, "model": cache["model"],
           "vectors": {h: v for h, v in sorted(cache["vectors"].items()) if h in keep}}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))
        os.replace(tmp, path)
    except OSError as e:
        sys.stderr.write(f"warning: could not write the embedding cache: {e}\n")


def _unit(a):
    n = math.sqrt(sum(map(mul, a, a))) or 1.0
    return array.array("f", (x / n for x in a))


def semantic_rank(index, query, url, cache_path, stats=None):
    """[(doc, cosine, chunk line index)] best first, one entry per page. Raises
    EmbedError when the server fails. `stats` collects cache hits and misses."""
    cache = load_cache(cache_path)
    chunks = []  # (doc, start line, hash, text)
    for d, page in enumerate(index.pages):
        for start, text in chunk_page(page):
            chunks.append((d, start, chunk_hash(text), text))
    missing, seen = [], set()
    for _, _, h, text in chunks:
        if h not in cache["vectors"] and h not in seen:
            seen.add(h)
            missing.append((h, text))
    if stats is not None:
        stats.update(chunks=len(chunks), hits=len(chunks) - len(missing), misses=len(missing))

    dirty = False
    try:
        qmodel, qvecs = embed_texts(url, [query])
        if cache["model"] and qmodel and qmodel != cache["model"]:
            # another model: the stored vectors are not comparable
            cache["vectors"], missing = {}, list(dict.fromkeys((h, t) for _, _, h, t in chunks))
            dirty = True
        cache["model"] = qmodel or cache["model"]
        for i in range(0, len(missing), BATCH):
            batch = missing[i:i + BATCH]
            _, vecs = embed_texts(url, [t for _, t in batch])
            for (h, _), v in zip(batch, vecs):
                cache["vectors"][h] = _pack(v)
            dirty = True
    finally:
        if dirty:
            save_cache(cache_path, cache, {h for _, _, h, _ in chunks})

    q = _unit(qvecs[0])
    best = {}
    unpacked = {}
    for d, start, h, _ in chunks:
        v = unpacked.get(h)
        if v is None:
            v = unpacked[h] = _unit(_unpack(cache["vectors"][h]))
        if len(v) != len(q):
            raise EmbedError("cached vectors have a different size; delete " + cache_path)
        c = sum(map(mul, q, v))
        if d not in best or c > best[d][0]:
            best[d] = (c, start)
    return sorted(((d, c, s) for d, (c, s) in best.items()),
                  key=lambda r: (-r[1], index.pages[r[0]].path))


def search(vault, query, limit=10, include_archive=False, include_restricted=False,
           embed_url=None, embed_cache=None, index=None, info=None, warn=None):
    """Hits for `query`, best first: dicts with path, title, score, line, snippet
    and sensitivity. `path` is vault-relative with '/'. Pass a prebuilt `index`
    (see build_index) to search repeatedly. `info`, if a dict, receives `mode`
    ("bm25" or "hybrid") and cache counts. `warn(msg)` receives warnings; the
    default writes to stderr."""
    warn = warn or (lambda m: sys.stderr.write(f"warning: {m}\n"))
    if index is None:
        index = build_index(vault, include_archive, include_restricted)
    ranked = index.rank(query)
    mode = "bm25"
    hits = None
    if embed_url and index.pages:
        cache_path = embed_cache or os.path.join(vault, ".cache", "embeddings.json")
        stats = {}
        try:
            if not _is_loopback(embed_url):
                warn("the embedding server is not on this machine; page text is sent to it")
            sem = semantic_rank(index, query, embed_url, cache_path, stats)
            mode = "hybrid"
        except EmbedError as e:
            warn(f"embedding server unavailable ({e}); using BM25 only")
            sem = None
        if info is not None and stats:
            info.update(stats)
        if sem is not None:
            n = max(50, limit * 5)
            fused, chunk_line = {}, {}
            for r, (d, _) in enumerate(ranked[:n]):
                fused[d] = fused.get(d, 0.0) + 1.0 / (RRF_K + r + 1)
            lexical = {d for d, _ in ranked}
            for r, (d, _c, start) in enumerate(sem[:n]):
                fused[d] = fused.get(d, 0.0) + 1.0 / (RRF_K + r + 1)
                chunk_line[d] = start
            order = sorted(fused.items(), key=lambda kv: (-kv[1], index.pages[kv[0]].path))
            hits = []
            for d, score in order[:limit]:
                page = index.pages[d]
                if d in lexical or d not in chunk_line:
                    hits.append(make_hit(page, score, query))
                else:  # a semantic-only hit: cite the start of its best chunk
                    q = dict.fromkeys(tokens(query))
                    hits.append(make_hit(page, score, query, chunk_line[d] + 1,
                                         snippet(page.lines, chunk_line[d], q, {fold(t) for t in q})))
                hits[-1]["score"] = round(score, 6)
    if hits is None:
        hits = [make_hit(index.pages[d], s, query) for d, s in ranked[:limit]]
    if info is not None:
        info["mode"] = mode
    return hits


# ---------------------------------------------------------------- CLI


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("vault")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10, metavar="N", help="hits to show (default 10)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-archive", action="store_true", help="also search archive/")
    ap.add_argument("--include-restricted", action="store_true",
                    help="also search pages with `sensitivity: restricted`")
    ap.add_argument("--embed-url", metavar="URL",
                    help="llama-server base URL (started with --embedding); enables hybrid ranking")
    ap.add_argument("--embed-cache", metavar="PATH",
                    help="embedding cache (default VAULT/.cache/embeddings.json)")
    args = ap.parse_args(argv)
    if args.limit < 1:
        ap.error("--limit must be at least 1")
    if not args.query.strip():
        ap.error("the query is empty")
    if not os.path.isdir(args.vault):
        sys.stderr.write(f"not a directory: {args.vault}\n")
        return 1

    info = {}
    hits = search(args.vault, args.query, args.limit, args.include_archive, args.include_restricted,
                  args.embed_url, args.embed_cache, info=info)
    if args.json:
        lines = [json.dumps({"query": args.query, "mode": info["mode"], "count": len(hits),
                             "hits": hits}, indent=2, ensure_ascii=False)]
    else:
        lines = []
        for i, h in enumerate(hits, 1):
            tag = "" if h["sensitivity"] == "normal" else f"  [{h['sensitivity']}]"
            lines.append(f"{i}. {h['path']}:{h['line']}  {h['title']}  (score {h['score']}){tag}")
            lines.append(f"   {h['snippet']}")
        if not hits:
            lines.append("no hits")
    lc.emit(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
