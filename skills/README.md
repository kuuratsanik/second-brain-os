# skills

Twenty-nine skills covering every workflow in the guide. Plain `SKILL.md` files, so
they work with Claude Code and with any agent that reads the Agent Skills format.

| Skill | What it does |
|---|---|
| `second-brain-archive` | Archive orphaned, stale and cold pages |
| `second-brain-ask` | Answer a question from the vault with line-level citations |
| `second-brain-backfill` | Backfill an archive |
| `second-brain-brief` | Brief the owner on what needs attention |
| `second-brain-capture` | Capture Gmail, Granola and Notion items into raw/, read-only |
| `second-brain-changed-my-mind` | Trace changed positions |
| `second-brain-chat-import` | Import chat history |
| `second-brain-commit` | Commit a run, by path |
| `second-brain-doctor` | Check the setup |
| `second-brain-flashcards` | Make flashcards from concept pages |
| `second-brain-graph` | Analyse the graph |
| `second-brain-ingest` | Ingest a source |
| `second-brain-lifecycle` | Move self-improvement ideas to experiments, reviews and decisions |
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

Or install the whole kit as the `second-brain` plugin, which loads the skills,
commands and agents from `~/.claude/plugins/` and names the skills
`/second-brain:second-brain-ingest` and so on. Pick one method per vault, not
both. See [plugins](../plugins/README.md#second-brain).

## Version and updates

[`VERSION`](VERSION) holds the kit version, one line. It covers the skills,
commands, agents and vault scripts together (the agents-course plugin is
versioned separately), and [`CHANGELOG.md`](../CHANGELOG.md)
at the repository root says what changed in each version. Copying the whole
`skills/` folder (as the Quickstart does) puts `VERSION` at
`.claude/skills/VERSION`, which is how a vault records what it was installed
from. A vault without that file predates versioning.

To update a plugin install, run `claude plugin update second-brain@second-brain-os`.
To update a vault that has copies, pull the checkout and run `/install` in the vault. It
compares the two versions, shows the CHANGELOG entries since yours, and lists
the copy commands for you to run. It never overwrites the vault's `CLAUDE.md`
or `.claude/settings.json`.

The plugin's manifest, [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json),
carries the same version, and `claude plugin update` finds a new release only when
it changes. Bump `VERSION` and the manifest's `version` together;
`tools/check_kit.py` fails when they differ.

Bump `VERSION` in the same change as any user-facing edit to the kit: a major
version for a change that breaks an existing vault (a rename, a removed
command), a minor version for new skills or commands, a patch version for fixes.

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
