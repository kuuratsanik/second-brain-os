#!/usr/bin/env python3
"""Generate sitemap.xml, robots.txt and 404.html for GitHub Pages.

All three come from the constants in tools/site_common.py, so a rerun is
byte-identical and CI's drift check covers them.

    python3 scripts/build_static.py
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from site_common import SITE_URL, FOOTER, NAV_PAGES, head, header, min_css

CSS = """
:root{--paper:#EAEEE9;--card:#F7F9F6;--ink:#15201B;--soft:#4B5A52;--faint:#5C6A62;
  --rule:#D2DACF;--accent:#1F6B52}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font:17px/1.62 Charter,Georgia,serif;
  min-height:100vh;display:flex;flex-direction:column}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}
header{background:var(--card);border-bottom:1px solid var(--rule)}
.bar{max-width:1500px;margin:0 auto;padding:13px 22px;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.brand{font:600 15px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink)}
.brand span{color:var(--accent)}
nav{display:flex;gap:18px;font-size:14.5px}
nav a{color:var(--soft)}nav a.on{color:var(--ink);font-weight:600}
main{flex:1;max-width:68ch;width:100%;margin:0 auto;padding:64px 22px 90px}
.code{font:600 13px/1 ui-monospace,Menlo,monospace;color:var(--faint);letter-spacing:.08em}
h1{font:600 clamp(32px,4.6vw,48px)/1.08 Charter,Georgia,serif;letter-spacing:-.025em;margin:12px 0 14px}
p{color:var(--soft);margin-bottom:14px}
.go{display:inline-block;margin-top:10px;font:600 14px/1 ui-monospace,Menlo,monospace;
  background:var(--accent);color:#F7F9F6;border-radius:3px;padding:11px 16px}
.go:hover{text-decoration:none;background:#17503D}
footer{border-top:1px solid var(--rule);padding:22px;text-align:center;
  font:12px ui-monospace,Menlo,monospace;color:var(--faint)}
"""

PAGES = [page for _, page, _ in NAV_PAGES]


def sitemap():
    urls = "".join(
        f"  <url><loc>{SITE_URL}{'' if p == 'index.html' else p}</loc></url>\n"
        for p in PAGES)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + urls + "</urlset>\n")


def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n"


def not_found():
    # GitHub Pages serves this from any path depth, so every link is absolute.
    return (head("Page not found - Second Brain OS",
                 "That page does not exist. The Second Brain OS guide is one click away.",
                 "404.html", min_css(CSS), base=SITE_URL, robots="noindex")
            + "\n" + header("", base=SITE_URL)
            + '\n<main id="main" tabindex="-1">\n  <div class="code">404</div>\n'
              '  <h1>That page is not here</h1>\n'
              '  <p>The link may be old, or the address mistyped. Every page of the '
              'guide, the course and the handbooks lives behind the front page.</p>\n'
              f'  <a class="go" href="{SITE_URL}">Back to the guide</a>\n</main>\n'
            + FOOTER + "\n</body></html>\n")


def write(name, text):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    write("sitemap.xml", sitemap())
    write("robots.txt", robots())
    write("404.html", not_found())
    print("sitemap.xml, robots.txt, 404.html written")
