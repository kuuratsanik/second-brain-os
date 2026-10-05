# tools

The site at [kuuratsanik.github.io/second-brain-os](https://kuuratsanik.github.io/second-brain-os/)
is generated from this repository, so it cannot drift from the guide.

```bash
pip install -r requirements.txt   # Python 3.11+ (markdown 3.11)
python3 scripts/build_all.py
```

`scripts/build_all.py` is the single entry point. It runs five steps in order,
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
5. `scripts/build_static.py` - `sitemap.xml`, `robots.txt` and `404.html`.

`extract_site.py` reads every page in `docs/`, keeps the reading order declared in
each section's `README.md`, resolves internal links to page ids, and parses every
table row in `resources/` that carries a link.

`build_site.py` writes two self-contained HTML files. No build step, no
framework, no external requests at runtime: the content is embedded, so the pages
work offline and from `file://`.

One dependency, `markdown`, pinned in `requirements.txt` and needing Python 3.11 or
newer. The scripts assume the
repo root as the working directory; `build_all.py` sets it for you. The guide
itself holds only the ten numbered sections: `extract_site.py` skips `course-*` and
`track-*` so step 3 owns them.

`site_common.py` holds what every generator shares: the fork and upstream URLs,
the favicon, the page head (description, canonical, Open Graph and Twitter
tags, theme-color), the skip link, header and footer, the CSS minifier and the compact
JSON writer. Change the repository owner or the credit line there.

`doc_links.py` is a stdlib-only check for relative markdown links and `#anchors`
in `docs/` and `README.md`. CI runs it; run it locally before committing docs.
`python3 tools/doc_links.py --selftest` checks the checker.

`check_kit.py` is a stdlib-only validator for what ships to users' vaults:
`skills/`, `commands/`, `agents/` and `plugins/`. It checks that frontmatter
parses, required fields are present and no key is outside the list in the
Claude Code docs (source URLs are in the script), that skill names match their
folders and descriptions fit 1,536 characters, that every `second-brain-*` skill
and `scripts/*.py` a file names exists, that `argument-hint` is set exactly when
a command uses `$ARGUMENTS`, that `marketplace.json` and each `plugin.json` are
valid with resolving sources, that `vault-template/.claude/settings.json` has
only known top-level and `permissions` keys (`SETTINGS_KEYS`), well-formed
hooks with valid event names (`HOOK_EVENTS`), no rule in two lists, and
existing `${CLAUDE_PROJECT_DIR}/...` hook paths, and that the schedulable list in
`commands/README.md` equals the commands without `disable-model-invocation:
true`. It reports `path:line: message` and exits 1 on any problem. It never edits
anything. Run `python3 tools/check_kit.py` and `python3 tools/check_kit.py
--selftest`; when the Claude Code docs add a frontmatter field, a settings key
or a hook event, update the key sets at the top of the script.

`tests/` holds `unittest` tests for the four vault scripts, using a fixture vault
built in a temp dir (CRLF and BOM files, aliases, piped links, skip folders and
`--include`, CSV and GraphML shape, and ChatGPT and Claude chat exports). Run
`python3 -m unittest discover -s tests -t .` from the repo root. No installs.
CI runs these on Linux with Python 3.9 and on Windows with Python 3.13, because
the vault scripts must work on plain Python 3 everywhere.

Size: the embedded JSON carries only `id`, `title` and `html` per page. Search
text, section, source path and heading lists are derived in the browser, and the
CSS and JS are minified. To measure, run `wc -c index.html` and
`gzip -9 -c index.html | wc -c` (both in bytes) before and after a change.

CI runs on pushes to `main` and on pull requests, not on pushes to other
branches. Open a pull request, or run `python3 scripts/build_all.py` and the
checks above locally, to get the same checks on a feature branch. Every action
in `.github/workflows/` is pinned to a full commit SHA with the version in a
comment; Dependabot (`.github/dependabot.yml`) proposes weekly updates for
actions and pip.
