---
description: Set up scheduled maintenance
disable-model-invocation: true
---

Propose a schedule for ingest, link, lint and review with the right cadence
for this vault's volume, and the exact prompt for each task. Schedule only the
maintenance commands (`/ingest`, `/link`, `/lint`, `/review`, `/weekly`,
`/monthly`, `/metrics`, `/health`, `/commit`, `/stale`, `/orphans`, `/prune`,
`/archive`, `/dedupe`, `/backfill`, `/index`); the other commands cannot be
fired by a scheduled task.

Follow the `second-brain-review` skill.
