#!/usr/bin/env python3
"""Export a vault's wikilink graph as CSV edges or GraphML.

Usage:
    python3 graph_export.py /path/to/vault edges.csv
    python3 graph_export.py /path/to/vault graph.graphml --format graphml

CSV loads into NetworkX, Kuzu, Neo4j or a spreadsheet. GraphML opens in Gephi.
No dependencies.
"""
import argparse
import csv
import os
import re
from xml.sax.saxutils import escape

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


def load(vault):
    pages = {}
    for dirpath, dirnames, filenames in os.walk(vault):
        prune(dirnames)
        for name in filenames:
            if is_page(name):
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8-sig", errors="replace") as fh:
                    pages[path] = fh.read()
    return pages


def aliases_of(text):
    """Names from a flow-style `aliases: [a, b]` line in the frontmatter."""
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    m2 = m and re.search(r"^aliases:[ \t]*\[(.*?)\]", m.group(1), re.M)
    if not m2:
        return []
    return [a.strip().strip("\"'") for a in m2.group(1).split(",") if a.strip()]


def link_key(target):
    """Normalise a wikilink target: folder/Page.md and Page both mean `page`."""
    t = target.strip().replace("\\", "/").rsplit("/", 1)[-1]
    if t.lower().endswith(".md"):
        t = t[:-3]
    return t.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("out")
    ap.add_argument("--format", choices=["csv", "graphml"], default="csv")
    ap.add_argument("--include", default="", metavar="DIRS",
                    help="comma-separated folders to count anyway, e.g. archive,journal")
    args = ap.parse_args()
    SKIP_DIRS.difference_update(x.strip() for x in args.include.split(","))

    pages = load(args.vault)
    stems = {os.path.splitext(os.path.basename(p))[0]: p for p in pages}
    lower = {}
    for stem, path in stems.items():
        for a in aliases_of(pages[path]):
            lower.setdefault(a.lower(), stem)
    lower.update({k.lower(): k for k in stems})

    nodes = {}
    for stem, path in stems.items():
        m = TYPE.search(pages[path])
        nodes[stem] = m.group(1) if m else "untyped"

    edges = []
    for stem, path in stems.items():
        for target in LINK.findall(pages[path]):
            key = lower.get(link_key(target))
            if key and key != stem:
                edges.append((stem, key))

    if args.format == "csv":
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["source", "target"])
            w.writerows(edges)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            fh.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
            fh.write('<key id="t" for="node" attr.name="type" attr.type="string"/>\n')
            fh.write('<graph edgedefault="directed">\n')
            for n, t in nodes.items():
                fh.write(f'<node id="{escape(n)}"><data key="t">{escape(t)}</data></node>\n')
            for i, (s, t) in enumerate(edges):
                fh.write(f'<edge id="e{i}" source="{escape(s)}" target="{escape(t)}"/>\n')
            fh.write("</graph>\n</graphml>\n")

    print(f"{len(nodes)} nodes, {len(edges)} edges -> {args.out}")


if __name__ == "__main__":
    main()
