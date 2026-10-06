#!/usr/bin/env python3
"""Write one self-contained HTML dashboard for a second-brain vault.

Usage:
    python3 dashboard.py /path/to/vault [--out output/dashboard.html] [--stale-days 90]
    python3 dashboard.py /path/to/vault --json

Shows page, link, broken-link, orphan and stub counts, stale pages, duplicate
groups, the idea-to-adopted lifecycle funnel, pages per top-level folder, the
10 most linked pages and the length of the needs-owner queue. The file has no
external scripts, styles or fonts, uses inline SVG, follows the light or dark
setting of the browser, and is byte-for-byte the same for the same vault and
date.

Pages with `sensitivity: restricted` count in the numbers but only their paths
appear; no title, link target or body text from them is written.

`--out` is relative to the vault unless it is absolute. `--json` prints the
data behind the page and writes no file. `--today YYYY-MM-DD` fixes the date
used for staleness. Uses link_check.py and vault_search.py from this folder.

No dependencies. Reads only, except for the output file. Exit codes: 0, 1 for a
bad vault path, 2 for a usage error.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import link_check as lc  # noqa: E402
from vault_search import sensitivity_of  # noqa: E402

TOP_LINKED = 10
NEEDS_OWNER = "wiki/systems/needs-owner.md"

# The lifecycle stages and the `status:` values that put an idea or experiment
# page in each (skills/second-brain-lifecycle/SKILL.md: there is no `plan`
# status, a plan is an experiment that is `planned`; a review is an experiment
# that is `reviewing`, counted with the experiments in flight). A literal
# `status: idea|plan|experiment` on any page also counts. `promoted` ideas are
# done as ideas and live on as a planned experiment, so they are listed apart.
FUNNEL = [
    ("idea", ("new", "considering", "idea")),
    ("plan", ("planned", "plan")),
    ("experiment", ("active", "reviewing", "experiment")),
    ("adopted", ("adopted",)),
    ("dropped", ("dropped",)),
]
LIFECYCLE_TYPES = ("idea", "experiment")


def rel(vault, path):
    return os.path.relpath(path, vault).replace(os.sep, "/")


def lifecycle(pages):
    """Counts per funnel stage, plus `promoted` and the statuses nothing maps to."""
    stage_of = {s: name for name, statuses in FUNNEL for s in statuses}
    counts = {name: 0 for name, _ in FUNNEL}
    other = {}
    for text in pages.values():
        status = lc._field(text, "status").strip().lower()
        kind = lc._field(text, "type").strip().lower()
        if not status:
            continue
        literal = status in ("idea", "plan", "experiment")
        if kind not in LIFECYCLE_TYPES and not literal:
            continue
        if status in stage_of:
            counts[stage_of[status]] += 1
        elif kind in LIFECYCLE_TYPES:
            other[status] = other.get(status, 0) + 1
    return {"stages": counts, "promoted": other.pop("promoted", 0),
            "other": dict(sorted(other.items()))}


def needs_owner_open(vault):
    """Open items in the needs-owner page: top-level list items that are not
    ticked and sit under a heading other than Done, Resolved or Closed. None if
    the page does not exist."""
    path = os.path.join(vault, *NEEDS_OWNER.split("/"))
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.match(r"---\n.*?\n---\n", text, re.S)
    if m:
        text = text[m.end():]
    closed, fence, n = False, False, 0
    for line in text.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        elif fence:
            continue
        elif re.match(r"#{1,6}[ \t]", line):
            closed = bool(re.match(r"#{1,6}[ \t]+(done|resolved|closed|completed)\b", line, re.I))
        elif (not closed and re.match(r"(?:[-*+]|\d+[.)])[ \t]+\S", line)
              and not re.match(r"[-*+][ \t]+\[[xX]\]", line)):
            n += 1
    return n


def gather(vault, stale_days=90, today=None):
    pages = lc.collect(vault)
    outbound, inbound, broken = lc.link_graph(vault, pages)
    orphans = lc.find_orphans(pages, inbound)
    stubs = lc.find_stubs(pages)
    restricted = {p for p, t in pages.items() if sensitivity_of(t) == "restricted"}
    links = sum(len(v) for v in outbound.values())

    folders = {}
    for p in pages:
        r = rel(vault, p)
        top = r.split("/", 1)[0] if "/" in r else "(root)"
        folders[top] = folders.get(top, 0) + 1

    stale = [{"page": rel(vault, p), "date": d.isoformat(), "age_days": a}
             for p, d, a in lc.stale_pages(pages, stale_days, today=today)]

    dups = []
    for kind, key, group in lc.duplicate_groups(pages):
        secret = any(p in restricted for p in group)
        dups.append({"kind": kind, "name": "(restricted)" if secret else key,
                     "pages": [rel(vault, p) for p in group]})

    linked = sorted(((len(v), rel(vault, p)) for p, v in inbound.items() if v),
                    key=lambda r: (-r[0], r[1]))[:TOP_LINKED]

    return {
        "vault": os.path.basename(os.path.abspath(vault)),
        "as_of": (today or datetime.date.today()).isoformat(),
        "stale_days": stale_days,
        "counts": {"pages": len(pages), "links": links,
                   "avg_links_per_page": round(links / len(pages), 2) if pages else 0,
                   "broken": len(broken), "orphans": len(orphans), "stubs": len(stubs),
                   "restricted": len(restricted)},
        "broken": [{"page": rel(vault, p), "target": None if p in restricted else t}
                   for p, t in sorted(broken, key=lambda b: (rel(vault, b[0]), b[1]))],
        "orphans": sorted(rel(vault, p) for p in orphans),
        "stubs": sorted(rel(vault, p) for p in stubs),
        "stale": stale,
        "duplicates": dups,
        "lifecycle": lifecycle(pages),
        "folders": [{"folder": k, "pages": v} for k, v in sorted(folders.items(), key=lambda kv: (-kv[1], kv[0]))],
        "most_linked": [{"page": p, "inbound": n} for n, p in linked],
        "needs_owner_open": needs_owner_open(vault),
    }


# ---------------------------------------------------------------- HTML

CSS = """
:root{color-scheme:light dark;--bg:#fbfaf7;--fg:#1f2328;--muted:#59606a;--card:#fff;--line:#d8d4ca;
--bar:#2a6f97;--bar2:#9a5b13;--warn:#9a3412;--focus:#0b57d0}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#e6e6e3;--muted:#a3a9b1;--card:#1c1f25;
--line:#363b44;--bar:#6fb3dd;--bar2:#e0a35c;--warn:#f0a070;--focus:#8ab4f8}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:inherit}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:var(--card);padding:8px;z-index:2}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
header,main{max-width:64rem;margin:0 auto;padding:0 16px}
header{padding-top:24px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:0 0 12px}
.sub{color:var(--muted);margin:0}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:16px 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:12px;margin:16px 0;padding:0;list-style:none}
.tiles li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.tiles b{display:block;font-size:1.7rem;line-height:1.2}.tiles span{color:var(--muted);font-size:.9rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:0 16px}
.bars{list-style:none;margin:0;padding:0}
.bars li{display:grid;grid-template-columns:minmax(0,1fr) 3rem;gap:2px 8px;margin:0 0 10px}
.bars .l{overflow-wrap:anywhere}.bars .n{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.bars svg{grid-column:1/3;width:100%;height:10px;display:block}
.bars rect.t{fill:var(--line)}.bars rect.v{fill:var(--bar)}.bars .alt rect.v{fill:var(--bar2)}
table{width:100%;border-collapse:collapse;font-size:.92rem}
th,td{text-align:left;padding:4px 8px 4px 0;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
th{color:var(--muted);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}
.empty{color:var(--muted);margin:0}.warn{color:var(--warn);font-weight:600}
code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.9em}
footer{max-width:64rem;margin:0 auto;padding:0 16px 32px;color:var(--muted);font-size:.9rem}
"""


def e(x):
    return html.escape(str(x), quote=True)


def bars(rows, total=None, alt=False):
    """A list of label, count and an inline SVG bar. The numbers are text, so the
    bar is decoration."""
    if not rows:
        return '<p class="empty">None.</p>'
    top = total or max(n for _, n in rows) or 1
    out = ['<ul class="bars">']
    cls = ' class="alt"' if alt else ""
    for label, n in rows:
        w = 100.0 * n / top
        out.append(
            f'<li{cls}><span class="l">{e(label)}</span><span class="n">{n}</span>'
            f'<svg viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            f'<rect class="t" width="100" height="10" rx="2"/><rect class="v" width="{w:.2f}" height="10" rx="2"/></svg></li>')
    out.append("</ul>")
    return "".join(out)


def table(head, rows, num=()):
    if not rows:
        return '<p class="empty">None.</p>'
    th = "".join(f'<th scope="col">{e(h)}</th>' for h in head)
    body = "".join(
        "<tr>" + "".join(('<td class="num">' if i in num else "<td>") + f"{c}</td>"
                         for i, c in enumerate(r)) + "</tr>"
        for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def render(d):
    c = d["counts"]
    lc_ = d["lifecycle"]
    tiles = [("Pages", c["pages"], ""), ("Links", c["links"], f'{c["avg_links_per_page"]} per page'),
             ("Broken links", c["broken"], ""), ("Orphans", c["orphans"], ""),
             ("Stubs", c["stubs"], f"under {lc.STUB_WORDS} words"),
             ("Stale", len(d["stale"]), f'over {d["stale_days"]} days'),
             ("Duplicate groups", len(d["duplicates"]), "")]
    q = d["needs_owner_open"]
    tiles.append(("Needs owner", "n/a" if q is None else q, "open items" if q is not None else "no queue page"))
    tile_html = "".join(f"<li><b>{e(v)}</b><span>{e(k)}" + (f", {e(s)}" if s else "") + "</span></li>"
                        for k, v, s in tiles)

    funnel = bars([(name, lc_["stages"][name]) for name, _ in FUNNEL])
    funnel_note = []
    if lc_["promoted"]:
        funnel_note.append(f'{lc_["promoted"]} promoted idea(s) are not counted; their experiment is.')
    if lc_["other"]:
        funnel_note.append("Other statuses: " + ", ".join(f"{k} {v}" for k, v in lc_["other"].items()) + ".")
    funnel += "".join(f'<p class="sub">{e(n)}</p>' for n in funnel_note)

    broken = table(["Page", "Link target"], [[f"<code>{e(b['page'])}</code>",
                                              "restricted page, target not shown" if b["target"] is None
                                              else f"<code>[[{e(b['target'])}]]</code>"] for b in d["broken"][:100]])
    paths = lambda xs: table(["Page"], [[f"<code>{e(p)}</code>"] for p in xs[:100]])
    stale = table(["Page", "Last updated", "Days"],
                  [[f"<code>{e(s['page'])}</code>", e(s["date"]), s["age_days"]] for s in d["stale"][:100]], num=(2,))
    dups = table(["Kind", "Name", "Pages"],
                 [[e(g["kind"]), e(g["name"]), "<br>".join(f"<code>{e(p)}</code>" for p in g["pages"])]
                  for g in d["duplicates"][:100]])
    linked = table(["Page", "Linked from"], [[f"<code>{e(m['page'])}</code>", m["inbound"]] for m in d["most_linked"]], num=(1,))

    def sec(title, body, note=""):
        h = title.lower().replace(" ", "-")
        return f'<section aria-labelledby="{h}"><h2 id="{h}">{e(title)}</h2>{body}{note}</section>'

    cut = lambda n: f'<p class="sub">Showing 100 of {n}.</p>' if n > 100 else ""
    parts = [
        sec("Lifecycle funnel", funnel),
        '<div class="grid">' + sec("Pages per folder", bars([(f["folder"], f["pages"]) for f in d["folders"]], alt=True)) +
        sec("Most linked pages", linked) + "</div>",
        sec("Broken links", broken, cut(len(d["broken"]))),
        sec("Orphans", paths(d["orphans"]), cut(len(d["orphans"]))),
        sec("Stubs", paths(d["stubs"]), cut(len(d["stubs"]))),
        sec(f'Stale pages, not updated for over {d["stale_days"]} days', stale, cut(len(d["stale"]))),
        sec("Duplicate groups", dups, cut(len(d["duplicates"]))),
    ]
    note = f' {c["restricted"]} restricted page(s) are counted, and shown by path only.' if c["restricted"] else ""
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        f'<title>Vault dashboard: {e(d["vault"])}</title>\n<style>{CSS}</style>\n</head>\n<body>\n'
        '<a class="skip" href="#main">Skip to content</a>\n'
        f'<header><h1>Vault dashboard: {e(d["vault"])}</h1>'
        f'<p class="sub">As of {e(d["as_of"])}. Generated by scripts/dashboard.py.{e(note)}</p></header>\n'
        f'<main id="main"><ul class="tiles" aria-label="Summary">{tile_html}</ul>\n'
        + "\n".join(parts) +
        '\n</main>\n<footer>Counts follow scripts/link_check.py: archive, journal, raw, templates and output '
        'folders are not counted.</footer>\n</body>\n</html>\n')


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("vault")
    ap.add_argument("--out", default=os.path.join("output", "dashboard.html"),
                    help="output file, relative to the vault (default output/dashboard.html)")
    ap.add_argument("--stale-days", type=int, default=90, metavar="DAYS")
    ap.add_argument("--json", action="store_true", help="print the data as JSON and write no file")
    ap.add_argument("--today", metavar="YYYY-MM-DD", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.stale_days < 0:
        ap.error("--stale-days must not be negative")
    today = None
    if args.today:
        today = lc._day(args.today)
        if not today:
            ap.error("--today must be YYYY-MM-DD")
    if not os.path.isdir(args.vault):
        sys.stderr.write(f"not a directory: {args.vault}\n")
        return 1

    data = gather(args.vault, args.stale_days, today)
    if args.json:
        lc.emit([json.dumps(data, indent=2, ensure_ascii=False)])
        return 0
    out = args.out if os.path.isabs(args.out) else os.path.join(args.vault, args.out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(data))
    lc.emit([f"wrote {out}"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
