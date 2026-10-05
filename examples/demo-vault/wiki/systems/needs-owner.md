---
title: Needs owner
type: system
status: active
domain: [systems]
lang: en
sensitivity: normal
maintained_by: agent
created: 2026-08-13
updated: 2026-10-04
aliases: [Queue for the owner]
tags: [vault]
---

# Needs owner

> Fictional. This page belongs to the demo vault; the people, organisations and articles in it are invented.

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

- **2026-10-04, secret in a raw file.** `raw/inbox/2026-09-25-vendor-call-notes.md`
  contains what looks like a login token for the vendor's staging portal (kind:
  token; the value is not recorded here). Hard stop (d): the file is not
  ingested and not staged. Last seen 2026-09-26 and again 2026-10-04, so this is
  one entry with a new date. Needs: the owner removes the token from the
  file, or tells the agent to ingest the notes without the line. Raw files are
  append-only for the agent, so it cannot edit the original. The six-week
  migration estimate in the file is not on any page yet; it bears on the open
  warehouse question in [[hub-work|Work]].
- **2026-10-04, checkpoint failed, tag rename not done.** The monthly tag check
  wants to rename the tag `habit` to `routine` on seven pages, which is a batch
  rewrite and needs a checkpoint first. The checkpoint commit failed with
  `fatal: Unable to create '.git/index.lock': File exists`. The agent cannot
  delete the lock file (hard stop (c)), so it skipped the rename and did
  nothing else destructive. Needs: the owner checks that no other git process
  is running, deletes `.git/index.lock`, and says whether `habit` or `routine`
  is the tag to keep.

## Done

- **2026-09-11, calendar block for the Friday review.** The agent was asked,
  in a note, to add a recurring Friday 16:30 block. Hard stop (a): it does not
  write to connected services. Outcome: the owner created the block by hand on
  2026-09-11; see [[friday-review]].

Part of [[hub-systems|Systems]].
