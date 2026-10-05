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
| `scripts/` | Vault scripts (copied by the Quickstart) and two site builders | Yes, except `build_*.py` |
| `plugins/`, `.claude-plugin/` | The agents-course Claude Code plugin and marketplace | Yes |
| `tools/` | Site generators | No |
| `index.html`, `resources.html`, `tree.html` | Generated site, committed for GitHub Pages | Published |
| `.claude/agents/` | Agents for working on this repo | No |

`agents/` is product content for users' vaults. Agents for developing this
repo go in `.claude/agents/`, never in `agents/`.

## Building the site

The HTML files are generated. Never edit them by hand.

```bash
pip install markdown
python3 tools/extract_site.py   # docs + resources -> site_data.json
python3 tools/build_site.py     # -> index.html, resources.html
python3 scripts/build_tracks.py # course + handbooks -> index.html
python3 scripts/build_tree.py   # -> tree.html
```

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
