#!/usr/bin/env python3
"""Print health metrics for a second-brain vault.

Usage:
    python3 vault_stats.py /path/to/vault

Reports page counts by type, link density, orphan rate and the most connected
pages. Track these over time: a rising orphan rate means ingestion is running
without linking, which is the usual way a vault stops being useful.

Links: `[[Page]]` matches a file name or an alias; `[[folder/Page]]` matches the
vault-relative path first and falls back to the file name.
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TYPE = re.compile(r"^type:\s*(\S+)", re.M)
# Hidden folders (.claude, .obsidian, .git, .trash), the page templates and
# the scripts folder hold instructions and tooling, not knowledge, so they are
# never counted as pages. Same for CLAUDE.md and README.md wherever they sit.
SKIP_DIRS = {"node_modules", "raw", "templates", "scripts", "archive", "journal", "output"}
SKIP_FILES = {"CLAUDE.md", "README.md"}


def is_page(name):
    return name.endswith(".md") and name not in SKIP_FILES


def prune(dirnames):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]


def aliases_of(text):
    """Names from a flow-style `aliases: [a, b]` line in the frontmatter."""
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    m2 = m and re.search(r"^aliases:[ \t]*\[(.*?)\]", m.group(1), re.M)
    if not m2:
        return []
    return [a.strip().strip("\"'") for a in m2.group(1).split(",") if a.strip()]


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
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("vault")
    ap.add_argument("--include", default="", metavar="DIRS",
                    help="comma-separated folders to count anyway, e.g. archive,journal")
    args = ap.parse_args()
    SKIP_DIRS.difference_update(x.strip() for x in args.include.split(","))
    vault = args.vault

    pages, types = {}, Counter()
    for dirpath, dirnames, filenames in os.walk(vault):
        prune(dirnames)
        for name in filenames:
            if is_page(name):
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8-sig", errors="replace") as fh:
                    text = fh.read()
                pages[path] = text
                m = TYPE.search(text)
                types[m.group(1) if m else "untyped"] += 1

    if not pages:
        sys.exit("no markdown files found")

    by_path = {rel_key(vault, p): p for p in pages}
    stems = {}
    for p in sorted(pages):
        stems.setdefault(os.path.splitext(os.path.basename(p))[0].lower(), p)
    for p in sorted(pages):
        for a in aliases_of(pages[p]):
            stems.setdefault(a.lower(), p)
    indeg = defaultdict(int)
    total = 0
    for path, text in pages.items():
        for target in LINK.findall(text):
            dest = resolve(target, by_path, stems)
            if dest and dest != path:
                indeg[dest] += 1
                total += 1

    orphans = [p for p in pages if indeg[p] == 0 and not p.endswith(("index.md", "log.md"))]
    words = sum(len(t.split()) for t in pages.values())

    print(f"pages          {len(pages)}")
    for t, c in types.most_common():
        print(f"  {t:<12} {c}")
    print(f"words          {words:,}")
    print(f"links          {total}")
    print(f"avg degree     {total / len(pages):.2f}")
    print(f"orphan rate    {100 * len(orphans) / len(pages):.1f}%")
    print("\nmost linked:")
    for path, n in sorted(indeg.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {n:>4}  {os.path.relpath(path, vault)}")


if __name__ == "__main__":
    main()
