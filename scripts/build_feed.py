#!/usr/bin/env python3
"""Generate feed.xml, an Atom feed (RFC 4287) of the CHANGELOG.md releases.

One entry per `## [version] - YYYY-MM-DD` heading. The dates are the ones
written in the headings, so the build reads neither git nor the clock. The
"Unreleased" heading has no date and is left out. Entry ids are tag URIs
(RFC 4151) built from the site host, the heading date and the version, so
they never change when the text is edited.

    python3 scripts/build_feed.py
"""
import io, os, re, sys
from xml.sax.saxutils import escape, quoteattr

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from site_common import OWNER, GH, GHT, SITE_NAME, FEED_URL

HOST = f"{OWNER}.github.io"
HEADING = re.compile(r"^## \[([^\]]+)\] - (\d{4}-\d{2}-\d{2})[ \t]*$", re.M)


def absolutize(html):
    """Relative hrefs in the changelog resolve against the repository root."""
    def fix(m):
        href = m.group(1)
        if re.match(r"([a-z][a-z0-9+.-]*:|//)", href, re.I):
            return m.group(0)
        if href.startswith("#"):
            return f'href="{GH}CHANGELOG.md{href}"'
        path = re.split(r"[#?]", href)[0]
        tree = path.endswith("/") or "." not in path.rsplit("/", 1)[-1]
        return f'href="{GHT if tree else GH}{href}"'
    return re.sub(r'href="([^"]*)"', fix, html)


def entries():
    with io.open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as fh:
        text = fh.read()
    marks = list(re.finditer(r"^## \[", text, re.M))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        block = text[m.start():end]
        h = HEADING.match(block)
        if not h:
            continue
        ver, date = h.groups()
        md = markdown.Markdown(extensions=["fenced_code", "tables"])
        out.append((ver, date, absolutize(md.convert(block[h.end():].strip()))))
    return out


def build():
    es = entries()
    if not es:
        raise SystemExit("CHANGELOG.md: no dated '## [version] - date' headings")
    updated = max(d for _, d, _ in es) + "T00:00:00Z"
    x = ['<?xml version="1.0" encoding="utf-8"?>',
         '<feed xmlns="http://www.w3.org/2005/Atom">',
         f"  <title>{escape(SITE_NAME)} changelog</title>",
         "  <subtitle>User-facing changes to the kit: skills, commands, agents, "
         "vault scripts, vault template, plugins and guide.</subtitle>",
         f"  <id>{FEED_URL}</id>",
         f"  <updated>{updated}</updated>",
         f'  <link rel="self" type="application/atom+xml" href={quoteattr(FEED_URL)}/>',
         f'  <link rel="alternate" type="text/html" href={quoteattr(GH + "CHANGELOG.md")}/>',
         f"  <author><name>{escape(OWNER)}</name><uri>https://github.com/{OWNER}</uri></author>"]
    for ver, date, html in es:
        slug = re.sub(r"[^a-z0-9 _-]", "", f"{ver} - {date}".lower()).replace(" ", "-")
        link = f"{GH}CHANGELOG.md#{slug}"
        x += ["  <entry>",
              f"    <title>{escape(SITE_NAME)} kit {escape(ver)}</title>",
              f"    <id>tag:{HOST},{date}:second-brain-os/{escape(ver)}</id>",
              f"    <updated>{date}T00:00:00Z</updated>",
              f'    <link rel="alternate" type="text/html" href={quoteattr(link)}/>',
              f'    <content type="html">{escape(html)}</content>',
              "  </entry>"]
    x.append("</feed>")
    return "\n".join(x) + "\n"


if __name__ == "__main__":
    text = build()
    with io.open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"feed.xml {len(text.encode())//1024} KB")
