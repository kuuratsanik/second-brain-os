---
description: Install the skills, commands and agents, or update an installed vault
argument-hint: "[path to checkout]"
disable-model-invocation: true
---

Install or update the kit in this vault. Ask for the path of the `second-brain-os` checkout if it is not given as $ARGUMENTS, and call it `$KIT` below. Do not copy the folder README.md files, since a README in `.claude/commands/` becomes a `/README` command.

Who runs the copy: in a vault with the template's guard hook, writes to `.claude/` and `scripts/` are blocked for the agent. There the owner runs every copy command in a terminal, and you list the exact commands and do not run them. Elsewhere, show the commands and run them only after the owner agrees.

## Installed as a plugin

If the owner installed the kit as the `second-brain` plugin (`~/.claude/plugins/installed_plugins.json` has a `second-brain@second-brain-os` entry), this command does not apply to the skills, commands and agents: they live outside the vault. Do not copy them into `.claude/`, since the vault would then load each one twice. Tell the owner to update with `claude plugin update second-brain@second-brain-os`, then `/reload-plugins` or a new session. The version is the one in `$KIT/skills/VERSION`; `claude plugin update` finds nothing new until the kit bumps it. Still read the CHANGELOG entries since the plugin's version for them, and compare the protected files as in step 4 below. The four scripts are the one part that is copied into the vault, so for those, follow steps 3 and 5.

## First install

If the vault has no `.claude/skills/` folder, copy the skills, commands and agents into `.claude/`, and the scripts into `scripts/`, so they are versioned with the notes. Report what was installed and what already existed. These commands match the Quickstart, except that they drop the folder README files and copy only the four vault scripts:

```bash
mkdir -p .claude scripts
cp -r "$KIT"/skills   .claude/skills   && rm .claude/skills/README.md
cp -r "$KIT"/commands .claude/commands && rm .claude/commands/README.md
cp -r "$KIT"/agents   .claude/agents   && rm .claude/agents/README.md
cp "$KIT"/scripts/{chat_export_to_md,graph_export,link_check,vault_stats}.py scripts/
```

`.claude/skills/VERSION` comes with the skills folder. It records the kit version this vault was installed from.

## Update an installed vault

Use this when `.claude/skills/` exists. Change nothing until step 5.

1. **Compare versions.** Read `$KIT/skills/VERSION` and `.claude/skills/VERSION`; a missing vault file means 0.0.0, before versioning. Newest of the two:

   ```bash
   printf '%s\n' "$(cat .claude/skills/VERSION 2>/dev/null || echo 0.0.0)" "$(cat "$KIT"/skills/VERSION)" | sort -V | tail -1
   ```

   If the vault's version is the newest (equal or higher), say the vault is current, or that the checkout is older and needs `git -C "$KIT" pull`; stop.
2. **Show what changed.** Read `$KIT/CHANGELOG.md`. Quote, in full, every `## [x.y.z]` section whose version is newer than the vault's (use `sort -V` to compare), newest first, and `## [Unreleased]` if it has entries. Lead with the entries marked **Breaking** and say what each asks the owner to do. If there is no CHANGELOG, say so and rely on step 3.
3. **Show what would be copied.** Run `diff -rq "$KIT"/skills .claude/skills`, the same for `commands` and `agents`, and for `scripts` limit it to the four vault scripts (`chat_export_to_md.py`, `graph_export.py`, `link_check.py`, `vault_stats.py`; the `build_*.py` files are site builders). Ignore the folder README.md files. List new files, changed files and vault-only files.
   - **Flag customised files.** For each changed file, run `git log --oneline -1 -- <path>` in the vault and `git status --short -- <path>`. A file that has been committed or edited since the install commit, or that has uncommitted changes, is probably the owner's own edit: mark it **customised** and offer a `diff -u` of it against the checkout. A file with no history of its own (copied in once) is stock.
   - **Vault-only files** are the owner's own or were removed upstream. Never delete them; name any the CHANGELOG says to remove (for example `.claude/commands/schedule.md`).
4. **Compare the protected files, read-only.** Run `diff -u "$KIT"/vault-template/.claude/settings.json .claude/settings.json`, and the same for `.claude/hooks/guard.py` and `CLAUDE.md`. Summarise the differences and say which CHANGELOG entries explain them. These files hold the owner's own rules and boundaries, so the update never copies over them: the owner merges any wanted change by hand.
5. **List the commands for the owner to run**, in this order, with `$KIT` filled in and the vault root as the working directory. The first one commits the vault as it is, so the update is a separate commit you can revert:

   ```bash
   git add -A && git commit -m "Before kit update"      # skip if "git status --short" is empty
   cp -r "$KIT"/skills/second-brain-* .claude/skills/
   cp "$KIT"/commands/*.md .claude/commands/ && rm .claude/commands/README.md
   cp "$KIT"/agents/*.md .claude/agents/ && rm .claude/agents/README.md
   cp "$KIT"/scripts/{chat_export_to_md,graph_export,link_check,vault_stats}.py scripts/
   rm -f .claude/commands/schedule.md      # renamed to /maintenance-schedule in 1.0.0
   cp "$KIT"/skills/VERSION .claude/skills/VERSION
   git diff --stat
   ```

   The copy overwrites every file that exists in both places, including the customised ones from step 3. Tell the owner to read `git diff` file by file before `git add`, and to keep their own version of a file with `git restore <path>` (the checkpoint commit holds it). Only then:

   ```bash
   git add .claude/skills .claude/commands .claude/agents scripts
   git commit -m "Update the kit to $(cat .claude/skills/VERSION)"
   ```

   Drop the `rm -f` line if the vault is already on 1.0.0 or later, and add a line for each other removal the CHANGELOG names.
6. **Never write these**, in any mode: `CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/`, `raw/` and `journal/`. If a CHANGELOG entry asks for a change to one of them, describe the change and leave it to the owner.

When the owner reports the commands have run, check `.claude/skills/VERSION` against `$KIT/skills/VERSION` and run `/doctor` to confirm the setup.
