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
| `vault_mcp.py` | Read-only MCP server (stdio) for Claude Code or Claude Desktop: search, read page, backlinks, stale, duplicates, health, lifecycle |
| `chat_export_to_md.py` | Chat history export into per-conversation markdown |

```bash
python3 scripts/vault_stats.py ~/brain
python3 scripts/link_check.py ~/brain
python3 scripts/link_check.py ~/brain --stale 90      # path, date, age in days, oldest first
python3 scripts/link_check.py ~/brain --duplicates    # same name once punctuation is ignored, or shared aliases
python3 scripts/graph_export.py ~/brain graph.graphml --format graphml
python3 scripts/vault_search.py ~/brain "weekly review" --limit 5
python3 scripts/dashboard.py ~/brain                  # writes ~/brain/output/dashboard.html
python3 scripts/vault_mcp.py ~/brain                   # started by an MCP client, not by hand
```

### vault_search.py

```
python3 scripts/vault_search.py VAULT QUERY [--limit N] [--json]
    [--include-archive] [--include-restricted]
    [--embed-url URL] [--embed-cache PATH] [--embed-model NAME] [--allow-remote-embed]
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
is slow. `--embed-url` takes the server's base address; a trailing `/v1` is
fine. The request has no `model` field unless you pass `--embed-model NAME`.

Page text and the query go to that server, so the script only accepts one on
this machine (`localhost`, `127.x.x.x`, `::1`). Another address is refused with
exit 2 unless you add `--allow-remote-embed`. Restricted pages are never sent
unless you pass `--include-restricted`. The cache holds vectors of your pages,
which can be used to infer their content, so keep it out of version control:
`vault-template/.gitignore` already lists `.cache/`. Whenever the cache's keys
differ from the current chunks, the file is rewritten without the others, so
vectors of a restricted page or of text you deleted do not linger after the
next run without `--include-restricted`. A damaged cache entry, or a server
that changes model or vector size, is handled by embedding again. If the
server cannot be reached, the script warns on stderr and answers with BM25,
exit 0.

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

The funnel has five stages: idea (`new`, `considering`), plan (`planned`),
experiment (`active`, `reviewing`; review is folded in here), adopted and
dropped. `promoted` ideas and other statuses are listed under the funnel, and a
restricted page's status is counted as `(restricted)`. Dropped ideas move to
`archive/`, which is not counted, so "dropped" is in practice the number of
dropped experiments. The script needs `link_check.py` and `vault_search.py` in
the same folder.

### vault_mcp.py

```
python3 scripts/vault_mcp.py VAULT [--embed-url URL [--embed-model NAME] [--allow-remote-embed]] [--allow-raw]
```

A read-only [Model Context Protocol](https://modelcontextprotocol.io/) server
for the vault, so an MCP client (Claude Code, Claude Desktop) can search and
read your notes without shell access. It reads and writes JSON-RPC 2.0 over
standard input and output, one message per line; logs go to stderr, and
nothing but protocol messages goes to stdout. You do not run it yourself: the
client starts it. Python 3.9 or newer, no installs, Windows included.

| Tool | Arguments | Returns |
|---|---|---|
| `search` | `query`, `limit` (1 to 50, default 10) | Ranked hits from `vault_search.py`, each with `path`, `title`, `score`, `line`, `snippet` and `citation` (`path:line`) |
| `read_page` | `path` | The page text (frontmatter included, so line numbers match the citations) and the parsed frontmatter |
| `backlinks` | `path` | Pages that link to the page, from the `link_check.py` link graph |
| `stale` | `days` (default 90) | Pages not updated for more than `days` days, as in `dashboard.py --json` |
| `duplicates` | none | Duplicate-name groups, as in `dashboard.py --json` |
| `health` | none | Counts, broken links, orphans, stubs, pages per folder, most linked pages, needs-owner count |
| `lifecycle_status` | none | Idea and experiment pages by funnel stage (`dashboard.py`'s `FUNNEL`) |

There is no tool that writes. The server never changes the vault; the one file
it can write is the embedding cache that `vault_search.py` keeps in
`VAULT/.cache/embeddings.json` when you pass `--embed-url` (see
[vault_search.py](#vault_searchpy); the page text goes to that server, so keep
it on your machine). The server takes `--embed-model` and `--allow-remote-embed`
with the same meaning as the script, and refuses a non-local `--embed-url`
without the latter. The search index and link graph are built on the first
call and kept in memory; they are rebuilt when a page changes, is added or is
removed.

What it will not return:

- A page with `sensitivity: restricted`, or with a `sensitivity:` value other
  than `normal`, `public` or `private`, is refused by `read_page` and `backlinks`
  and left out of `search`. The key is read in any letter case. The other tools
  show such a page by path only, with no title, link target or name.
- A `private` page is returned with `"private": true` and a notice. The model
  can still quote it to you, so connect this server only to a client you trust
  with those notes.
- `read_page` takes a vault-relative path to a `.md` file. It refuses absolute
  paths, drive letters, `..`, Windows stream and wildcard characters, any
  folder whose name starts with a dot (`.git`, `.claude`, `.obsidian`,
  `.cache`), `journal/`, and `raw/` unless you start the server with
  `--allow-raw`. It follows symlinks and then checks the real location, so a
  link that leaves the vault, or points into a refused folder, is refused too.
  Symlinked files that resolve outside the vault are also kept out of the
  index. Files with more than one hard link are refused and not indexed, since
  a hard link cannot be traced back to where it points; copy such a page
  instead. `--allow-raw` opens `raw/` only; restricted pages in it stay closed.
- Output is capped: 200,000 characters of page text, 200 entries per list.

A failing tool returns a normal result with `isError: true` and a message the
model can act on. Unknown methods and malformed requests get JSON-RPC errors.

Protocol: implemented from the MCP specification revision 2026-07-28 (the
latest when this was written; fetched 2026-10-06 from the specification source
in the `modelcontextprotocol/modelcontextprotocol` repository, because
modelcontextprotocol.io was not reachable from the build environment). That
revision removed the `initialize` handshake and `ping`, and clients are still
moving over, so the server speaks both: a request that carries
`io.modelcontextprotocol/protocolVersion` in `_meta` is served as 2026-07-28
(`server/discover`, `tools/list`, `tools/call`), and `initialize` starts a
session that negotiates 2025-11-25 or 2025-06-18
(`ping`, `tools/list`, `tools/call`). Only the `tools` capability is
advertised. 2025-03-26 and 2024-11-05 are not offered, because they allow
JSON-RPC batches, which the server does not accept. Details are in the module docstring.

#### Connect it to Claude Code

Syntax from [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)
(fetched 2026-10-06). Everything after `--` is the server's command. This adds
it at the default local scope (this project, only you):

```bash
claude mcp add --transport stdio second-brain -- python3 ~/brain/scripts/vault_mcp.py ~/brain
claude mcp get second-brain          # shows whether it connected
```

Add `--scope project` to write a `.mcp.json` at the project root instead, which
you can commit; Claude Code asks each person to approve a project server the
first time. The same file by hand, in the vault root (the `:-.` default is
what the docs prescribe, because `CLAUDE_PROJECT_DIR` is set only in the
server's environment):

```json
{
  "mcpServers": {
    "second-brain": {
      "type": "stdio",
      "command": "python3",
      "args": ["${CLAUDE_PROJECT_DIR:-.}/scripts/vault_mcp.py", "${CLAUDE_PROJECT_DIR:-.}"]
    }
  }
}
```

On Windows use `python` (or `py`) for `python3`. These commands and the file
follow the page above; they have not been run against a live Claude Code here.

#### Connect it to Claude Desktop

Claude Desktop reads `claude_desktop_config.json`: Settings, Developer, Edit
Config opens it. Its location, the `mcpServers` shape and the advice to use
absolute paths come from the MCP project's guide
[Connect to local MCP servers](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers)
(fetched 2026-10-06 from its source in the `modelcontextprotocol/modelcontextprotocol`
repository, `docs/docs/2026-07-28/develop/connect-local-servers.mdx`). Anthropic's
help-center page on local MCP servers (fetched the same day) covers desktop
extensions and does not describe this file, so the file is not re-checked
against Anthropic's own pages.

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "second-brain": {
      "command": "/usr/bin/python3",
      "args": ["/Users/you/brain/scripts/vault_mcp.py", "/Users/you/brain"]
    }
  }
}
```

On Windows, double the backslashes: `"command": "C:\\Python313\\python.exe"` and
`"args": ["C:\\Users\\you\\brain\\scripts\\vault_mcp.py", "C:\\Users\\you\\brain"]`.
Quit and restart Claude Desktop after saving. If the server does not connect,
the guide says to read `mcp.log` and `mcp-server-second-brain.log` in
`~/Library/Logs/Claude` (macOS) or `%APPDATA%\Claude\logs` (Windows); this
server's stderr lands in the second one. Use the full path to the Python you
want (`which python3`, `where python`): a desktop app may not see your shell's
`PATH`. That last point is a precaution, not a statement from the guide.

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
