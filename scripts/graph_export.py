#!/usr/bin/env python3
"""Export a vault's wikilink graph as CSV edges or GraphML.

Usage:
    python3 graph_export.py /path/to/vault edges.csv
    python3 graph_export.py /path/to/vault graph.graphml --format graphml

CSV loads into NetworkX, Kuzu, Neo4j or a spreadsheet. GraphML opens in Gephi.
No dependencies.

Links: `[[Page]]` matches a file name or an alias; `[[folder/Page]]` matches the
vault-relative path first and falls back to the file name. Nodes and edges are
emitted in path order, so the output is the same on every run.
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
    ap.add_argument("out")
    ap.add_argument("--format", choices=["csv", "graphml"], default="csv")
    ap.add_argument("--include", default="", metavar="DIRS",
                    help="comma-separated folders to count anyway, e.g. archive,journal")
    args = ap.parse_args()
    SKIP_DIRS.difference_update(x.strip() for x in args.include.split(","))

    pages = load(args.vault)
    order = sorted(pages)
    by_path = {rel_key(args.vault, p): p for p in order}
    stem_of = {p: os.path.splitext(os.path.basename(p))[0] for p in order}
    counts = {}
    for st in stem_of.values():
        counts[st.lower()] = counts.get(st.lower(), 0) + 1
    # A node is its file name, or its vault-relative path when two pages share a name.
    node_id = {p: stem_of[p] if counts[stem_of[p].lower()] == 1
               else os.path.relpath(p, args.vault).replace(os.sep, "/")[:-3] for p in order}

    names = {}
    for p in order:
        names.setdefault(stem_of[p].lower(), p)
    for p in order:
        for a in aliases_of(pages[p]):
            names.setdefault(a.lower(), p)

    nodes = {}
    for p in order:
        m = TYPE.search(pages[p])
        nodes[node_id[p]] = m.group(1) if m else "untyped"

    edges = []
    for p in order:
        for target in LINK.findall(pages[p]):
            dest = resolve(target, by_path, names)
            if dest and dest != p:
                edges.append((node_id[p], node_id[dest]))

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
