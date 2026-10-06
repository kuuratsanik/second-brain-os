---
title: Vault operating notes
type: system
status: active
domain: [systems]
lang: en
sensitivity: normal
maintained_by: agent
created: 2026-08-13
updated: 2026-10-04
aliases: [Operating notes]
tags: [vault]
---

# Vault operating notes

> Fictional. This page belongs to the demo vault; the people, organisations and articles in it are invented.

How this vault is run. The rules live in `CLAUDE.md`; this page holds what the
owner chooses within them, and the agent updates it when a run changes a
setting. The agent proposes changes to `CLAUDE.md` in its run report; the only
part of that file it may edit is the Profile block, with answers the owner gave
in a live session.

## Schedule

Set on 2026-08-20, after each job had been run by hand for a week. The owner
asked for the weekly pass on Sunday evening, after the Friday review, and the
monthly pass on the first Sunday.

| Job | Cadence | Scheduled? |
|---|---|---|
| Ingest raw material (20 oldest pending per run); pull new Granola meetings | Daily, 07:30 | Yes |
| Link, lint | Weekly, Sunday 18:00 | Yes |
| Metrics, archive pass, experiment review, tag check | Monthly, first Sunday 18:00 | Yes |

The weekly review itself is the owner's [[friday-review]]; the Sunday job only
lints and links.

## Standing rules for connected services

What the agent may pull without being asked. Pulling is read only. Change a row
to change the behaviour.

| Service | Pulled without being asked | Default |
|---|---|---|
| Granola | All new meetings | yes |
| Google Calendar | Not used; the owner has no calendar snapshots | no |
| Gmail | Threads matching a rule the owner lists here | no rules yet |
| Slack | Channels the owner lists here | no rules yet |
| Notion | Areas the owner lists here | no rules yet |
| Google Drive | Folders the owner lists here | no rules yet |

The Q4 planning meeting of 2026-09-22 came in under the Granola rule.

## Settings the owner can change

- Active experiments before the agent flags it: 3
- Archive pass: pages with one source and no inbound links after a year, and
  stubs never filled
- Pending raw items taken per scheduled ingest: 20

Part of [[hub-systems|Systems]]. Unresolved items are in [[needs-owner]].
