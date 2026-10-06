# scripts

Small, dependency-free Python scripts. Everything here reads the vault as
plain files, so nothing breaks if you switch editors or agents.

| Script | What it does |
|---|---|
| `link_check.py` | Broken wikilinks, orphan pages, stubs; `--stale DAYS` and `--duplicates` list old and likely duplicate pages |
| `vault_stats.py` | Page counts, link density, orphan rate, most-linked pages |
| `graph_export.py` | Wikilink graph as CSV edges or GraphML for Gephi |
| `vault_search.py` | Ranked search with `path:line` citations; BM25, optionally hybrid with local embeddings |
| `dashboard.py` | One self-contained HTML page of vault health: counts, funnel, stale pages, duplicates |
| `chat_export_to_md.py` | Chat history export into per-conversation markdown |

```bash
python3 scripts/vault_stats.py ~/brain
python3 scripts/link_check.py ~/brain
python3 scripts/link_check.py ~/brain --stale 90      # path, date, age in days, oldest first
python3 scripts/link_check.py ~/brain --duplicates    # same name once punctuation is ignored, or shared aliases
python3 scripts/graph_export.py ~/brain graph.graphml --format graphml
python3 scripts/vault_search.py ~/brain "weekly review" --limit 5
python3 scripts/dashboard.py ~/brain                  # writes ~/brain/output/dashboard.html
```

### vault_search.py

```
python3 scripts/vault_search.py VAULT QUERY [--limit N] [--json]
    [--include-archive] [--include-restricted]
    [--embed-url URL] [--embed-cache PATH]
```

Each hit is `path:line`, the title, a score and a snippet of about 200
characters; `line` is the 1-based line of the best match, so an answer can cite
it. Ranking is BM25 with title above aliases above `##` headings above body.
Text is compared in Unicode NFC and case-folded, and diacritics must match:
`õppimine` finds `õppimine`. A folded fallback lets `oppimine` find it too, at a
lower score. There is no stemming, so `õppimine` does not find `õppimise`.

- Pages with `sensitivity: restricted` are left out; `--include-restricted`
  adds them. `private` pages are included and marked in the output and as
  `sensitivity` in `--json`.
- `archive/`, `journal/`, `raw/` and the other skipped folders are not searched;
  `--include-archive` adds `archive/`.
- `--json` prints `{"query", "mode", "count", "hits": [{"path", "title",
  "score", "line", "snippet", "sensitivity"}]}`.
- Exit 0 with or without hits, 1 for a vault path that is not a folder, 2 for a
  usage error.

For semantic matches, start a llama.cpp `llama-server` with an embedding model
and `--embedding`, then pass its address, for example
`--embed-url http://127.0.0.1:8080`. The script posts chunks to its
OpenAI-compatible `/v1/embeddings` endpoint and fuses the BM25 and cosine
rankings by reciprocal rank fusion (`mode` is then `hybrid`). Vectors are cached
in `VAULT/.cache/embeddings.json` (or `--embed-cache`), keyed by a hash of each
chunk, so only changed chunks are embedded again; the first run on a large vault
is slow. Page text and the query go to that server, so use one on your own
machine; the script warns when the address is not local. Restricted pages are
never sent unless you pass `--include-restricted`. If the server cannot be
reached, the script warns on stderr and answers with BM25, exit 0.

### dashboard.py

```
python3 scripts/dashboard.py VAULT [--out output/dashboard.html] [--stale-days 90] [--json]
```

Writes one HTML file with no external scripts, styles or fonts, in light or dark
to match the browser. It shows page, link, broken, orphan and stub counts, stale
pages (by `updated:`, then `created:`, then file date, as `link_check.py
--stale` does), duplicate groups, the idea-to-adopted funnel from `status:` on
`type: idea` and `type: experiment` pages, pages per top-level folder, the 10
most linked pages and the open items in `wiki/systems/needs-owner.md`. A
restricted page counts in the numbers but only its path is written. `--out` is
relative to the vault. `--json` prints the data instead and writes no file. The
same vault on the same day gives the same bytes. Exit codes are as above.

Copy the vault scripts (everything except the `build_*.py` files) into the vault's `scripts/` folder (the
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
