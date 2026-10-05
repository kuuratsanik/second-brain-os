# skills

Twenty-four skills covering every workflow in the guide. Plain `SKILL.md` files, so
they work with Claude Code and with any agent that reads the Agent Skills format.

| Skill | What it does |
|---|---|
| `second-brain-archive` | Archive orphaned, stale and cold pages |
| `second-brain-backfill` | Backfill an archive |
| `second-brain-changed-my-mind` | Trace changed positions |
| `second-brain-chat-import` | Import chat history |
| `second-brain-commit` | Commit a run, by path |
| `second-brain-doctor` | Check the setup |
| `second-brain-graph` | Analyse the graph |
| `second-brain-ingest` | Ingest a source |
| `second-brain-lint` | Lint the vault |
| `second-brain-merge` | Merge duplicate pages |
| `second-brain-metrics` | Record metrics |
| `second-brain-privacy` | Audit privacy |
| `second-brain-project` | Set up a project |
| `second-brain-publish` | Prepare to publish |
| `second-brain-query` | Query the vault |
| `second-brain-quiz` | Quiz from your own pages |
| `second-brain-rename` | Rename a page |
| `second-brain-report` | Write a research report |
| `second-brain-review` | Review the vault |
| `second-brain-rollback` | Undo one run |
| `second-brain-schedule` | Propose scheduled maintenance |
| `second-brain-structure` | Link, split, retype, tag and alias pages |
| `second-brain-transcript` | Clean a transcript |
| `second-brain-write` | Write from the vault |

## Install

```bash
mkdir -p ~/.claude/skills
cp -r skills/second-brain-* ~/.claude/skills/
```

Or keep them inside the vault at `.claude/skills/` so they travel with it and get
versioned alongside your notes.

## Which ones matter most

`second-brain-ingest` and `second-brain-query` carry the system. The linking rule
in the first and the citation rule in the second are the two that keep a vault
from degrading into a folder of summaries; loosen either and the rest stops
paying off.

`second-brain-archive`, `second-brain-commit`, `second-brain-rollback` and
`second-brain-structure` change or move existing pages. Their default is to
propose, and to act on their own only where the vault's `CLAUDE.md` grants it;
`second-brain-doctor` and `second-brain-schedule` only report and propose.

Everything else is fair game to adapt. These are opinions, and yours may differ.
