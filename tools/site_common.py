"""Shared constants and helpers for the site generators.

Imported by tools/build_site.py, scripts/build_tracks.py and
scripts/build_tree.py, so the fork URL, the favicon, the header and the
footer exist in exactly one place.
"""
import html as _html, json, re

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


LIGHT = {"paper": "#EAEEE9", "card": "#F7F9F6", "ink": "#15201B", "soft": "#4B5A52",
         "faint": "#5C6A62", "rule": "#D2DACF", "accent": "#1F6B52",
         "accent-bg": "#E1EDE5", "num": "#7A5E1C", "on-accent": "#F7F9F6",
         "accent-hover": "#17503D", "hdr": "rgba(234,238,233,.94)", "fig": "#F7F9F6"}
DARK = {"paper": "#0F1613", "card": "#17211C", "ink": "#E6ECE8", "soft": "#B3BFB8",
        "faint": "#9AA8A0", "rule": "#2E3C35", "accent": "#5FBF9A",
        "accent-bg": "#1F3A2F", "num": "#D9B25A", "on-accent": "#0F1613",
        "accent-hover": "#86D4B5", "hdr": "rgba(15,22,19,.94)", "fig": "#F7F9F6"}


def _vars(d):
    return ";".join(f"--{k}:{v}" for k, v in d.items())


# Palette, dark override and the rules every page shares. The dark palette is
# written twice from one dict: for the OS preference (unless the visitor chose
# light) and for an explicit choice.
THEME_CSS = (
    f":root{{color-scheme:light dark;{_vars(LIGHT)}}}\n"
    f":root[data-theme=light]{{color-scheme:light}}\n"
    f":root[data-theme=dark]{{color-scheme:dark;{_vars(DARK)}}}\n"
    f"@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{{_vars(DARK)}}}}}\n")

SHARED_CSS = THEME_CSS + """
body{background:var(--paper)}
.skip{position:absolute;left:12px;top:-60px;z-index:100;background:var(--card);color:var(--ink);
  border:2px solid var(--accent);border-radius:3px;padding:9px 14px;font:600 14px/1 ui-monospace,Menlo,monospace}
.skip:focus{top:10px;text-decoration:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
main:focus{outline:none}
.theme{margin-left:auto;font:12.5px/1 ui-monospace,Menlo,monospace;color:var(--soft);
  background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:7px 10px;cursor:pointer}
.theme[hidden]{display:none}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.theme:hover{border-color:var(--accent);color:var(--ink)}
.search~.theme{margin-left:0}
img[src$=".svg"]{background:var(--fig);border-radius:4px}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]) img[src$=".svg"]{padding:10px}}
:root[data-theme=dark] img[src$=".svg"]{padding:10px}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}*{transition:none!important;animation:none!important}}
"""

# Runs in <head>, before first paint. Storage may be blocked: every access is guarded.
# The key is namespaced because GitHub Pages shares one origin across the owner's
# project sites; the old bare "theme" key is still read once so choices survive.
THEME_INIT = ("<script>try{var t=localStorage.getItem('sbo-theme')||localStorage.getItem('theme');"
              "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}</script>")

# Sits right after the toggle button. It is a two-state light/dark toggle, so every
# click changes the page. With nothing stored the page follows the OS ("system");
# the first click picks the opposite of what the OS shows. Picking the theme the
# OS already shows clears the stored choice, which is the way back to system.
# The button ships hidden so it is never an empty control without JavaScript. The
# visually hidden role=status span announces each change, and the button name
# carries the state. The script also points theme-color at the shown theme.
THEME_BUTTON = (
    '<button class="theme" id="theme" type="button" hidden></button>'
    '<span class="sr" id="theme-say" role="status" aria-live="polite"></span>\n'
    '<script>(function(){var b=document.getElementById("theme"),s=document.getElementById("theme-say"),'
    'r=document.documentElement,q=window.matchMedia?matchMedia("(prefers-color-scheme: dark)"):{},'
    f'C={{light:"{LIGHT["paper"]}",dark:"{DARK["paper"]}"}},'
    'M=document.querySelectorAll("meta[name=theme-color]");'
    'function e(){var t=r.dataset.theme;return t==="light"||t==="dark"?t:""}'
    'function g(){return e()||(q.matches?"dark":"light")}'
    'function l(){var t=g();return e()?t:t+" (system)"}'
    'function u(){var t=g(),n=t==="dark"?"light":"dark";b.textContent="Theme: "+l();'
    'b.setAttribute("aria-label","Theme: "+l()+". Switch to "+n);'
    'for(var i=0;i<M.length;i++)M[i].content=C[e()?t:(/dark/.test(M[i].media||"")?"dark":"light")]}'
    'b.hidden=false;'
    'b.onclick=function(){var n=g()==="dark"?"light":"dark",y=n===(q.matches?"dark":"light");'
    'if(y)delete r.dataset.theme;else r.dataset.theme=n;'
    'try{localStorage.removeItem("theme");if(y)localStorage.removeItem("sbo-theme");'
    'else localStorage.setItem("sbo-theme",n)}catch(x){}u();s.textContent="Theme set to "+l()};'
    'if(q.addEventListener)q.addEventListener("change",u);'
    'u()})()</script>')

THEME_COLOR = LIGHT["paper"]
THEME_COLOR_DARK = DARK["paper"]
SITE_NAME = "Second Brain OS"


def head(title, description, page, css, robots=""):
    """Everything from the doctype through the opening <body> and skip link.

    `robots` adds a robots meta tag (the 404 page passes "noindex").
    """
    url = SITE_URL + ("" if page == "index.html" else page)
    t, d, u = (_html.escape(x, quote=True) for x in (title, description, url))
    meta = [
        f'<meta name="description" content="{d}">',
        f'<meta name="theme-color" media="(prefers-color-scheme: light)" content="{THEME_COLOR}">',
        f'<meta name="theme-color" media="(prefers-color-scheme: dark)" content="{THEME_COLOR_DARK}">',
        '<meta name="color-scheme" content="light dark">',
        f'<link rel="canonical" href="{u}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{u}">',
        '<meta property="og:locale" content="en_US">',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{t}">',
        f'<meta name="twitter:description" content="{d}">',
    ]
    if robots:
        meta.append(f'<meta name="robots" content="{robots}">')
    return (f'<!DOCTYPE html><html lang="en"><head>\n'
            f'<meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1">\n'
            f'{FAVICON}<title>{t}</title>\n{THEME_INIT}\n' + "\n".join(meta) + "\n"
            f'<style>{css}{min_css(SHARED_CSS)}</style>\n</head><body>\n'
            f'<a class="skip" href="#main">Skip to content</a>')


def header(active, extra="", base=""):
    on = ' class="on" aria-current="page"'
    links = "\n".join(
        f'    <a href="{base}{href}"{on if key == active else ""}>{label}</a>'
        for key, href, label in NAV_PAGES)
    return (f'<header><div class="bar">\n'
            f'  <a class="brand" href="{base}index.html">[[ second<span>brain</span>os ]]</a>\n'
            f'  <nav aria-label="Site">\n{links}\n    <a href="{REPO}">Repo</a>\n  </nav>\n'
            f'{extra}{THEME_BUTTON}</div></header>')


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
