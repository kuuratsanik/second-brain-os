#!/usr/bin/env python3
"""Inject the compact topic tracks into index.html.

The site is a single self-contained page: every guide page lives in an
embedded JSON blob that the tiny SPA renders. This script reads the track
markdown from docs/track-*/, renders it the same way the main guide was
rendered, and rewrites three things in place:

  1. the JSON blob        - pages, sections (flagged track:true), order
  2. the hero blocks      - between <!--ENTRIES-->, <!--COURSE--> and
                            <!--TRACKS--> and their closing markers
  3. nothing else         - the SPA handles tracks generically

tools/build_site.py emits the empty marker pairs; this script must run
after it (scripts/build_all.py does). Re-running is safe: previous course
and track entries are replaced, not duplicated.

    pip install -r requirements.txt
    python3 scripts/build_tracks.py
"""
import glob, io, json, os, re, sys

import markdown

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from site_common import dumps, slim_page, word

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "index.html")

# the course: seven modules, three lessons each - theory, mechanics, practice.
# Built on Google's agent whitepapers and the five-layer frame.
COURSE = {
    "course-0-map": {
        "title": "0 · The map",
        "blurb": "What an agent is, the five layers around the model, and "
                 "when a workflow beats a loop.",
        "order": ["what-an-agent-is", "five-layers", "agents-or-workflows"],
    },
    "course-1-context": {
        "title": "1 · Context",
        "blurb": "What the model sees: attention, caching, the four places, "
                 "sessions and memory.",
        "order": ["how-models-read", "the-four-places", "context-practice"],
    },
    "course-2-loop": {
        "title": "2 · Loop",
        "blurb": "Who decides the next step: goal, checker, stop rule, "
                 "budget - and the hybrid that survives production.",
        "order": ["loops-vs-workflows", "the-four-parts", "loop-practice"],
    },
    "course-3-gate": {
        "title": "3 · The gate",
        "blurb": "Cheap decisions in front of expensive models: classifiers "
                 "first, System One models where they earn it.",
        "order": ["cheap-decisions", "gates-in-practice", "gate-practice"],
    },
    "course-4-harness": {
        "title": "4 · Harness",
        "blurb": "The office around the model: containment, guides, sensors, "
                 "permissions - built from the outside in.",
        "order": ["the-office", "the-four-rings", "harness-practice"],
    },
    "course-5-evals": {
        "title": "5 · Evals",
        "blurb": "The same test every month: behavioural checks on traces, "
                 "judged judges, golden sets that include failures.",
        "order": ["two-kinds-of-checks", "judges-and-golden-sets",
                  "evals-practice"],
    },
    "course-6-production": {
        "title": "6 · Production",
        "blurb": "From demo to deployed: gateways, tracing, cost, security - "
                 "and the day-one plan across all five layers.",
        "order": ["from-prototype", "operating-agents", "day-one-plan"],
    },
}

# page order inside each track is editorial, not alphabetical
TRACKS = {
    "track-graph": {
        "title": "Knowledge graphs",
        "blurb": "Graphs as agent memory: GraphRAG, extraction pipelines, "
                 "stores — then an evening build of a graph layer over "
                 "your own vault.",
        "order": ["why-graphs", "graphrag", "building-graphs-with-llms",
                  "graph-stores", "tools",
                  "build-extract", "build-query", "build-use", "resources"],
    },
    "track-jev": {
        "title": "Jev engineering",
        "module": ("3", "course-3-gate"),
        "blurb": "The gate is the layer; Jev is one way to build it. Typed "
                 "decisions with confidence scores instead of generated text "
                 "— and a build you can run before your Jev access lands.",
        "order": ["system-one-models", "what-jev-is-good-for",
                  "jev-in-an-agent-stack", "getting-started",
                  "build-decision-endpoint", "build-router",
                  "build-swap-in-jev", "resources"],
    },
    "track-harness": {
        "title": "Agent harnesses",
        "module": ("4", "course-4-harness"),
        "blurb": "The machinery around the model: loops, tools, context "
                 "engineering, the landscape — and a working harness in "
                 "an evening, about 150 lines.",
        "order": ["what-a-harness-is", "claude-code-as-harness",
                  "context-engineering", "tools-and-mcp",
                  "harness-landscape",
                  "build-the-loop", "build-guardrails", "build-graduate",
                  "resources"],
    },
    "track-loop": {
        "title": "Loop engineering",
        "module": ("2", "course-2-loop"),
        "blurb": "The control system around the agent: stop conditions, "
                 "critics, context hygiene — and an overnight loop you can "
                 "trust by morning.",
        "order": ["what-loop-engineering-is", "stop-conditions",
                  "critics-and-verification", "context-hygiene", "patterns",
                  "build-goal-test", "build-critic", "build-overnight",
                  "resources"],
    },
    "track-evals": {
        "title": "Eval engineering",
        "module": ("5", "course-5-evals"),
        "blurb": "Measurement as the discipline of AI products: golden sets, "
                 "judges that do not lie, agent trajectories — and your "
                 "first suite built in an afternoon.",
        "order": ["why-evals", "designing-evals", "llm-as-judge",
                  "agent-evals", "tooling",
                  "build-traces", "build-suite", "build-ci", "resources"],
    },
}

MD = markdown.Markdown(extensions=["fenced_code", "tables"])


def render_page(sec, fname):
    meta = COURSE.get(sec) or TRACKS[sec]
    path = os.path.join(ROOT, "docs", sec, fname + ".md")
    src = io.open(path, encoding="utf-8").read().strip()
    lines = src.split("\n")
    if not lines[0].startswith("# "):
        raise SystemExit(f"{path}: first line must be an H1 title")
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:]).strip()
    MD.reset()
    html = MD.convert(body)
    # relative images resolve against the repo, wherever the page renders
    html = re.sub(r'(<img[^>]+src=")(?!https?:|/|docs/)',
                  lambda m: m.group(1) + f"docs/{sec}/", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    headings = re.findall(r"<h2[^>]*>(.*?)</h2>", html)
    links = []
    for href, label in re.findall(r'href="([^"]+\.md)"[^>]*>(.*?)</a>', html):
        to = sec + "/" + href.replace("./", "").replace(".md", "")
        links.append({"to": to, "label": re.sub(r"<[^>]+>", "", label)})
    return {
        "id": f"{sec}/{fname}",
        "path": f"docs/{sec}/{fname}.md",
        "section": sec,
        "section_title": meta["title"],
        "title": title,
        "html": html,
        "headings": headings,
        "words": len(text.split()),
        "text": text[:4000],
        "links": links,
    }


def main():
    s = io.open(INDEX, encoding="utf-8").read()
    i = s.find('application/json">') + len('application/json">')
    j = s.find("</script>", i)
    D = json.loads(s[i:j])

    # replace any previous course and track entries
    gone = lambda k: k.startswith("track-") or k.startswith("course-")
    D["pages"] = [p for p in D["pages"] if not gone(p["id"].split("/")[0])]
    D["sections"] = {k: v for k, v in D["sections"].items() if not gone(k)}
    D["order"] = {k: v for k, v in D["order"].items() if not gone(k)}

    course_cards = build_group(D, COURSE, "course")
    cards = build_group(D, TRACKS, "track")

    s = s[:i] + dumps(D) + s[j:]

    course_block = ('<!--COURSE--><div class="trkhead"><h2>the agents course</h2>'
                    f'<p>{word(len(COURSE), True)} modules from a single prompt to a production '
                    'agent: theory from the whitepapers, a build in every '
                    'module. A path — start at the map, read in order, '
                    'finish with the day-one plan.'
                    '</p></div><div class="seclist courselist">'
                    + "".join(course_cards) + "</div><!--/COURSE-->")
    track_block = ('<!--TRACKS--><div class="trkhead"><h2>handbooks</h2>'
                   '<p>Not a path — references. The full menu of techniques, '
                   'tools and builds for one layer of the course; open one '
                   'when that layer starts hurting, dip in anywhere.</p></div>'
                   '<div class="seclist tracklist">' + "".join(cards)
                   + "</div><!--/TRACKS-->")
    guide_pages = sum(len(v) for k, v in D["order"].items() if not gone(k))
    n_course = sum(len(v) for k, v in D["order"].items() if k.startswith("course-"))
    n_track = sum(len(v) for k, v in D["order"].items() if k.startswith("track-"))
    n_skills = len(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")))
    n_tracks = sum(1 for k in D["order"] if k.startswith("track-"))
    n_guide_secs = sum(1 for k in D["order"] if not gone(k))
    n_course_secs = sum(1 for k in D["order"] if k.startswith("course-"))
    first = lambda pre: next(v[0] for k, v in D["order"].items() if k.startswith(pre))
    entries_block = (
        '<!--ENTRIES--><div class="entr">'
        f'<a class="ent e1" href="#{first("01-")}"><span class="ek">the guide &middot; 01&ndash;{n_guide_secs:02d}</span>'
        '<h2>The second brain</h2><p>A path you follow once: a knowledge base an agent builds and maintains for you, in markdown you own.</p>'
        f'<span class="em">{guide_pages} pages &middot; starter vault &middot; {n_skills} skills</span></a>'
        f'<a class="ent e2" href="#{first("course-")}"><span class="ek">the agents course &middot; C0&ndash;C{n_course_secs - 1}</span>'
        f'<h2>The agents course</h2><p>A path you read in order: {word(n_course_secs)} modules from a single prompt to a production agent, practice in every module.</p>'
        f'<span class="em">{n_course} lessons &middot; plugin: tools in two commands</span></a>'
        f'<a class="ent e3" href="#{first("track-")}"><span class="ek">handbooks &middot; T1&ndash;T{n_tracks}</span>'
        '<h2>The handbooks</h2><p>Not a path &mdash; references: the full menu of techniques, tools and builds for one layer, when it starts hurting.</p>'
        f'<span class="em">{n_tracks} handbooks &middot; {n_track} pages &middot; dip in anywhere</span></a>'
        '</div><!--/ENTRIES-->')
    for marker, block in (("ENTRIES", entries_block), ("COURSE", course_block), ("TRACKS", track_block)):
        pat = f"<!--{marker}-->.*?<!--/{marker}-->"
        if re.search(pat, s, re.S):
            s = re.sub(pat, lambda m: block, s, flags=re.S)
        else:
            raise SystemExit(f"no <!--{marker}--> marker in index.html")
    io.open(INDEX, "w", encoding="utf-8", newline="\n").write(s)
    print("index.html rewritten")


def build_group(D, group, kind):
    cards = []
    for sec, meta in group.items():
        missing = [f for f in meta["order"]
                   if not os.path.exists(os.path.join(ROOT, "docs", sec, f + ".md"))]
        if missing:
            print(f"skip {sec}: missing {', '.join(missing)}")
            continue
        pages = [render_page(sec, f) for f in meta["order"]]
        D["pages"].extend(slim_page(p) for p in pages)
        D["sections"][sec] = {"title": meta["title"], "blurb": meta["blurb"],
                              kind: True}
        D["order"][sec] = [p["id"] for p in pages]
        cards.append(
            f'<article><h3><a href="#{pages[0]["id"]}">{meta["title"]}</a></h3>'
            f'<p>{meta["blurb"]}</p>'
            f'<div class="pg">{len(pages)} pages</div></article>')
        # a browsable README per folder, kept in sync with the order
        toc = "\n".join(f"{n}. [{p['title']}]({os.path.basename(p['path'])})"
                        for n, p in enumerate(pages, 1))
        if kind == "course":
            label = ("A course module beside [the main guide](../../README.md)"
                     " — read it on the site or in order below.")
        elif meta.get("module"):
            n, mdir = meta["module"]
            label = (f"The handbook for [module {n}](../{mdir}/README.md) of "
                     "the agents course: the module teaches the idea once; "
                     "this holds the full menu — techniques, tools and "
                     "builds. Read it on the site or dip in below.")
        else:
            label = ("A handbook beside [the main guide](../../README.md) — "
                     "the full menu for one layer; dip in anywhere.")
        io.open(os.path.join(ROOT, "docs", sec, "README.md"), "w",
                encoding="utf-8", newline="\n").write(
            f"# {meta['title']}\n\n{meta['blurb']}\n\n{label}\n\n{toc}\n")
        print(f"{sec}: {len(pages)} pages, "
              f"{sum(p['words'] for p in pages)} words")
    return cards


if __name__ == "__main__":
    main()
