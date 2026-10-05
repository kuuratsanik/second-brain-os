"""Shared constants and helpers for the site generators.

Imported by tools/build_site.py, scripts/build_tracks.py and
scripts/build_tree.py, so the fork URL, the favicon, the header and the
footer exist in exactly one place.
"""
import json, re

OWNER = "kuuratsanik"
REPO = f"https://github.com/{OWNER}/second-brain-os"
GH = REPO + "/blob/main/"
GHT = REPO + "/tree/main/"
SITE_URL = f"https://{OWNER}.github.io/second-brain-os/"
UPSTREAM = "https://github.com/undefined-ui/second-brain-os"
UPSTREAM_OWNER = "undefined-ui"

FAVICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' rx=\'7\' fill=\'%23F7F9F6\'/%3E%3Crect x=\'.5\' y=\'.5\' width=\'31\' height=\'31\' rx=\'6.5\' fill=\'none\' stroke=\'%23D2DACF\'/%3E%3Cpath d=\'M10 21 L16 11 L22 19 M16 11 L23 9\' stroke=\'%231F6B52\' stroke-width=\'1.6\' fill=\'none\'/%3E%3Ccircle cx=\'10\' cy=\'21\' r=\'3\' fill=\'%23F7F9F6\' stroke=\'%231F6B52\' stroke-width=\'1.6\'/%3E%3Ccircle cx=\'16\' cy=\'11\' r=\'3\' fill=\'%23F7F9F6\' stroke=\'%231F6B52\' stroke-width=\'1.6\'/%3E%3Ccircle cx=\'22\' cy=\'19\' r=\'3\' fill=\'%23F7F9F6\' stroke=\'%231F6B52\' stroke-width=\'1.6\'/%3E%3Ccircle cx=\'24\' cy=\'8\' r=\'2\' fill=\'%231F6B52\'/%3E%3C/svg%3E">')

FOOTER = ('<footer>Generated from the repository. '
          f'<a href="{REPO}">{OWNER}/second-brain-os</a> · maintained by '
          f'<a href="https://github.com/{OWNER}" rel="noopener">{OWNER}</a>'
          f' · based on <a href="{UPSTREAM}" rel="noopener">second-brain-os</a>'
          f' by <a href="https://github.com/{UPSTREAM_OWNER}" rel="noopener">'
          f'{UPSTREAM_OWNER}</a></footer>')

NAV_PAGES = [("guide", "index.html", "Guide"),
             ("res", "resources.html", "Resources"),
             ("tree", "tree.html", "Tree")]


def head(title, description, page, css):
    """Everything from the doctype to the closing </head>."""
    return (f'<!DOCTYPE html><html lang="en"><head>\n'
            f'<meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1">\n'
            f'{FAVICON}<title>{title}</title>\n'
            f'<meta name="description" content="{description}">\n'
            f'<link rel="canonical" href="{SITE_URL}{"" if page == "index.html" else page}">\n'
            f'<style>{css}</style>\n</head><body>')


def header(active, extra=""):
    on = ' class="on"'
    links = "\n".join(
        f'    <a href="{href}"{on if key == active else ""}>{label}</a>'
        for key, href, label in NAV_PAGES)
    return (f'<header><div class="bar">\n'
            f'  <a class="brand" href="index.html">[[ second<span>brain</span>os ]]</a>\n'
            f'  <nav>\n{links}\n    <a href="{REPO}">Repo</a>\n  </nav>\n'
            f'{extra}</div></header>')


def min_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r" ?([{};,]) ?", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    return css.replace(";}", "}").strip()


def min_js(js):
    """Strip indentation and blank lines only; comments and strings stay."""
    return "\n".join(l.strip() for l in js.split("\n") if l.strip())


def dumps(obj):
    """Compact JSON that is safe inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")
                      ).replace("</", "<\\/")


def slim_page(p):
    """The only fields the browser needs; the rest is derived from the id."""
    return {"id": p["id"], "title": p["title"], "html": p["html"]}


WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve"]


def word(n, cap=False):
    w = WORDS[n] if n < len(WORDS) else str(n)
    return w.capitalize() if cap else w
