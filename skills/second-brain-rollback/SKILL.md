---
name: second-brain-rollback
description: >-
  Undo one maintenance run in a vault: find the run's commit, show what it
  changed, checkpoint the current state, revert only that commit's paths, keep
  the owner's unrelated edits untouched, record the rollback in the log, and
  report. Use this skill whenever the user says a run went wrong, asks to undo
  or roll back the last ingest, merge, archive or lint, or asks to revert a
  named run. Do NOT use for undoing the owner's own edits, for restoring one
  deleted file, or to rewrite or discard git history.
---

# Roll back a run

A bad run is cheap to undo only when each run is one commit and the undo
touches nothing else. The owner may have edited the same vault since.

## Core rule

Revert one run, by its commit or its paths, after a checkpoint, with the owner's
confirmation. Never touch a path the run did not change. Never reset, clean,
force or rewrite history.

## Workflow

1. **Find the run.** If the owner named a run id, use it. Otherwise list recent
   run commits with `git log --grep='^run-' -n 10 --format='%h %ad %s' --date=short`
   and take the newest. If the newest is ambiguous (several the same day), show
   the list and ask which. A commit whose message starts `checkpoint:` or
   `rollback` is not a run.
2. **Show it.** `git show --stat <hash>` and the path list from the message.
   Say which files the revert would remove from the working tree (files the run
   created), and which would return to an earlier state. Check later commits and
   uncommitted changes on those paths (`git log <hash>..HEAD -- <paths>`,
   `git status --porcelain -- <paths>`). A later run or an owner edit on the
   same path means reverting would undo that too: name each path and let the
   owner decide per path.
3. **Confirm.** Ask before changing anything. Rollback is never part of a
   scheduled run, and nothing in a scheduled run can approve it.
4. **Checkpoint.** If any of the run's paths have uncommitted changes, ask the
   owner whether to keep them; commit them by path as
   `checkpoint: rollback <run id>` so the rollback itself can be undone. If
   there are none, HEAD is the checkpoint.
5. **Revert.** `git revert --no-commit <hash>`. If it conflicts on a path, run
   `git revert --abort` and fall back to the paths that revert cleanly, using
   `git restore --source=<hash>^ --staged --worktree -- <path>` for each one.
   Report the paths you could not revert. Keep the run's lines in `log.md`:
   restore it to its pre-revert state with
   `git restore --source=HEAD --staged --worktree -- <log path>` so the audit
   trail survives.
6. **Log.** Append one line to `log.md`:
   `YYYY-MM-DD rollback run-... (<n> paths; checkpoint <hash>)`.
7. **Commit by path** with the second-brain-commit rules:
   `rollback run-2026-10-05-ingest`, the path list in the body, never `-A`.
8. **Report.**

## Output format

```
Rolled back: run-2026-10-05-ingest (<hash>)
Reverted: <n> paths (<n> files removed, <n> restored)
Checkpoint: <hash | HEAD>
Not reverted: <path - later change by owner or later run>
Not undoable: <paths git does not track, such as raw/workspace/>
```

## Calibration

Files that git ignores, such as `raw/workspace/`, are not in any run commit and
cannot be rolled back. Say so rather than implying the vault is back to its
earlier state.

A revert removes pages the run created from the working tree; they stay in git
history. Never delete anything in `raw/`, `journal/` or `output/` as part of a
rollback, even if the run commit contains it: list it and ask.

If nothing in the history looks like a run commit, say so. Do not guess a
commit from its date.
