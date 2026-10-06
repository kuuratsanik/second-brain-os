#!/usr/bin/env python3
"""Generate llms.txt and llms-full.txt at the repository root.

Format: the llms.txt proposal, https://llmstxt.org. An H1 with the name, a
blockquote summary, optional prose, then H2 sections holding lists of
"- [name](url): notes". An "Optional" section marks links a reader may skip
when context is short.
Not re-checked: llmstxt.org was blocked from the build environment on
2026-10-06, so the format above is from the proposal as recalled, not
re-fetched. Re-read it if the proposal changes.

Page order and titles come from the JSON embedded in index.html, so this step
runs after scripts/build_tracks.py. The page sources are the markdown files
in docs/. Nothing here reads git or the clock; a rerun is byte-identical.

    python3 scripts/build_llms.py
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from site_common import REPO, SITE_URL, SITE_NAME, RAW, FEED_URL
# The links to llms-full.txt, llms.txt and the feed use raw.githubusercontent.com
# because the Pages site is a 404 until Pages is enabled. Switch them to SITE_URL
# (and FEED_URL in site_common) once Pages is on.
SUMMARY = ("A guide to building a knowledge base your AI agent maintains, in plain "
           "markdown you own, plus an agents course and handbooks.")


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def load_index():
    s = read("index.html")
    i = s.find('application/json">') + len('application/json">')
    return json.loads(s[i:s.find("</script>", i)])


def plain(t):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[`*_]", "", t)
    return " ".join(t.split())


def describe(md):
    """First prose paragraph after the H1, cut to whole sentences.

    A paragraph that ends in ":" or "?" (a FAQ question) introduces something that is not prose (a list
    or code), so the next prose paragraph is taken as well.
    """
    paras, para, fence = [], [], False
    for line in md.split("\n")[1:]:
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if not line.strip():
            if para:
                paras.append(plain(" ".join(para)))
                para = []
                if len(paras) == 2 or not paras[0].endswith((":", "?")):
                    break
            continue
        if line.startswith(("#", "|", ">", "- ", "* ", "<", "!", "1. ")) and not para:
            continue
        para.append(line.strip())
    if para and len(paras) < 2:
        paras.append(plain(" ".join(para)))
    text = paras[0] if paras else ""
    if text.endswith((":", "?")) and len(paras) > 1:
        text = text + " " + paras[1]
    # whole sentences until there is enough to say something (a short opener such
    # as "You screenshot the post." is not a description)
    got = ""
    for sent in re.findall(r".+?(?:[.!?](?=\s|$)|$)", text):
        got = (got + " " + sent.strip()).strip()
        if len(got) >= 60:
            break
    text = got or text
    if len(text) > 180:
        text = text[:180].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return text


def build():
    D = load_index()
    titles = {p["id"]: p["title"] for p in D["pages"]}
    secs = []
    for sec, ids in D["order"].items():
        pages = []
        for pid in ids:
            path = f"docs/{pid}.md"
            md = read(path).strip() + "\n"
            pages.append({"id": pid, "path": path, "title": titles[pid], "md": md,
                          "desc": describe(md)})
        meta = D["sections"][sec]
        kind = "Course" if meta.get("course") else "Handbook" if meta.get("track") else "Guide"
        secs.append({"id": sec, "title": f"{kind}: {meta['title']}", "pages": pages})
    n = sum(len(s["pages"]) for s in secs)

    intro = (f"{n} pages in {len(secs)} sections: the guide (numbered "
             "sections, read once in order), the agents course (modules C0 to C6) "
             "and the handbooks (references, dip in anywhere). Every link below is "
             "the raw markdown of one page. The same text, concatenated, is in "
             f"[llms-full.txt]({RAW}llms-full.txt).")
    out = [f"# {SITE_NAME}", "", f"> {SUMMARY}", "", intro, ""]
    for s in secs:
        out += [f"## {s['title']}", ""]
        out += [f"- [{p['title']}]({RAW}{p['path']}): {p['desc']}" for p in s["pages"]]
        out.append("")
    out += ["## Optional", "",
            f"- [Resources]({RAW}resources/README.md): vetted links: plugins, tools, repositories, papers, reading",
            f"- [Changelog]({RAW}CHANGELOG.md): user-facing changes to the kit, by version",
            f"- [Changelog feed]({FEED_URL}): the same entries as an Atom feed",
            f"- [Site]({SITE_URL}): the guide, course and handbooks as a searchable page",
            ""]
    llms = "\n".join(out)

    bar = "=" * 72
    full = [f"# {SITE_NAME}: full text", "", f"> {SUMMARY}", "",
            f"The markdown of all {n} pages, in reading order, each under a page "
            "header. Relative links inside a page point to files in the repository "
            f"({REPO}/tree/main/); the index is {RAW}llms.txt.", ""]
    k = 0
    for s in secs:
        for p in s["pages"]:
            k += 1
            full += [bar, f"PAGE {k} of {n}: {p['title']}",
                     f"Section: {s['title']}", f"Source: {RAW}{p['path']}", bar, "",
                     p["md"].rstrip("\n"), ""]
    return llms + "\n", "\n".join(full) + "\n"


if __name__ == "__main__":
    a, b = build()
    for name, text in (("llms.txt", a), ("llms-full.txt", b)):
        with io.open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print(f"llms.txt {len(a.encode())//1024} KB, llms-full.txt {len(b.encode())//1024} KB")
