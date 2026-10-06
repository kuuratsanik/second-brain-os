---
description: Propose scheduled maintenance for this vault
disable-model-invocation: true
---

Propose a schedule for ingest, link, lint and review with the right cadence
for this vault's volume, where each should run (cloud, desktop or headless),
and the exact prompt for each task. Schedule only the maintenance commands
(`/ingest`, `/link`, `/lint`, `/vault-review`, `/weekly`, `/monthly`, `/metrics`,
`/health`, `/brief`, `/commit`, `/stale`, `/orphans`, `/prune`, `/archive`, `/dedupe`,
`/backfill`, `/index`); the other commands cannot be fired by a scheduled task,
so give those a plain-language prompt instead. Propose only; the owner creates
the tasks.

Follow the `second-brain-schedule` skill.
