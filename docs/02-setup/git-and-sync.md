# Git, sync and backups

A vault is a folder of text files, which makes it close to an ideal git
repository, and git is what makes an agent safe to run unattended.

Without version control, a bad run is a mystery. With it, every change the agent
made is a diff you can read and revert in one command.

```bash
cd ~/brain
git init
git add .gitignore CLAUDE.md README.md templates wiki projects output journal archive raw .obsidian \
  .claude/settings.json .claude/hooks .claude/skills .claude/commands .claude/agents scripts
git commit -m "Initial vault"
```

The vault must be its own repository, not a folder inside another one. The
[vault template](../../vault-template/README.md) uses the explicit-path first
commit above instead of `git add .`, so nothing you have not looked at is
committed. It includes `.claude/` (settings, hooks, skills, commands, agents) and `scripts/`
(the six vault scripts the Quickstart copies, not the site builders), the
vault's agent setup, which is worth versioning so a revert covers it too. `raw`
is included so the empty subfolders are tracked.

The template's `.claude/settings.json` and `.claude/hooks/guard.py` block pushes,
deletion, changes to existing `raw/` files, and writes to `journal/`, `scripts/`
and `.claude/` before they run; commit them so
a revert restores them too. See
[what is enforced](../../vault-template/README.md#what-is-enforced-and-what-is-not).

The template's `.gitignore` already covers the list below plus `raw/workspace/`,
where email, chat, docs and calendar pulls land. Its agent will
not run `git init` for you; if the vault is nested in another repository it
queues the problem for you instead.

## What to ignore

```
.obsidian/workspace*
.obsidian/cache
.DS_Store
.trash/
```

Commit the rest of `.obsidian/`, so your plugin list and settings travel with
the vault. Never commit API keys; the Local REST API key lives in plugin data,
so check what `.obsidian/plugins/` contains before the first push.

If any part of the vault is private, keep the remote private. A second brain is
one of the highest-signal documents about a person that exists.

## Commit around agent runs

Commit before a big ingest and after it. Then a bad batch is a revert of one
commit rather than an afternoon of manual repair. Scheduled tasks should commit
their own work, by path and not with `git add -A`, with a message naming the
run, so the history stays readable months later and a revert leaves your own
edits alone.

## Sync across machines

- **Git remote:** free, versioned, works everywhere, needs a pull and push
  habit.
- **[Obsidian Sync](https://help.obsidian.md/sync):** a paid add-on, end-to-end encrypted by default
  ([security and privacy](https://help.obsidian.md/sync/security)), with mobile support.
- **Generic cloud drives:** work, with a caveat. A sync client rewriting files
  while an agent writes them produces conflict copies. If you go this route,
  keep long-running agent work to one machine.

## Backups

Sync is not backup. Sync propagates a bad delete to every device.

Keep one copy that is not connected to the sync path: a periodic archive to
external storage or a separate remote. Test a restore once, before you need it.
The failure mode you are protecting against is not disk death, it is an
automation that quietly rewrote two hundred pages three weeks ago.

## Next

The vault is set up. Go to [Ingestion](../03-ingestion/README.md) to start
feeding it, or [Structuring](../04-structuring/README.md) for the rules that
decide what the pages look like.
