---
title: Needs owner
type: system
status: active
domain: [systems]
lang: en
sensitivity: normal
maintained_by: agent
created:
updated:
aliases: [Queue for the owner]
tags: [vault]
---

# Needs owner

Items the agent skipped because they hit a hard stop in `CLAUDE.md`, or because
git was not ready for a destructive step. Scheduled runs cannot ask questions,
so they write here and carry on with the rest.

Each entry: date, what, why it stopped, and what the agent needs from the
owner. Before adding an entry, the agent searches Waiting for the same path or
item and updates that entry's date instead of adding a second. A checkpoint that
keeps failing (for example no git identity) is one entry with the git error.
The owner resolves an entry by answering it; the agent then moves it to Done
with the outcome. Nothing is removed from this page.

## Waiting

_Nothing yet._

## Done

_Nothing yet._

Part of [[hub-systems|Systems]].
