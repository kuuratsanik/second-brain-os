# tools

The site at [undefined-ui.github.io/second-brain-os](https://undefined-ui.github.io/second-brain-os/)
is generated from this repository, so it cannot drift from the guide.

```bash
pip install -r requirements.txt
python3 scripts/build_all.py
```

`scripts/build_all.py` is the single entry point. It runs four steps in order,
each reading the previous one's output, and produces `index.html`,
`resources.html` and `tree.html`. Running it twice gives identical bytes, and CI
rebuilds on every push and fails if the committed HTML is stale.

1. `tools/extract_site.py` - docs and resources to `site_data.json` (ignored by git).
2. `tools/build_site.py` - `index.html` (the ten-section guide) and `resources.html`.
   It leaves empty `<!--ENTRIES-->`, `<!--COURSE-->` and `<!--TRACKS-->` marker
   pairs in the guide hero.
3. `scripts/build_tracks.py` - renders `docs/course-*/` and `docs/track-*/`, fills
   those markers and adds the pages to the embedded JSON. Fails if a marker is
   missing, so it must run after step 2. Also rewrites the folder READMEs.
4. `scripts/build_tree.py` - `tree.html`, reading the repo and `index.html`.

`extract_site.py` reads every page in `docs/`, keeps the reading order declared in
each section's `README.md`, resolves internal links to page ids, and parses every
table row in `resources/` that carries a link.

`build_site.py` writes two self-contained HTML files. No build step, no
framework, no external requests at runtime: the content is embedded, so the pages
work offline and from `file://`.

One dependency, `markdown`, pinned in `requirements.txt`. The scripts assume the
repo root as the working directory; `build_all.py` sets it for you. The guide
itself holds only the ten numbered sections: `extract_site.py` skips `course-*` and
`track-*` so step 3 owns them.
