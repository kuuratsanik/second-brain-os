---
name: second-brain-doctor
description: >-
  Check that a second-brain vault is set up correctly and report what is
  missing or wrong: CLAUDE.md, the folder layout, the scripts, git state,
  .gitignore, installed skills, commands and agents, and connectors the vault
  refers to but that are not connected. Use this skill whenever the user asks
  whether their setup works, after installing the kit, when a command or skill
  does not behave as expected, or before scheduling anything. Do NOT use to fix
  what it finds, to audit page content, which is second-brain-lint, or to scan
  for secrets, which is second-brain-privacy.
---

# Check the setup

Most "the agent is not doing what I set up" problems are a missing file, a
skill that did not get copied, or a repository that is not where the agent
thinks it is.

## Core rule

Read-only. Report what is wrong and the command or edit that would fix it, and
change nothing. Do not run `git init`, install files or edit `CLAUDE.md` here.

## Workflow

Run every check, then report all of them, including the ones that pass.

1. **CLAUDE.md.** Present at the vault root and not empty. Count remaining
   `TODO(interview)` lines in it: they mean the profile was never filled in.
   Note whether it has an Autonomy section or other explicit grant to act without
   asking, because that decides how every other skill behaves.
2. **Folders.** `raw/`, `wiki/` with `sources/`, `entities/`, `concepts/` and
   `synthesis/`, `projects/`, `output/`, `archive/`, `templates/`, and
   `index.md` and `log.md` (in `wiki/` in the template vault, at the root in
   others). `journal/` is optional. Report extra top-level folders as
   information only.
3. **Scripts.** `scripts/vault_stats.py`, `link_check.py`, `graph_export.py`
   and `chat_export_to_md.py` exist, and `python3 --version` runs (`python` on
   Windows). Do not run the scripts on the vault; existence and an interpreter
   are the check.
4. **Git.** `git rev-parse --show-toplevel` equals the vault folder (not no
   repository, not a parent repository). Then: current branch, whether commits
   exist, `git config user.name` and `user.email` set, count of uncommitted
   paths, and any remotes with their URLs. A remote is information, not an
   error; say whether the vault holds `private` or `restricted` pages if
   `CLAUDE.md` says so, because that is the owner's call to make.
5. **.gitignore.** Exists, contains `raw/workspace/` and editor state
   (`.obsidian/workspace*`). Check `git ls-files raw/workspace` for files that
   were committed before the rule existed.
6. **Skills, commands, agents.** Look in `.claude/` in the vault and in
   `~/.claude/`. Every `second-brain-*` skill must be a folder holding
   `SKILL.md` whose `name` matches the folder. Every skill named in an installed
   command or agent must be installed. A `README.md` inside `.claude/commands/`
   or `.claude/agents/` is a defect: it becomes a `/README` command or agent.
   Report skills present in the kit but not installed.
7. **Connectors.** Collect the services the vault refers to, from `CLAUDE.md`,
   `wiki/systems/vault-operating-notes.md` and `wiki/systems/routing.md` (mail,
   chat, calendar, documents, meeting notes, any named service) and from
   `raw/workspace/` subfolders. Compare against the connectors and MCP servers
   available in this session (`.mcp.json`, `claude mcp list`, or the tool list).
   Report each service referred to and not connected. Do not call a connector to
   test it.
8. **Say what you could not check**, such as scheduled tasks, which live outside
   the vault.

## Output format

```
Setup check: <path>

OK       <check>
WARN     <check> - <what is off> -> <fix>
MISSING  <check> - <what is absent> -> <fix>

Connectors referred to, not connected: <list | none>
Not checked: <list>

<n> ok, <n> warnings, <n> missing. Fix first: <the one that blocks the most>
```

## Calibration

Name the single most blocking problem rather than a flat list of twelve. A
missing `CLAUDE.md` or a vault not in its own git repository outranks a missing
optional folder.

Never print a credential if you see one while checking `.mcp.json` or the
environment: name the file and say a key is present, nothing more.

A vault that deliberately has no git or no remote is not broken. Report the
state and what it means for checkpoints, and mark it WARN only.
