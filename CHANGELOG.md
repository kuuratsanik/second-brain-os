# Changelog

All user-facing changes to the kit that ships into your vault: the skills,
commands, agents, scripts and vault template, plus the agents-course plugin and
the guide. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

The kit version is the single line in [`skills/VERSION`](skills/VERSION). A vault
records the version it was installed from in `.claude/skills/VERSION`, and
[`/install`](commands/install.md) compares the two when you update.

## [Unreleased]

The entries below are the changes in 1.0.0, the first versioned release.
A vault installed before this release has no `.claude/skills/VERSION` and
counts as older than 1.0.0.

### Breaking

- **`/schedule` is now `/maintenance-schedule`.** A project command named
  `/schedule` would shadow Claude Code's built-in `/schedule`. Copying the new
  `commands/` folder into a vault adds `maintenance-schedule.md` but leaves the
  old `.claude/commands/schedule.md` in place, so delete that file. Anything of
  yours that calls `/schedule` (notes, scheduled tasks, other commands) needs
  the new name. The skill keeps its name, `second-brain-schedule`.
- **Most commands are manual-only.** 56 commands now set
  `disable-model-invocation: true` and run only when you type them. The 16
  maintenance commands (`/ingest`, `/link`, `/lint`, `/review`, `/weekly`,
  `/monthly`, `/metrics`, `/health`, `/commit`, `/stale`, `/orphans`, `/prune`,
  `/archive`, `/dedupe`, `/backfill`, `/index`) stay schedulable. A scheduled
  task that fires any other command no longer runs it.
- **Merge and import archive instead of deleting.** Merging moves the merged
  page to `archive/`, and imports skip a duplicate instead of removing it.
  `/prune` and `/archive` propose, and move pages only if your `CLAUDE.md`
  grants autonomy. If you relied on deletion, say so in your `CLAUDE.md`.

### Skills, commands and agents

- Added six skills, 24 in total: `second-brain-commit`, `second-brain-rollback`,
  `second-brain-doctor`, `second-brain-schedule`, `second-brain-archive` and
  `second-brain-structure`.
- Every command now points at a skill that does its job, or carries its own
  instructions. Added `argument-hint` to every command that takes an argument.
- Near-duplicate commands (`/ask`, `/know`, `/trace`; `/contradictions`,
  `/contradicts`; `/health`, `/graph`, `/metrics`, `/monthly`) say when to use
  their sibling.
- `/rollback` undoes one run and keeps your own edits. It never touches `raw/`,
  `journal/` or `output/`.
- Every maintenance skill ends with a run commit that stages files by path.
  Archive moves use `git mv`; restoring a page is an owner step.
- Trimmed skill introductions and rewrote trigger descriptions so that two
  skills no longer claim the same request.
- `graph-analyst` runs on a smaller model.
- `/install` now also updates an existing vault: it compares versions, shows
  the entries in this file, and lists the copy commands for you to run. It
  never overwrites your `CLAUDE.md` or `.claude/settings.json`.

### Vault template

- Six domains with hubs (work, learning, personal, creative, self-improvement,
  systems) and a self-improvement lifecycle.
- One `raw/` folder per source, and mixed-language rules with ASCII slugs.
- Autonomy rails: a checkpoint commit before destructive steps, archive instead
  of delete, a change log in `wiki/log.md`, and a needs-owner queue.
- Hard stops are enforced, not only requested. `.claude/settings.json` carries
  deny, ask and allow rules, and `.claude/hooks/guard.py` is a PreToolUse and
  Stop hook that blocks writes to existing `raw/` files, `journal/`, `scripts/`
  and `.claude/`, deletes, pushes, uploads and unsafe git forms. The template
  README lists what stays prompt-only.
- A `.gitignore` keeps email, chat and document intake out of git.
- A slimmer `CLAUDE.md` (about 1,600 words) with an empty Profile block that the
  interview fills in.
- Not updated for you: `/install` never overwrites `CLAUDE.md`,
  `.claude/settings.json` or `.claude/hooks/`. Compare them with the template
  by hand if you want the new rules.

### Scripts

- ChatGPT exports in the `mapping` shape produced nothing; they are now read by
  walking the conversation tree.
- A UTF-8 byte order mark hid a page's frontmatter; fixed.
- Aliases are now counted in `vault_stats.py` and the graph export.
- `[[folder/Page]]` resolved to the wrong page when two pages shared a name;
  it now resolves by path.
- `vault_stats.py` parses its arguments with `argparse`.
- Added unit tests for the four vault scripts, and a fictional demo vault in
  `examples/demo-vault/` that you can run them against.

### Plugin

- `agents-course` 0.3.0. The two audit skills (`context-audit`,
  `harness-audit`) now block `Edit`, `Write` and `NotebookEdit` while they run,
  so "read-only" is enforced rather than promised.
- `goal-test`: the loop script caps each attempt with `--max-turns` and
  `--max-budget-usd`, and explains what `acceptEdits` does and does not allow
  in a headless run.
- `evals-bootstrap`: notes that Claude Code's transcript format is internal and
  changes between versions, so convert it in one place.
- Clearer wording in `gate-check` and `context-audit`.

### Docs and site

- The Quickstart sets up git and the guide pages match the template.
- Safety and scheduling pages cover real enforcement, the `acceptEdits`
  permission mode for unattended runs, and why template vaults should not use
  cloud routines.
- Resource counts refreshed as of 2026-10-05, with one stamp for sources that
  could not be re-checked. Added alt text for the course figures.
- The site is built by one command (`python3 scripts/build_all.py`), is checked
  in CI, and carries sharing tags, a sitemap and a 404 page. The upstream
  analytics beacon is removed, and links point to this fork.
- Added a repository `CLAUDE.md` and a kit checker (`tools/check_kit.py`) that
  validates the skills, commands, agents and plugin manifests.
