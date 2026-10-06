# scripts

Small, dependency-free Python scripts. Everything here reads the vault as
plain files, so nothing breaks if you switch editors or agents.

| Script | What it does |
|---|---|
| `link_check.py` | Broken wikilinks, orphan pages, stubs; `--stale DAYS` and `--duplicates` list old and likely duplicate pages |
| `vault_stats.py` | Page counts, link density, orphan rate, most-linked pages |
| `graph_export.py` | Wikilink graph as CSV edges or GraphML for Gephi |
| `chat_export_to_md.py` | Chat history export into per-conversation markdown |

```bash
python3 scripts/vault_stats.py ~/brain
python3 scripts/link_check.py ~/brain
python3 scripts/link_check.py ~/brain --stale 90      # path, date, age in days, oldest first
python3 scripts/link_check.py ~/brain --duplicates    # same name once punctuation is ignored, or shared aliases
python3 scripts/graph_export.py ~/brain graph.graphml --format graphml
```

Copy the four vault scripts into the vault's `scripts/` folder (the
[Quickstart](../README.md#quickstart) does this; the `build_*.py` files are site
builders and stay behind) so the `/metrics`, `/health` and `/graph-export` commands can find
them. Hidden folders such as `.claude/` and `.obsidian/`, `templates/`,
`scripts/`, `raw/`, `archive/`, `journal/`, `output/`, and any `CLAUDE.md` or
`README.md` are skipped, so the counts describe your wiki, not the tooling or
the cold and generated material around it. Pass `--include archive,journal` to
count folders anyway. On Windows, `python3` is
usually the Microsoft Store stub; run these with `python` instead.

The agent can do all of this in natural language, but a script gives the same
answer every time and costs nothing to run, which is what you want for anything
you check weekly.
