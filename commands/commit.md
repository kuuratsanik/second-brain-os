---
description: Commit what this run or session wrote, by path
---

Commit the paths this run or session wrote, using the `run-YYYY-MM-DD-<job>` message format with the path list. Stage by explicit path only. Never stage `raw/workspace/`, ignored files or files flagged as containing secrets. Report the diff summary and anything left unstaged. Local commit only; nothing is pushed.

Follow the `second-brain-commit` skill.
