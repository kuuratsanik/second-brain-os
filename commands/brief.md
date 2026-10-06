---
description: Brief of what needs your attention in the vault
argument-hint: "[since date]"
---

Write a brief of what needs the owner: raw sources added since the last brief (from `wiki/log.md`, or since $ARGUMENTS if given), the needs-owner queue, experiments and ideas due, stale pages from `scripts/link_check.py . --stale 90`, likely duplicates, and the path of the dashboard from `scripts/dashboard.py`. Report only; the only files written are `output/brief-<date>.md`, `output/dashboard.html` and one log line. If the vault has no `scripts/` folder (the kit is installed as the `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/` versions of those scripts instead; Claude Code fills in that path only for a plugin install. This command can be scheduled. To act on what it lists use `/ingest`, `/experiment-review`, `/stale` and `/dedupe`.

Follow the `second-brain-brief` skill.
