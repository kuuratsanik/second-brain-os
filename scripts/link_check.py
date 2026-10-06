#!/usr/bin/env python3
"""Check a second-brain vault for broken wikilinks, orphan pages and stubs.

Usage:
    python3 link_check.py /path/to/vault [--json] [--include DIRS]
    python3 link_check.py /path/to/vault --stale DAYS
    python3 link_check.py /path/to/vault --duplicates

No dependencies. Reads only; never modifies the vault.

Links: `[[Page]]` matches a file name or an alias; `[[folder/Page]]` matches the
vault-relative path first and falls back to the file name.
"""
import argparse
import datetime
import errno
import json
import os
import re
import sys
import unicodedata

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
# Hidden folders (.claude, .obsidian, .git, .trash), the page templates and
# the scripts folder hold instructions and tooling, not knowledge, so they are
# never counted as pages. Same for CLAUDE.md and README.md wherever they sit.
SKIP_DIRS = {"node_modules", "raw", "templates", "scripts", "archive", "journal", "output"}
SKIP_FILES = {"CLAUDE.md", "README.md"}


def is_page(name):
    return name.endswith(".md") and name not in SKIP_FILES


def prune(dirnames, skip=None):
    skip = SKIP_DIRS if skip is None else skip
    dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]


STUB_WORDS = 40


def collect(vault, skip=None):
    """{path: text} for every counted page. `skip` replaces SKIP_DIRS for this
    call, so a library caller can include a folder without touching the module."""
    pages = {}
    for dirpath, dirnames, filenames in os.walk(vault):
        prune(dirnames, skip)
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


def _front(text):
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def _field(text, key):
    m = re.search(rf"^{key}:[ \t]*(.*)$", _front(text), re.M)
    return _scalar(m.group(1)) if m else ""


_DAY = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)", re.ASCII)


def _day(value):
    """A YYYY-MM-DD date, or None. `[[2020-01-05]]` and `[[2020-01-05|alias]]` are unwrapped, `2020-1-5`
    is accepted, and a time after the date is ignored. Checked by hand rather than
    with fromisoformat, whose accepted forms differ between 3.9 and 3.11."""
    v = value.strip()
    if v.startswith("[[") and v.endswith("]]"):
        v = v[2:-2].split("|", 1)[0].strip()
    m = _DAY.match(v)
    if not m:
        return None
    try:
        return datetime.date(*(int(x) for x in m.groups()))
    except ValueError:
        return None


def page_date(path, text, warn=None):
    """`updated:`, else `created:`, else the file's mtime. A missing, empty or
    unparseable value falls through to the next source; an unparseable one is
    passed to `warn(path, key)`."""
    for key in ("updated", "created"):
        value = _field(text, key)
        d = _day(value)
        if d:
            return d
        if value and warn:
            warn(path, key)
    return datetime.date.fromtimestamp(os.path.getmtime(path))


def stale_pages(pages, days, today=None, warn=None):
    """[(path, date, age_days)] for pages older than `days`, oldest first."""
    today = today or datetime.date.today()
    out = []
    for path, text in pages.items():
        d = page_date(path, text, warn)
        age = (today - d).days
        if age > days:
            out.append((path, d, age))
    out.sort(key=lambda r: (r[1], r[0]))
    return out


def norm_name(s):
    """Names compare equal when they match after Unicode composition and case
    folding and with everything but letters and digits removed."""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFC", s).casefold())


def duplicate_groups(pages):
    """[(kind, key, [paths])]. One table holds every page's file name, `title:`
    and aliases under the normalised name; two or more pages on one key is a
    group. The kind is 'title' if two or more pages are in it by file name or
    `title:`, else 'alias'."""
    table = {}
    for path in sorted(pages):
        text = pages[path]
        stem = os.path.splitext(os.path.basename(path))[0]
        names = [(stem, "title"), (_field(text, "title"), "title")]
        names += [(a, "alias") for a in aliases_of(text)]
        for name, kind in names:
            k = norm_name(name)
            if k:
                table.setdefault(k, {}).setdefault(path, set()).add(kind)
    out = []
    for k in sorted(table):
        if len(table[k]) > 1:
            by_name = sum("title" in kinds for kinds in table[k].values())
            out.append(("title" if by_name > 1 else "alias", k, sorted(table[k])))
    return out


def link_graph(vault, pages):
    """(outbound, inbound, broken): sets of page paths per page, and a list of
    (page, target) for links that resolve to nothing. Self links are ignored."""
    by_path = {rel_key(vault, p): p for p in pages}
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
    return outbound, inbound, broken


def find_orphans(pages, inbound):
    return [p for p in pages if not inbound[p] and not p.endswith(("index.md", "log.md", "README.md"))]


def find_stubs(pages):
    return [p for p, t in pages.items() if len(t.split()) < STUB_WORDS]


def emit(lines):
    """Print lines; if the reader went away (head, a closed pager) stop quietly:
    EPIPE, or EINVAL on Windows."""
    try:
        for line in lines:
            print(line)
        sys.stdout.flush()
    except OSError as e:
        if e.errno not in (errno.EPIPE, errno.EINVAL):
            raise
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except (OSError, ValueError):
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include", default="", metavar="DIRS",
                    help="comma-separated folders to count anyway, e.g. archive,journal")
    ap.add_argument("--stale", type=int, metavar="DAYS",
                    help="list pages not updated for more than DAYS days")
    ap.add_argument("--duplicates", action="store_true",
                    help="list pages with matching titles or shared aliases")
    args = ap.parse_args()
    SKIP_DIRS.difference_update(x.strip() for x in args.include.split(","))

    if not os.path.isdir(args.vault):
        sys.exit(f"not a directory: {args.vault}")

    pages = collect(args.vault)
    if args.stale is not None or args.duplicates:
        rel = lambda p: os.path.relpath(p, args.vault).replace(os.sep, "/")
        warn = lambda p, k: print(f"unparseable {k}: {rel(p)}", file=sys.stderr)
        stale = dup = None
        if args.stale is not None:
            stale = stale_pages(pages, args.stale, warn=warn)
        if args.duplicates:
            dup = duplicate_groups(pages)
        lines = []
        if args.json:
            doc = {}
            if stale is not None:
                doc["stale"] = [{"page": rel(p), "date": d.isoformat(), "age_days": a}
                                for p, d, a in stale]
            if dup is not None:
                doc["duplicates"] = [{"kind": k, "key": key, "pages": [rel(p) for p in ps]}
                                     for k, key, ps in dup]
            lines.append(json.dumps(doc, indent=2))
        else:
            for p, d, a in stale or []:
                lines.append(f"{rel(p)}\t{d.isoformat()}\t{a}")
            for k, key, ps in dup or []:
                lines.append("\t".join([k, key] + [rel(p) for p in ps]))
        emit(lines)
        return

    outbound, inbound, broken = link_graph(args.vault, pages)
    orphans = find_orphans(pages, inbound)
    stubs = find_stubs(pages)
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
