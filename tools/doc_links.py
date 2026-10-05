#!/usr/bin/env python3
"""Check relative markdown links in docs/ and README.md. Stdlib only.

A link is broken when its target file or folder does not exist, or when its
#anchor matches no heading in the target markdown file (GitHub slug rules).
Links inside code fences and inline code are ignored, as are URLs.

    python3 tools/doc_links.py            # from anywhere; exit 1 on any failure
"""
import glob, io, os, re, sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"!?\[(?:[^\]\\]|\\.)*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def strip_code(text):
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            out.append("")
            continue
        out.append("" if fence else re.sub(r"`+[^`]*`+", "", line))
    return out


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
        for line in strip_code(text):
            m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
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


def main():
    files = [os.path.join(ROOT, "README.md")] + sorted(
        glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True))
    errs = [e for f in files if os.path.exists(f) for e in check(f)]
    for e in errs:
        print(e)
    print(f"{len(files)} files checked, {len(errs)} broken links")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
