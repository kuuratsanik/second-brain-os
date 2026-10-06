#!/usr/bin/env python3
"""Check a second-brain vault for broken wikilinks, orphan pages and stubs.

Usage:
    python3 link_check.py /path/to/vault [--json]

No dependencies. Reads only; never modifies the vault.

Links: `[[Page]]` matches a file name or an alias; `[[folder/Page]]` matches the
vault-relative path first and falls back to the file name.
"""
import argparse
import json
import os
import re
import sys

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
# Hidden folders (.claude, .obsidian, .git, .trash), the page templates and
# the scripts folder hold instructions and tooling, not knowledge, so they are
# never counted as pages. Same for CLAUDE.md and README.md wherever they sit.
SKIP_DIRS = {"node_modules", "raw", "templates", "scripts", "archive", "journal", "output"}
SKIP_FILES = {"CLAUDE.md", "README.md"}


def is_page(name):
    return name.endswith(".md") and name not in SKIP_FILES


def prune(dirnames):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]


STUB_WORDS = 40


def collect(vault):
    pages = {}
    for dirpath, dirnames, filenames in os.walk(vault):
        prune(dirnames)
        for name in filenames:
            if not is_page(name):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8-sig", errors="replace") as fh:
                text = fh.read()
            pages[path] = text
    return pages


def title_of(path, text):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem


_PROP = re.compile(r"^(?:[&!]\S*(?:\s+|$))+")  # YAML anchor or tag


def _scalar(s):
    """One YAML scalar: quotes stripped, `\\"` and `\\\\` unescaped in double
    quotes, `''` in single quotes, a trailing ` # comment` dropped when plain."""
    s = _PROP.sub("", s.strip())
    if s[:1] == '"':
        out, i = [], 1
        while i < len(s) and s[i] != '"':
            if s[i] == "\\" and i + 1 < len(s):
                i += 1
            out.append(s[i])
            i += 1
        return "".join(out)
    if s[:1] == "'":
        out, i = [], 1
        while i < len(s):
            if s[i] == "'":
                if s[i + 1:i + 2] != "'":
                    break
                i += 1
            out.append(s[i])
            i += 1
        return "".join(out)
    return re.sub(r"\s+#.*$", "", s).strip()


def _flow_items(s):
    """Split the inside of a flow list on commas outside quotes, up to `]`. An
    unclosed list stops at the next line that looks like a `key:`."""
    items, cur, quote, i = [], [], None, 0
    while i < len(s):
        c = s[i]
        if quote:
            cur.append(c)
            if quote == '"' and c == "\\" and i + 1 < len(s):
                i += 1
                cur.append(s[i])
            elif c == quote:
                if quote == "'" and s[i + 1:i + 2] == "'":
                    i += 1
                    cur.append("'")
                else:
                    quote = None
        elif c == "\n" and re.match(r"[A-Za-z_][\w-]*:", s[i + 1:]):
            items.append("".join(cur))
            return items
        elif c in "\"'" and not "".join(cur).strip():
            quote = c
            cur.append(c)
        elif c in ",]":
            items.append("".join(cur))
            cur = []
            if c == "]":
                break
        else:
            cur.append(c)
        i += 1
    return items


def aliases_of(text):
    """Names from `aliases:` in the frontmatter: a flow list `[a, "b, c"]`, a
    block list of `- item` lines, or a single scalar. Quotes are stripped.
    Expects normalized text (read with utf-8-sig, text mode), not raw bytes."""
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    m2 = m and re.search(r"^aliases:[ \t]*(.*)$", m.group(1), re.M)
    if not m2:
        return []
    rest = _PROP.sub("", m2.group(1).strip())
    if rest.startswith("["):
        raw = _flow_items(m.group(1)[m2.start(1) + m2.group(1).index("[") + 1:])
    elif rest and not rest.startswith("#"):
        raw = [rest]
    else:
        raw = []
        for line in m.group(1)[m2.end():].lstrip("\n").split("\n"):
            b = re.match(r"^[ \t]*-[ \t]+(.*)$", line)
            if not b:
                if line.strip() and not line.lstrip().startswith("#"):
                    break
                continue
            raw.append(b.group(1))
    return [a for a in (_scalar(x) for x in raw) if a]


def link_key(target):
    """Normalise a wikilink target: backslashes become '/', `.md` and case go."""
    t = target.strip().replace("\\", "/").strip("/")
    if t.lower().endswith(".md"):
        t = t[:-3]
    return t.lower()


def rel_key(vault, path):
    """Vault-relative path without `.md`, lower case, with '/' on every OS."""
    return os.path.relpath(path, vault).replace(os.sep, "/")[:-3].lower()


def resolve(target, by_path, by_name):
    """Find the page a wikilink points at.

    A target with a '/' (`[[people/Ann]]`) is matched against the vault-relative
    path first, so two pages named Ann in different folders stay distinct. If no
    path matches, or the target has no '/', it matches the file name or an
    alias. When several pages share a name, a bare `[[Ann]]` goes to the first
    in path order.
    """
    key = link_key(target)
    if "/" in key:
        if key in by_path:
            return by_path[key]
        key = key.rsplit("/", 1)[-1]
    return by_name.get(key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include", default="", metavar="DIRS",
                    help="comma-separated folders to count anyway, e.g. archive,journal")
    args = ap.parse_args()
    SKIP_DIRS.difference_update(x.strip() for x in args.include.split(","))

    if not os.path.isdir(args.vault):
        sys.exit(f"not a directory: {args.vault}")

    pages = collect(args.vault)
    by_path = {rel_key(args.vault, p): p for p in pages}
    names = {}
    for path in sorted(pages):
        names.setdefault(title_of(path, pages[path]).lower(), path)
    for path in sorted(pages):
        for a in aliases_of(pages[path]):
            names.setdefault(a.lower(), path)

    outbound = {p: set() for p in pages}
    inbound = {p: set() for p in pages}
    broken = []

    for path, text in pages.items():
        for target in LINK.findall(text):
            dest = resolve(target, by_path, names)
            if dest:
                if dest != path:
                    outbound[path].add(dest)
                    inbound[dest].add(path)
            else:
                broken.append((path, target.strip()))

    orphans = [p for p in pages if not inbound[p] and not p.endswith(("index.md", "log.md", "README.md"))]
    stubs = [p for p, t in pages.items() if len(t.split()) < STUB_WORDS]
    links = sum(len(v) for v in outbound.values())

    result = {
        "pages": len(pages),
        "links": links,
        "avg_links_per_page": round(links / len(pages), 2) if pages else 0,
        "broken": [{"page": os.path.relpath(p, args.vault), "target": t} for p, t in broken],
        "orphans": [os.path.relpath(p, args.vault) for p in sorted(orphans)],
        "stubs": [os.path.relpath(p, args.vault) for p in sorted(stubs)],
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"pages: {result['pages']}")
    print(f"links: {result['links']} (avg {result['avg_links_per_page']} per page)")
    print(f"broken links: {len(result['broken'])}")
    for b in result["broken"][:40]:
        print(f"  {b['page']} -> [[{b['target']}]]")
    print(f"orphans: {len(result['orphans'])}")
    for o in result["orphans"][:40]:
        print(f"  {o}")
    print(f"stubs (<{STUB_WORDS} words): {len(result['stubs'])}")
    for s in result["stubs"][:40]:
        print(f"  {s}")


if __name__ == "__main__":
    main()
