# second-brain-os

A guide, an agents course and a set of handbooks, published as markdown and
as a static site, plus the skills, commands, agents, scripts and vault
template that readers copy into their own vault.

## Layout

| Path | What it is | Ships to users |
|---|---|---|
| `docs/` | Guide sections (`01`–`10`), course (`course-*`), handbooks (`track-*`) | Read on GitHub and the site |
| `resources/` | Vetted link tables, parsed into `resources.html` | Read |
| `skills/`, `commands/`, `agents/`, `vault-template/` | Copied into `~/brain` by the Quickstart | Yes |
| `scripts/` | The seven vault scripts (copied by the Quickstart) and the site builders (`build_*.py`) | Yes, except `build_*.py` |
| `plugins/`, `.claude-plugin/` | The agents-course plugin, the `second-brain` kit plugin (packaged from the repo root) and the marketplace | Yes |
| `tools/` | Site generators, shared helpers, doc link checker, kit checker, external link checker, release notes, KV-slot benchmark | No |
| `tests/` | `unittest` tests for the vault scripts (the guard has its own suite, `vault-template/.claude/hooks/test_guard.py`) | No |
| `index.html`, `resources.html`, `tree.html`, `404.html`, `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`, `feed.xml`, `og.png` | Generated site, committed for GitHub Pages | Published |
| `.claude/agents/`, `.claude/workflows/` | Agents and the `upgrade-round` workflow for working on this repo | No |

`agents/` is product content for users' vaults. Agents for developing this
repo go in `.claude/agents/`, never in `agents/`.

## Building the site

The site files listed above are generated. Never edit them by hand.

```bash
pip install -r requirements.txt   # pins markdown; needs Python 3.11+
python3 scripts/build_all.py      # the whole pipeline, in order
```

`build_all.py` runs, in this order: `tools/extract_site.py` (docs and
resources to `site_data.json`), `tools/build_site.py` (guide and resources
pages, with empty marker blocks for the course and handbooks),
`scripts/build_tracks.py` (fills the markers, rewrites the
`docs/course-*/` and `docs/track-*/` READMEs), `scripts/build_tree.py`
(`tree.html`, which reads `index.html`), `scripts/build_static.py`
(`sitemap.xml`, `robots.txt`, `404.html`), `scripts/build_llms.py`
(`llms.txt`, `llms-full.txt`, which reads `index.html`),
`scripts/build_feed.py` (`feed.xml` from `CHANGELOG.md`) and
`scripts/build_og.py` (`og.png`). The order matters: each step reads the
previous step's output. The build is deterministic, and CI
(`.github/workflows/site.yml`) fails if any committed generated file differs
from a fresh build.

The pinned `markdown==3.11` needs Python 3.11 or newer. The vault scripts and
the vault guard need Python 3.9 or newer. CI also runs these stdlib-only
checks, which you can run locally (`CONTRIBUTING.md` lists them in order):

- `python3 tools/check_kit.py` (frontmatter, references, plugin manifests,
  the vault-template `settings.json`, and that `skills/VERSION`,
  `plugin.json` and the `CHANGELOG.md` heading agree; add `--selftest`)
- `python3 tools/doc_links.py` (relative links and anchors in `docs/` and
  `README.md`; add `--selftest`)
- `python3 -m unittest discover -s tests -t .` (the vault scripts; also run on
  Python 3.9 and on Windows)
- `python3 vault-template/.claude/hooks/test_guard.py` (the guard and its
  regression corpus, `guard_corpus.json`; also run on Python 3.9 and Windows)
- `python3 scripts/link_check.py vault-template`
- `--selftest` of `tools/check_external_links.py`, `tools/release_notes.py`
  and `tools/bench_kv_slots.py`

`.github/workflows/lint.yml` runs `python3 -m ruff check .` (pinned version,
`ruff.toml`), actionlint and zizmor. `link-rot.yml` checks external links
weekly and only reports. `release.yml` publishes a GitHub release when a
`vX.Y.Z` tag that matches `skills/VERSION` is pushed.

Rebuild after any change to `docs/`, `resources/`, `skills/`, `commands/`,
`agents/`, `scripts/`, `tools/`, `plugins/` or `CHANGELOG.md`, and commit the
result in the same change.

## Standards

From `CONTRIBUTING.md`: primary sources for every factual claim, plain
writing with no marketing language or emoji, one topic per change, and a new
docs page updates its section `README.md` index.

## Team

- `content` (Sonnet): markdown content.
- `tooling` (Sonnet): generators, scripts, generated HTML, CI.
- `adversary` (Fable): read-only review. Content and tooling ask it to review
  every task before marking it complete.

For a batch of independent changes, the `upgrade-round` workflow
(`.claude/workflows/upgrade-round.js`) builds each task in its own worktree
and loops adversary review and fixes until it ships. It never merges or
pushes: the lead merges the branches, rebuilds the site once and pushes.
