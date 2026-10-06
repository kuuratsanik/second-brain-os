---
title: Vault operating notes
type: system
status: draft
domain: [systems]
lang: en
sensitivity: normal
maintained_by: agent
created:
updated:
aliases: [Operating notes]
tags: [vault]
---

# Vault operating notes

How this vault is run. The rules live in `CLAUDE.md`; this page holds what the
owner chooses within them, and the agent updates it when a run changes a
setting. The agent proposes changes to `CLAUDE.md` in its run report; the only
part of that file it may edit is the Profile block, with answers the owner gave
in a live session.

## Schedule

Defaults. Replace them with real times once each job has been run by hand for a
week. TODO(interview): preferred time of day for the daily run and the weekly
review.

| Job | Cadence | Scheduled? |
|---|---|---|
| Ingest raw material (20 oldest pending per run); pull new Granola meetings | Daily | No |
| Link, lint, weekly review, calendar snapshot | Weekly | No |
| Metrics, archive pass, experiment review, tag check | Monthly | No |

## Standing rules for connected services

What the agent may pull without being asked. Pulling is read only. The Granola
and calendar rows match the schedule above. Change a row to change the
behaviour.

| Service | Pulled without being asked | Default |
|---|---|---|
| Granola | All new meetings | yes |
| Google Calendar | The week's events, for the weekly review | yes |
| Gmail | Threads matching a rule the owner lists here | no rules yet |
| Slack | Channels the owner lists here | no rules yet |
| Notion | Areas the owner lists here | no rules yet |
| Google Drive | Folders the owner lists here | no rules yet |

TODO(interview): rules for Gmail, Slack, Notion and Drive.

## Settings the owner can change

- Active experiments before the agent flags it: 3
- Archive pass: pages with one source and no inbound links after a year, and
  stubs never filled
- Pending raw items taken per scheduled ingest: 20

Part of [[hub-systems|Systems]]. Unresolved items are in [[needs-owner]].
