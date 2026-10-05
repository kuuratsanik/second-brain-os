---
title: Vault operating notes
type: system
status: draft
domain: [systems]
lang: en
sensitivity: normal
created: 1970-01-01
updated: 1970-01-01
aliases: [Operating notes]
tags: [vault]
---

# Vault operating notes

How this vault is run. The rules live in `CLAUDE.md`; this page holds what the
owner chooses within them, and the agent updates it when a run changes a
setting. The agent never edits `CLAUDE.md` itself.

## Schedule

Defaults from `CLAUDE.md`. Replace with the real times once each job has been
run by hand for a week. TODO(interview): preferred time of day for the daily
run and the weekly review.

| Job | Cadence | Scheduled? |
|---|---|---|
| Ingest raw material, pull Granola meetings | Daily | No |
| Link, lint, weekly review | Weekly | No |
| Metrics, archive pass, experiment review | Monthly | No |

## Standing rules for connected services

Which Gmail threads, Slack channels, Notion areas and Drive folders the agent
may pull from without being asked. Empty means pull only on request.
TODO(interview).

## Settings the owner can change

- Active experiments before the agent flags it: 3
- Archive pass: pages with one source and no inbound links after a year, and
  stubs never filled
- Safety rails: see the Autonomy section of `CLAUDE.md`

Part of [[hub-systems|Systems]]. Unresolved items are in [[needs-owner]].
