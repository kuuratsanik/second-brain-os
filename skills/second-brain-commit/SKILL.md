---
name: second-brain-commit
description: >-
  Commit what a run or session wrote to the vault's git history: stage only the
  paths that run changed, by explicit path, write a message that names the run
  and lists the paths, and leave the owner's own edits, ignored files and
  anything holding a secret out. Use this skill whenever the user asks to
  commit, save a checkpoint or version the vault, at the end of a maintenance
  run, or when a scheduled commit task fires. Do NOT use to push, to rewrite
  history, or to undo a run, which is second-brain-rollback.
---

# Commit a run

A commit is only useful as an undo point if it contains exactly what one run
changed. A commit that also holds the owner's half-written notes cannot be
reverted without losing them.

## Core rule

Stage by explicit path, only paths this run wrote. Never `git add -A`, never
`git add .`, never `git commit -a`. Commit locally and stop: pushing is not part
of this skill.

## Workflow

1. **Check the repository.** Run `git rev-parse --show-toplevel`. If it fails
   (no git) or prints a folder other than the vault, do not run `git init` and
   do not commit into the outer repository. Report what you would have
   committed, queue the problem for the owner (`wiki/systems/needs-owner.md` if
   the vault has it, otherwise in the report), and stop. Creating a repository
   is the owner's decision.
2. **Find the run's paths.** Take them from what this run created, edited,
   moved or archived, and from its `log.md` lines. Then run
   `git status --porcelain` and compare. A path that the owner also edited
   in the same session is listed in the report as mixed, not hidden. Anything
   modified that this run did not touch is the owner's: leave it unstaged and list it in the report. If you
   cannot tell whose a change is, leave it out.
3. **Cut the list.** Remove, whatever the run did:
   - anything under `raw/workspace/`;
   - anything git ignores (`git check-ignore -v <path>`);
   - editor state such as `.obsidian/workspace*`;
   - any file in which this run, or a privacy or secrets scan, found a credential
     or token. Never stage it. Name the file and the kind, never the value, and
     queue it.
   A path inside a nested repository (a folder with its own `.git`) is not the
   vault repository's to stage. Report it and leave it.
4. **Check the index, then stage by path.** Run `git diff --cached --name-only`
   first. If it is not empty, the owner staged something: leave it alone, make
   no commit, and queue it (`wiki/systems/needs-owner.md` if the vault has it,
   otherwise the report). Then `git add -- <path> <path> ...`. For a moved or
   archived page, list both the old and the new path, or the deletion is left behind.
5. **Write the message.** The subject is the run id, `run-YYYY-MM-DD-<job>`,
   for example `run-2026-10-05-ingest`. Use the date the run started and a short
   job name (`ingest`, `link`, `lint`, `review`, `archive`). For a manual
   session with no named job, use `manual`. If that id already exists in
   `git log`, append `-2`. The body is the path list, one path per line, then one
   line of counts (created, updated, archived). Another skill finds a run's
   commit by that subject, so keep it first.
6. **Commit the index.** `git commit -m "<message>"`, with no path list and no
   `-a`. Check `git diff --cached --name-only` is exactly the run's paths.
   Committing `-- <path>` would take the working-tree contents and sweep in
   owner edits made after the run. Only in a live session, and only as a
   fallback if something extra got staged, unstage it with
   `git restore --staged -- <path>`; that may prompt for approval in the vault's
   settings, which is expected. In a scheduled run, stop and queue instead. If it
   fails (no identity, a hook), report the git error and stop. Do not change git
   config, do not use `--no-verify`, do not amend.
7. **Report.** Commit hash, path count, `git show --stat` summary, and the
   paths you left out with the reason for each.

## Output format

```
Commit: <hash> run-2026-10-05-ingest
Paths: <n> (<n> created, <n> updated, <n> moved)
Left unstaged: <path - owner's edit | ignored | nested repo>
Withheld: <path - credential found, kind>
```

## Calibration

When the run wrote nothing, say "nothing to commit" and make no commit.

If the owner asks for "commit everything", stage by path anyway, listing every
path from `git status`, minus the cut list above. The owner's edits may be
included when they ask for them by name, never by default.

A vault with no git at all is a legitimate state, not an error to fix. Report
it once and stop.
