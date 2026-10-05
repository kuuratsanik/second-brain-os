---
description: Undo one run, leaving your own edits alone
argument-hint: "[run id]"
disable-model-invocation: true
---

Roll back the run named in $ARGUMENTS, or the most recent run commit if none is given. Show what it changed, checkpoint first, revert only that run's own commit or paths on confirmation, and record the rollback in `log.md`. Never touch the owner's unrelated edits. To undo your own edit, use git directly; `/audit` shows what a run changed without undoing it.

Follow the `second-brain-rollback` skill.
