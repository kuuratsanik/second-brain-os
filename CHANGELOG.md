# Changelog

All user-facing changes to the kit that ships into your vault: the skills,
commands, agents and vault scripts, plus the vault template, the agents-course
plugin and the guide. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

The kit version is the single line in [`skills/VERSION`](skills/VERSION). It
covers the skills, commands, agents and vault scripts together; the
agents-course plugin is versioned separately, in its own `plugin.json`. A vault
records the kit version it was installed from in `.claude/skills/VERSION`, and
[`/install`](commands/install.md) compares the two when you update. A vault
without that file predates 1.0.0.

## [Unreleased]

## [1.0.0] - 2026-10-05

### Added

- Six skills, 24 in total: `second-brain-commit`, `second-brain-rollback`,
  `second-brain-doctor`, `second-brain-schedule`, `second-brain-archive` and
  `second-brain-structure`.
- `argument-hint` on every command that takes an argument.
- `/install` now also updates an installed vault. It compares versions, shows
  the entries in this file, flags files that differ from the checkout and
  that you may have customised (so you can keep your version), and lists the copy commands for you to run. It
  never overwrites your `CLAUDE.md` or `.claude/settings.json`.
- Vault template: six domains with hubs (work, learning, personal, creative,
  self-improvement, systems), a self-improvement lifecycle, one `raw/` folder
  per source, mixed-language rules with ASCII slugs, and a `.gitignore` that
  keeps email, chat and document intake out of git.
- Vault template autonomy rails: a checkpoint commit before destructive steps,
  archive instead of delete, a change log in `wiki/log.md` and a needs-owner
  queue.
- Unit tests for the four vault scripts, and a fictional demo vault in
  `examples/demo-vault/` that you can run them against.
- The site has a system, light and dark theme toggle, and carries sharing tags,
  a sitemap and a 404 page. Alt text for the course figures.
- Developer note: `tools/check_kit.py` validates `vault-template/.claude/settings.json`
  (valid JSON, known keys), as well as the skills, commands, agents and plugin
  manifests. CI runs it, the vault script tests and the guard hook tests.
  The site now builds with one command, `python3 scripts/build_all.py`, and CI
  fails on drift. Added a repository `CLAUDE.md`.

### Changed

- **Breaking:** `/schedule` is now `/maintenance-schedule`. A project command
  named `/schedule` would shadow Claude Code's built-in `/schedule`. Copying
  the new `commands/` folder adds `maintenance-schedule.md` but leaves the old
  `.claude/commands/schedule.md` in place, so delete that file. Anything of
  yours that calls `/schedule` (notes, scheduled tasks, other commands) needs
  the new name. The skill keeps its name, `second-brain-schedule`.
- **Breaking:** 56 commands are manual-only. They set
  `disable-model-invocation: true` and run only when you type them. The 16
  maintenance commands (`/ingest`, `/link`, `/lint`, `/review`, `/weekly`,
  `/monthly`, `/metrics`, `/health`, `/commit`, `/stale`, `/orphans`, `/prune`,
  `/archive`, `/dedupe`, `/backfill`, `/index`) stay schedulable. A scheduled
  task that fires any other command no longer runs it.
- **Breaking:** merge and import archive or skip instead of deleting. Merging
  moves the merged page to `archive/`, and imports skip a duplicate. `/prune`
  and `/archive` propose, and move pages only if your `CLAUDE.md` grants
  autonomy. If you relied on deletion, say so in your `CLAUDE.md`.
- **Breaking:** every maintenance skill now commits its run to git, staging
  files by path, and needs the vault to be a git repository. In a vault that is
  not one, the commit step stops and queues the problem for you; the run's
  edits stay uncommitted.
- `/rollback` undoes one run and keeps your own edits. It never touches `raw/`,
  `journal/` or `output/`. Archive moves use `git mv`; restoring a page is an
  owner step.
- Every command points at a skill that does its job, or carries its own
  instructions. Near-duplicate commands (`/ask`, `/know`, `/trace`;
  `/contradictions`, `/contradicts`; `/health`, `/graph`, `/metrics`,
  `/monthly`) say when to use their sibling.
- Skill introductions are trimmed and trigger descriptions rewritten so two
  skills no longer claim the same request. `graph-analyst` runs on a smaller
  model.
- The vault template's `CLAUDE.md` is slimmer (about 1,750 words), with an
  empty Profile block that the interview fills in. `/install` never overwrites
  it, `.claude/settings.json` or `.claude/hooks/`; compare them with the
  template by hand if you want the new rules.
- `agents-course` plugin 0.3.0: `context-audit` and `harness-audit` block
  `Edit`, `Write` and `NotebookEdit` while they run, so "read-only" is
  enforced. The `goal-test` loop caps each attempt with `--max-turns` and
  `--max-budget-usd` and explains what `acceptEdits` allows in a headless run.
  `evals-bootstrap` notes that Claude Code's transcript format is internal and
  changes between versions. Clearer wording in `gate-check` and `context-audit`.
- Docs: the Quickstart sets up git, the guide pages match the template, and the
  safety and scheduling pages cover real enforcement, `acceptEdits` for
  unattended runs, and why template vaults should not use cloud routines.
  Resource counts are refreshed as of 2026-10-05, with one stamp for sources
  that could not be re-checked. Links point to this fork.

### Removed

- The old `/schedule` command name (see Changed).
- The upstream analytics beacon and the stale roadmap page from the site.

### Fixed

- ChatGPT exports in the `mapping` shape produced nothing; they are now read by
  walking the conversation tree.
- A UTF-8 byte order mark hid a page's frontmatter in the vault scripts.
- Aliases are now counted in `vault_stats.py` and the graph export.
- `[[folder/Page]]` resolved to the wrong page when two pages shared a name; it
  now resolves by path.
- `vault_stats.py` parses its arguments with `argparse`.
- Site accessibility: contrast, landmarks, heading order, a skip link,
  keyboard-operable graph nodes and labelled controls.

### Security

- The template's hard stops are enforced, not only requested.
  `.claude/settings.json` carries deny, ask and allow rules, and
  `.claude/hooks/guard.py` is a PreToolUse and Stop hook that blocks writes to
  existing `raw/` files, `journal/`, `scripts/` and `.claude/`, deletes,
  pushes, uploads and unsafe git forms. The template README lists what stays
  prompt-only. To adopt this in an existing vault, copy the two files by hand;
  `/install` does not.
