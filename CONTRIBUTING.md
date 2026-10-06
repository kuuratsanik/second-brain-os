# Contributing

## What is wanted

- Fixes to the guide where it is wrong or out of date
- Resources that are genuinely worth someone's time
- Examples: real vault structures, real output, screenshots
- Skills and commands that solve a problem the existing ones do not

## What is not

- Tool listings with no explanation of why the tool is worth using
- Affiliate or referral links
- Pages padded with general advice that applies to any note system

## Standards

Every factual claim needs a source, and the source has to be the primary one:
the README, the paper, the release note, not somebody's summary of it. Numbers
that appear only in secondary coverage get dropped. If two sources disagree,
say so rather than picking the one that reads better.

Write plainly. No marketing language, no emoji, no filler.

## Pull requests

One topic per PR. If you are adding a docs page, follow the shape of the
existing pages in that section.

### Before you open a PR

CI (`.github/workflows/site.yml`) runs these on every pull request. Run them
locally first, from the repository root:

```bash
pip install -r requirements.txt          # pins markdown; needs Python 3.11+
python3 tools/check_kit.py --selftest && python3 tools/check_kit.py
python3 -m unittest discover -s tests -t .
python3 tools/doc_links.py --selftest && python3 tools/doc_links.py
python3 tools/check_external_links.py --selftest   # no network; the real check runs weekly, see link-rot.yml
python3 vault-template/.claude/hooks/test_guard.py
python3 tools/release_notes.py --selftest
python3 tools/bench_kv_slots.py --selftest   # fake local server; no llama-server needed
python3 scripts/build_all.py             # rebuild the site, then commit the result
python3 scripts/link_check.py vault-template

# lint, as in .github/workflows/lint.yml (pinned versions; any finding fails CI)
pip install ruff==0.16.10 zizmor==1.30.1
ruff check .                             # rules and the py39 target are in ruff.toml
zizmor --offline --no-progress .github   # workflow security audit
actionlint                               # workflow syntax; see the actionlint note below

# also run by the vault-scripts job, on the demo vault (use a temp path for the outputs)
python3 scripts/link_check.py examples/demo-vault
python3 scripts/vault_stats.py examples/demo-vault
python3 scripts/graph_export.py examples/demo-vault /tmp/graph.csv
python3 scripts/graph_export.py examples/demo-vault /tmp/graph.graphml --format graphml
```

- `actionlint` is a Go binary, not a pip package. CI installs release 1.7.12 and
  checks its SHA-256 (see `lint.yml`). Locally, download the same release from
  [rhysd/actionlint](https://github.com/rhysd/actionlint/blob/main/docs/install.md)
  or use your package manager; CI runs it either way.
- Commit the regenerated HTML (`index.html`, `resources.html`, `tree.html`,
  `404.html`, `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`,
  `feed.xml`, `og.png` and any changed `docs/*/README.md`;
  `site_data.json` is gitignored) in the same change. CI rebuilds the site and fails if
  `git status` shows anything different from what you committed. Never edit
  the generated files by hand.
- The vault scripts also run on Python 3.9 and on Windows in CI, so keep
  `scripts/*.py` to the standard library and avoid newer syntax there.
- Every factual claim cites its primary source, and a source you could not
  fetch is marked "not re-checked on <date> because the page could not be
  fetched".
- One topic per change.
- A new docs page updates its section `README.md` index in the same change.
  For the course and handbooks the index is generated from the page order in
  `scripts/build_tracks.py`, so add the page there.

## Releases

Only a maintainer does this. The kit version is the single line in
`skills/VERSION`; `.github/workflows/release.yml` turns a tag into a GitHub
release whose body is that version's section of `CHANGELOG.md`.

1. Set the new version `X.Y.Z` in `skills/VERSION` and in the `version` of
   `.claude-plugin/plugin.json`.
2. In `CHANGELOG.md`, move the entries under `## [Unreleased]` to a new
   `## [X.Y.Z] - YYYY-MM-DD` heading.
3. Run the checks above. `python3 tools/check_kit.py` fails if the two version
   files differ or the changelog has no heading for the version, and
   `python3 tools/release_notes.py X.Y.Z` prints the text the release will carry.
4. Open a pull request and merge it to `main`.
5. Tag the merge commit and push the tag:

   ```bash
   git checkout main && git pull
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```

The workflow publishes nothing and fails if the tag is not `vX.Y.Z`, differs
from `skills/VERSION` or `plugin.json`, is not in `main`, or has no changelog
section. To redo a failed release, delete the tag locally and on `origin`, fix
the cause, and tag again.
