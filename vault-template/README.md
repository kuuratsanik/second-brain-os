# vault-template

An opinionated starter vault, tuned for an agent that works without asking
first, for several life and work domains (work, learning, personal, creative,
self-improvement, systems), and for notes in more than one language. Anyone can
use it: it ships with no personal facts, and the interview fills in the
profile. Copy this folder somewhere on your machine, open it in Obsidian as a
vault, and start Claude Code inside it.

```bash
cp -r vault-template ~/brain
cd ~/brain
git init
git add .gitignore CLAUDE.md README.md templates wiki projects output journal archive raw/README.md
git commit -m "Initial vault"
claude
```

Do the git step once. The agent's safety rails (a checkpoint commit before any
destructive step, one commit per run) need the vault folder to be its own git
repository. If the vault sits inside another repository, the agent will not
create one and will queue the problem for you instead.

`CLAUDE.md` is the instruction sheet the agent reads every session. Read it
before your first run. Its Profile block is empty on purpose: fill it with the
interview from [the CLAUDE.md guide](../docs/02-setup/claude-md.md), in a live
session, before you rely on the agent. The rules are strict about linking and
about never overwriting a contradiction, because those two are what separate a
vault that compounds from a folder of summaries.

Read the Autonomy section before you schedule anything. It lets the agent
ingest, merge and archive on its own, and limits that with rails: a checkpoint
before destructive steps, archive instead of delete, a change log in
`wiki/log.md`, and hard stops for writing to connected services, sending
personal data out, secrets and irreversible steps.

`.gitignore` keeps `raw/workspace/` (email, chat, docs, calendar) and editor
state out of git. Your journal and meeting transcripts are versioned unless you
uncomment their lines. Never push this vault to a remote without checking what
is in it.

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

Delete the domains you do not need, and edit `wiki/systems/routing.md` if your
sources differ.
