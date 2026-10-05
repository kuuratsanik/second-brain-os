# commands

Seventy-two slash commands for Claude Code, grouped by what you are doing.

```bash
mkdir -p ~/brain/.claude/commands
cp commands/*.md ~/brain/.claude/commands/ && rm ~/brain/.claude/commands/README.md
```

Leave this README out: anything in `.claude/commands/` becomes a slash command,
and `/README` is not one you want.

Commands are thin on purpose: each one points at a skill and sets its scope. The
behaviour lives in the skill, so `/ingest-youtube` and a scheduled task and you
asking in plain language all produce the same result.

Except for the maintenance set, every command sets `disable-model-invocation:
true`: it runs only when you type it, and the skills handle automatic
triggering. This also keeps those descriptions out of every session's context.
The maintenance set can be scheduled and run without you: `/ingest`, `/link`,
`/lint`, `/review`, `/weekly`, `/monthly`, `/metrics`, `/health`, `/commit`,
`/stale`, `/orphans`, `/prune`, `/archive`, `/dedupe`, `/backfill` and
`/index`. A scheduled task can fire only these.

Some commands overlap on purpose, and each says when to use its sibling:
`/ask`, `/know` and `/trace` (a question, a topic, a question with its reading
trail); `/contradictions` (the vault's open ones) and `/contradicts` (one claim
of yours); `/timeline` (the sources over time) and `/changed-my-mind` (your own
revisions); `/health`, `/graph`, `/metrics` and `/monthly` (a quick look, the
full report, a recorded snapshot, the monthly review); `/orphans`, `/stale`,
`/prune` and `/archive` (no inbound links, untouched, removal candidates, the
move itself); `/ingest-youtube` (someone else's recording) and `/ingest-voice`
(your own); `/review` (any period) and `/weekly`, which is `/review` with no
argument.

Most take an optional argument. With none, they default to the sensible whole:
`/lint` audits everything, `/ingest` takes whatever is waiting in `raw/`.

### Ingestion

| Command | What it does |
|---|---|
| `/ingest` | Ingest new material from raw/ into the wiki |
| `/ingest-url` | Clip and ingest a web page |
| `/ingest-youtube` | Ingest someone else's video or podcast |
| `/ingest-pdf` | Ingest a PDF |
| `/ingest-paper` | Ingest an academic paper |
| `/ingest-chats` | Import an exported chat history |
| `/ingest-voice` | Ingest your own voice note |
| `/ingest-newsletter` | Ingest newsletters without duplicating |
| `/ingest-highlights` | Ingest book or article highlights |
| `/backfill` | Bulk import an archive in batches |

### Structuring

| Command | What it does |
|---|---|
| `/link` | Find and add missing connections |
| `/dedupe` | Find near-duplicate pages |
| `/merge` | Merge two pages |
| `/rename` | Rename a page and fix every link |
| `/split` | Split an overloaded page |
| `/retype` | Fix a page's type |
| `/schema` | Check frontmatter against the schema |
| `/tags` | Audit the tag vocabulary |
| `/aliases` | Find missing aliases |
| `/contradictions` | List every open contradiction |
| `/index` | Rebuild the index |

### Graph

| Command | What it does |
|---|---|
| `/graph` | Report the shape of the graph |
| `/graph-export` | Export the graph for outside analysis |
| `/orphans` | Find unreachable pages |
| `/hubs` | Find pages that swallowed the graph |
| `/bridges` | Find the pages holding the graph together |
| `/clusters` | Show what the vault is actually about |
| `/typed-links` | Add relation types where they matter |
| `/stale` | Find concept pages nobody has touched |

### Retrieval

| Command | What it does |
|---|---|
| `/ask` | Answer a specific question from the vault |
| `/know` | Inventory what the vault holds on a topic |
| `/connect` | Find the path between two ideas |
| `/compare` | Compare two things from your own sources |
| `/sources` | Show what a claim rests on |
| `/gaps` | What is missing from my understanding |
| `/contradicts` | Argue against a claim of mine |
| `/timeline` | How sources on a topic developed over time |
| `/trace` | Answer a question and show the pages read |
| `/changed-my-mind` | What I have revised in my own positions |

### Maintenance

| Command | What it does |
|---|---|
| `/lint` | Audit structure and repair what is mechanical |
| `/health` | Quick health check, no recording |
| `/metrics` | Record a dated metrics snapshot |
| `/review` | Review what the vault learned over any period |
| `/weekly` | The weekly review (`/review` with no argument) |
| `/monthly` | The monthly structural review |
| `/prune` | Propose what is safe to remove; archives only if CLAUDE.md grants autonomy |
| `/archive` | Propose cold material to move out of the wiki; moves only if CLAUDE.md grants autonomy |
| `/commit` | Commit what this run wrote, by path |

### Outputs

| Command | What it does |
|---|---|
| `/outline` | Outline a piece from your concept pages |
| `/draft` | Draft from the vault |
| `/report` | Write a research report |
| `/publish` | Check what is safe to publish |
| `/export` | Export a page or set of pages |
| `/quiz` | Test yourself on your own pages |
| `/explain` | Explain it back and find the gaps |
| `/ingest-mine` | Ingest your own finished work |

### Projects

| Command | What it does |
|---|---|
| `/project` | Create a project |
| `/project-status` | Where a project stands |
| `/decisions` | List decisions made |
| `/commitments` | List open commitments |
| `/handoff` | Prepare a handoff brief |
| `/scope` | Pull knowledge into a project |

### Safety

| Command | What it does |
|---|---|
| `/privacy` | Audit what should not be in the vault |
| `/secrets` | Scan for credentials |
| `/dry-run` | Preview a run without writing |
| `/rollback` | Undo one run, leaving your edits alone |
| `/audit` | Audit what an agent did |

### Setup

| Command | What it does |
|---|---|
| `/init` | Scaffold a new vault |
| `/claude-md` | Build or update your CLAUDE.md |
| `/install` | Install the skills, commands and agents |
| `/doctor` | Check the setup is working |
| `/maintenance-schedule` | Propose scheduled maintenance |

## Why so many

Twenty-four skills do the real work. Most commands are scoped entry points into
them; a few, such as `/dry-run`, `/audit`, `/index` and `/scope`, carry short
self-contained instructions instead. That is the point: you should not have to remember how to phrase a
request for a thing you do every week.

If a command you want is missing, it is usually one line pointing at an existing
skill. Copy the closest file and change the scope.
