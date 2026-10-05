---
description: Install the skills, commands and agents, or update an installed vault
argument-hint: "[path to checkout]"
disable-model-invocation: true
---

Install or update the kit in this vault. Ask for the path of the `second-brain-os` checkout if it is not given as $ARGUMENTS, and call it `$KIT` below. Do not copy the folder README.md files, since a README in `.claude/commands/` becomes a `/README` command.

Who runs the copy: in a vault with the template's guard hook, writes to `.claude/` and `scripts/` are blocked for the agent. There the owner runs every copy command in a terminal, and you list the exact commands and do not run them. Elsewhere, show the commands and run them only after the owner agrees.

## First install

If the vault has no `.claude/skills/` folder, copy the skills, commands and agents into `.claude/`, and the scripts into `scripts/`, so they are versioned with the notes. Report what was installed and what already existed. The commands are the Quickstart's, plus the version file:

```bash
mkdir -p .claude scripts
cp -r "$KIT"/skills   .claude/skills
cp -r "$KIT"/commands .claude/commands && rm .claude/commands/README.md
cp -r "$KIT"/agents   .claude/agents
cp "$KIT"/scripts/{chat_export_to_md,graph_export,link_check,vault_stats}.py scripts/
```

`.claude/skills/VERSION` comes with the skills folder. It records the kit version this vault was installed from.

## Update an installed vault

Use this when `.claude/skills/` exists. Change nothing until step 5.

1. **Compare versions.** Read `$KIT/skills/VERSION` and `.claude/skills/VERSION`. A vault without the file was installed before versioning and counts as older than 1.0.0. If they are equal, say the vault is current and stop. If the vault's version is higher, say the checkout is older and ask the owner to update it (`git -C "$KIT" pull`); stop.
2. **Show what changed.** Read `$KIT/CHANGELOG.md` and quote every section newer than the vault's version, plus `[Unreleased]`, in full. Lead with any **Breaking** entries and say what each one asks the owner to do. If the checkout has no `CHANGELOG.md`, say so and rely on step 3.
3. **Show what would be copied.** Compare each folder and list new, changed and vault-only files:
   `diff -rq "$KIT"/skills .claude/skills`, the same for `commands`, `agents`, and `scripts` limited to the four vault scripts (`chat_export_to_md.py`, `graph_export.py`, `link_check.py`, `vault_stats.py`; the `build_*.py` files are site builders, not vault scripts). Ignore the folder README.md files. A changed file may hold the owner's own edits, so show a `diff -u` for any changed file the owner asks about. Vault-only files are the owner's own or were removed upstream: list them, never delete them, and name any the CHANGELOG says to remove (for example `.claude/commands/schedule.md`).
4. **Compare the protected files, read-only.** Run `diff -u "$KIT"/vault-template/.claude/settings.json .claude/settings.json` and the same for `.claude/hooks/guard.py` and `CLAUDE.md`. Summarise the differences and say which CHANGELOG entries explain them. These files hold the owner's own rules and boundaries, so the update never copies over them: the owner merges any wanted change by hand.
5. **List the commands for the owner to run**, in this order, with `$KIT` filled in and the vault root as the working directory. The first checkpoints the vault so the update is one revertible commit:

```bash
git status --short            # commit or stash your own changes first
cp -r "$KIT"/skills/second-brain-* .claude/skills/
cp "$KIT"/commands/*.md .claude/commands/ && rm .claude/commands/README.md
cp "$KIT"/agents/*.md .claude/agents/ && rm .claude/agents/README.md
cp "$KIT"/scripts/{chat_export_to_md,graph_export,link_check,vault_stats}.py scripts/
rm -f .claude/commands/schedule.md      # renamed to /maintenance-schedule in 1.0.0
cp "$KIT"/skills/VERSION .claude/skills/VERSION
git diff --stat
git add .claude/skills .claude/commands .claude/agents scripts
git commit -m "Update the kit to $(cat .claude/skills/VERSION)"
```

   Tell the owner to read `git diff` before the commit and to restore any file where their own edits were overwritten (`git restore <path>`). Drop the `rm -f` line if the update is from 1.0.0 or later. Add a line for each other removal the CHANGELOG names.
6. **Never write these**, in any mode: `CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/`, `raw/` and `journal/`. If a CHANGELOG entry asks for a change to one of them, describe the change and leave it to the owner.

When the owner reports the commands have run, check `.claude/skills/VERSION` against `$KIT/skills/VERSION` and run `/doctor` to confirm the setup.
