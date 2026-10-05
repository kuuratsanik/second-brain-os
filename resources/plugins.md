# Obsidian plugins

Ranked by installs from Obsidian's own [community stats](https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugin-stats.json),
as of 5 October 2026. The catalog
([`community-plugins.json`](https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json))
lists over 8,400 plugins; these are the ones that matter for an
agent-maintained vault.

## Agents inside Obsidian

The third setup option in [Claude Code setup](../docs/02-setup/claude-code-setup.md):
instead of running the agent in a terminal pointed at the vault folder,
run it inside Obsidian.

| Plugin | Installs | What it does |
|---|---|---|
| [Copilot](https://github.com/logancyang/obsidian-copilot) | 2,325,427 | Runs Claude Code, Codex and OpenCode inside your vault |
| [Claudian](https://github.com/yishentu/claudian) | 2,310,792 | Embeds Claude Code, Codex and other local agents as collaborators in the vault |
| [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) | 1,226,919 | Local embedding model surfaces related notes while you write. No API key |
| [Local REST API with MCP](https://github.com/coddingtonbear/obsidian-local-rest-api) | 767,439 | Vault over a secure local API, now with a built-in MCP server |
| [Agent Client](https://github.com/rait-09/obsidian-agent-client) | 288,967 | Chat with Claude Code, Codex and Gemini CLI over the Agent Client Protocol |
| [Smart Composer](https://github.com/glowingjade/obsidian-smart-composer) | 175,211 | AI chat with note context and one-click edits |

## Structure and queries

| Plugin | Installs | What it does |
|---|---|---|
| [Templater](https://github.com/SilentVoid13/Templater) | 5,805,655 | Dynamic templates. For the pages you write by hand |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | 5,082,782 | Query language over your frontmatter. Answers "which pages have property P" |
| [Metadata Menu](https://github.com/mdelobelle/metadatamenu) | 349,916 | Manage frontmatter fields at scale. Useful once your [schema](../docs/04-structuring/frontmatter-schema.md) is fixed |
| [Supercharged Links](https://github.com/mdelobelle/obsidian_supercharged_links) | 219,662 | Styles links by the target note's frontmatter, so page type is visible inline |

## Graph

| Plugin | Installs | What it does |
|---|---|---|
| [Breadcrumbs](https://github.com/michaelpporter/breadcrumbs) | 373,993 | Typed links plus trees, matrices, Mermaid and Canvas export |
| [ExcaliBrain](https://github.com/zsviczian/excalibrain) | 348,399 | Structured mind-map deriving five relationship types from links, Dataview fields and tags |
| [Juggl](https://github.com/HEmile/juggl) | 137,911 | Interactive Cytoscape.js graph with typed edges and a saveable workspace mode |
| [3D Graph](https://github.com/AlexW00/obsidian-3d-graph) | 74,870 | The vault as a 3D force graph. Shows cluster structure a 2D hairball hides |
| [Graph Analysis](https://github.com/SkepticMystic/graph-analysis) | not in the catalog | Graph algorithms and similarity measures over the vault, surfaces unlinked connections |

## Maintenance

| Plugin | Installs | What it does |
|---|---|---|
| [Git](https://github.com/Vinzent03/obsidian-git) | 3,241,254 | Commit and sync the vault from inside Obsidian. See [versioning](../docs/09-maintenance/versioning-with-git.md) |
| [Omnisearch](https://github.com/scambier/obsidian-omnisearch) | 1,962,113 | Better full-text search, including inside PDFs |
| [Importer](https://github.com/obsidianmd/obsidian-importer) | 1,758,380 | Official importer from Notion, Evernote, Roam, Bear, Apple Notes. The first step for anyone [backfilling](../docs/03-ingestion/bulk-backfill.md) |
| [Linter](https://github.com/platers/obsidian-linter) | 1,176,094 | Formats notes to consistent rules. Set it carefully, it rewrites files |
| [Find orphaned files and broken links](https://github.com/Vinzent03/find-unlinked-files) | 229,530 | Exactly what [lint](../docs/09-maintenance/lint-and-health.md) checks, without leaving Obsidian |

## Capture and study

| Plugin | Installs | What it does |
|---|---|---|
| [Excalidraw](https://github.com/zsviczian/obsidian-excalidraw-plugin) | 8,339,520 | The most installed plugin in the catalog. Diagrams that live in the vault as files |
| [QuickAdd](https://github.com/chhoumann/quickadd) | 2,189,945 | One-keystroke capture into a chosen folder and template |
| [Spaced Repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition) | 608,982 | Flashcards from your own notes. See [learning from your vault](../docs/08-outputs/teaching-yourself.md) |
| [Zotero Integration](https://github.com/obsidian-community/obsidian-zotero-integration) | 574,938 | Citations, bibliographies and PDF annotations from Zotero |
| [Webpage HTML Export](https://github.com/KosmosisDire/obsidian-webpage-export) | 156,810 | Export notes, canvases or the whole vault as HTML |
| [ReadItLater](https://github.com/DominikPieper/obsidian-ReadItLater) | 135,809 | Saves online content into the vault with a template |

## A warning about plugin count

Every plugin is code with write access to your notes, running alongside an agent
that also writes to them. Two things that rewrite files on their own schedule
will eventually disagree.

Install what solves a problem you actually have. An empty vault with fifteen
plugins is a procrastination artifact.
