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
| `scripts/` | Vault scripts (copied by the Quickstart) and the site builders (`build_*.py`) | Yes, except `build_*.py` |
| `plugins/`, `.claude-plugin/` | The agents-course Claude Code plugin and marketplace | Yes |
| `tools/` | Site generators, shared helpers, doc link checker, kit checker | No |
| `tests/` | `unittest` tests for the vault scripts | No |
| `index.html`, `resources.html`, `tree.html` | Generated site, committed for GitHub Pages | Published |
| `.claude/agents/` | Agents for working on this repo | No |

`agents/` is product content for users' vaults. Agents for developing this
repo go in `.claude/agents/`, never in `agents/`.

## Building the site

The HTML files are generated. Never edit them by hand.

```bash
pip install -r requirements.txt   # pins markdown; needs Python 3.11+
python3 scripts/build_all.py      # the whole pipeline, in order
```

`build_all.py` runs, in this order: `tools/extract_site.py` (docs and
resources to `site_data.json`), `tools/build_site.py` (guide and resources
pages, with empty marker blocks for the course and handbooks),
`scripts/build_tracks.py` (fills the markers, rewrites the
`docs/course-*/` and `docs/track-*/` READMEs), `scripts/build_tree.py`
(`tree.html`, which reads `index.html`) and `scripts/build_static.py`
(`sitemap.xml`, `robots.txt`, `404.html`). The order matters: each step reads
the previous step's output. The build is deterministic, and CI
(`.github/workflows/site.yml`) fails if the committed HTML differs from a
fresh build.

The pinned `markdown==3.11` needs Python 3.11 or newer. The vault scripts have
no such floor. CI also runs three stdlib-only checks, which you can run locally:
`python3 tools/doc_links.py` (relative links and anchors in `docs/` and
`README.md`; add `--selftest`), `python3 tools/check_kit.py` (frontmatter,
references and plugin manifests in the shipped kit; add `--selftest`) and
`python3 -m unittest discover -s tests -t .` (the vault scripts, also run on
Windows).

Rebuild after any change to `docs/`, `resources/`, `skills/`, `commands/`,
`agents/`, `scripts/` or `plugins/`, and commit the result in the same change.

## Standards

From `CONTRIBUTING.md`: primary sources for every factual claim, plain
writing with no marketing language or emoji, one topic per change, and a new
docs page updates its section `README.md` index.

## Team

- `content` (Sonnet): markdown content.
- `tooling` (Sonnet): generators, scripts, generated HTML, CI.
- `adversary` (Fable): read-only review. Content and tooling ask it to review
  every task before marking it complete.
