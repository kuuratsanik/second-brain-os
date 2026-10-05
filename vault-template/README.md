# vault-template

A starting vault, set up for one owner with six domains: work, learning,
personal life, creative work, self-improvement and systems. Copy this folder
somewhere on your machine, open it in Obsidian as a vault, and start Claude Code
inside it.

```bash
cp -r vault-template ~/brain
cd ~/brain
claude
```

`CLAUDE.md` is the instruction sheet the agent reads every session. Read it
before your first run. Its Profile section is empty on purpose: fill it with the
interview from [the CLAUDE.md guide](../docs/02-setup/claude-md.md) before you
rely on the agent. The rules are strict about linking and about never
overwriting a contradiction, because those two are what separate a vault that
compounds from a folder of summaries.

The template lets the agent work without asking first, and pairs that with
rails: a git checkpoint before any destructive step, archive instead of delete,
a change log in `wiki/log.md`, and a hard stop before anything private leaves
the vault. Read the Autonomy section before you schedule anything. The vault
must be a git repository for the checkpoints to work.

```
raw/        what arrives, by source: clippings, youtube, meetings, workspace, ai-chats, inbox
wiki/       the agent's pages: sources, entities, concepts, synthesis, hubs,
            self-improvement (ideas, experiments, reviews), systems
journal/    your own entries, read-only for the agent
projects/   one folder per project, each with its own CLAUDE.md
output/     generated drafts and reports
archive/    retired pages, never deleted
templates/  page templates
```

Delete the domains you do not need, and rewrite the language and routing
sections if your sources differ.
