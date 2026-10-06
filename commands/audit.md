---
description: Audit what an agent did
argument-hint: "[period]"
disable-model-invocation: true
---

Audit the period in $ARGUMENTS, defaulting to seven days. Read `log.md` and `git log --stat` for the period. Report what ran, which commits belong to which run, what each changed, and anything that changed without a log entry or without a run commit. Separate the owner's own commits and edits from the agent's. Report only; to undo a run use `/rollback`.
