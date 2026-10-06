#!/usr/bin/env python3
"""Check relative markdown links in docs/ and README.md. Stdlib only.

A link is broken when its target file or folder does not exist, or when its
#anchor matches no heading in the target markdown file (GitHub slug rules).
Links inside code fences and inline code are ignored, as are URLs.

    python3 tools/doc_links.py            # from anywhere; exit 1 on any failure
    python3 tools/doc_links.py --selftest # check the checker itself
"""
import glob
import io
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"!?\[(?:[^\]\\]|\\.)*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def fenced_lines(text):
    """Yield (line, in_code_block); fence lines themselves count as code."""
    fence = None
    for line in text.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            yield line, True
            continue
        yield line, fence is not None


def strip_code(text):
    """Lines with fenced blocks blanked and inline code removed (for links)."""
    return ["" if code else re.sub(r"`+[^`]*`+", "", line)
            for line, code in fenced_lines(text)]


def slug(heading):
    h = re.sub(r"<[^>]+>", "", heading)
    h = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = re.sub(r"[*_`]", "", h).strip().lower()
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


_anchors = {}


def anchors(path):
    if path not in _anchors:
        seen, found = {}, set()
        text = io.open(path, encoding="utf-8").read()
        for line, code in fenced_lines(text):
            m = None if code else re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
            if m:
                s = slug(m.group(1))
                n = seen.get(s, 0)
                seen[s] = n + 1
                found.add(s if n == 0 else f"{s}-{n}")
        for m in re.finditer(r'(?:id|name)="([^"]+)"', text):
            found.add(m.group(1))
        _anchors[path] = found
    return _anchors[path]


def check(path):
    errs = []
    text = io.open(path, encoding="utf-8").read()
    for n, line in enumerate(strip_code(text), 1):
        for m in LINK.finditer(line):
            target = m.group(1)
            if SCHEME.match(target) or target.startswith("//"):
                continue
            file_part, _, frag = target.partition("#")
            dest = path if not file_part else os.path.normpath(
                os.path.join(os.path.dirname(path), unquote(file_part)))
            where = f"{os.path.relpath(path, ROOT)}:{n}"
            if not os.path.exists(dest):
                errs.append(f"{where}: missing file {target}")
            elif frag and dest.endswith(".md") and os.path.isfile(dest):
                if unquote(frag).lower() not in anchors(dest):
                    errs.append(f"{where}: no heading for #{frag} in "
                                f"{os.path.relpath(dest, ROOT)}")
    return errs


def selftest():
    import tempfile
    body = ("# Title\n\n## The `raw/` folder\n\n## Dup\n\n## Dup\n\n"
            "## A & B: C.d!\n\n## [Link](x.md) text\n\n```\n## not a heading\n```\n\n"
            "<a id=\"custom\"></a>\n")
    src = ("# S\n[ok](t.md#the-raw-folder) [dup](t.md#dup-1) [punct](t.md#a--b-cd) "
           "[lnk](t.md#link-text) [id](t.md#custom) [self](#s) [url](https://x.y/z) "
           "`[code](gone.md)`\n```\n[fenced](gone.md)\n```\n"
           "[bad1](gone.md) [bad2](t.md#nope) [bad3](t.md#not-a-heading)\n")
    with tempfile.TemporaryDirectory() as d:
        io.open(os.path.join(d, "t.md"), "w", encoding="utf-8").write(body)
        io.open(os.path.join(d, "s.md"), "w", encoding="utf-8").write(src)
        errs = check(os.path.join(d, "s.md"))
    want = ["missing file gone.md", "no heading for #nope", "no heading for #not-a-heading"]
    ok = len(errs) == 3 and all(w in e for w, e in zip(want, errs))
    print("selftest", "ok" if ok else "FAILED")
    if not ok:
        for e in errs:
            print("  ", e)
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    files = [os.path.join(ROOT, "README.md")] + sorted(
        glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True))
    errs = [e for f in files if os.path.exists(f) for e in check(f)]
    for e in errs:
        print(e)
    print(f"{len(files)} files checked, {len(errs)} broken links")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
