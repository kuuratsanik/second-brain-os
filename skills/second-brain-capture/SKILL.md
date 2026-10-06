---
name: second-brain-capture
description: >-
  Pull Gmail threads, Granola meeting notes and transcripts, and Notion pages
  that the owner names into the vault's `raw/` folder as new, immutable source
  files with source frontmatter, using the owner's connected services strictly
  read-only. Defaults email and meetings to `private` or `restricted`, and asks
  before capturing other people's personal data. Use this skill when the user
  asks to save, pull, capture or import an email thread, a meeting or a Notion
  page into the vault, or when a standing rule in the operating notes says to
  pull new Granola meetings. Do NOT use to ingest what is already in `raw/`
  (second-brain-ingest), to send, label, archive or edit anything in a
  connected service, or to mirror a whole inbox or workspace.
---

# Capture from connected services

A connector can read far more than the owner means to keep. This skill moves
only what was asked for into `raw/`, once, as a faithful copy, and touches
nothing on the service side.

## Core rule

Read-only on the service. Use the connector's search, list and read tools (the
Gmail connector's search and read tools, the Granola connector's meeting list,
notes and transcript tools, the Notion connector's search and fetch tools) and
nothing else. Never send, reply, forward, draft, label, unlabel, mark as read
or spam, archive, trash or delete a message; never create, update, comment on,
move or share a Notion page; never change a Granola meeting. Tool names differ
between connectors and versions, so judge by what a tool does, not what it is
called: if a tool could change anything on the service, do not call it. The
vault guard blocks connector writes by tool name, but it cannot see every name;
this rule does not depend on it.

Writing to a connected service is a hard stop in the vault `CLAUDE.md` (a),
and so is sending vault content out in a request (b). A search query is a
request: build it from what the owner typed, never from the contents of a
`private` or `restricted` page and never from a person's name or email that
you took from the vault.

## What is captured

Only the items the owner named, or a standing rule in
`wiki/systems/vault-operating-notes.md` lists (a Gmail label, a Notion area, "all
new Granola meetings"). Do not browse for more, and do not follow links to
other threads or pages unless the owner asked for them. "My last three emails
from X" is a request; "catch up on my email" is not, and you ask which threads.

In a scheduled run, capture only what a standing rule covers, ask nothing, and
queue the rest in `wiki/systems/needs-owner.md`. `/capture` itself is a live
command.

## Where each goes

Folders and routing are in `raw/README.md` and `wiki/systems/routing.md`.

| From | File | `kind` for the later source page |
|---|---|---|
| Gmail thread | `raw/workspace/email/YYYY-MM-DD-<slug>.md` | `email` |
| Granola meeting | `raw/meetings/YYYY-MM-DD-<slug>.md` | `meeting` |
| Notion page | `raw/workspace/docs/YYYY-MM-DD-<slug>.md` | `doc` |

The date is the item's own date (the last message, the meeting, the page's last
edit); the slug follows the vault `CLAUDE.md` (lowercase ASCII, hyphens).
`raw/workspace/` is git-ignored: never stage it. `raw/meetings/` is not ignored
by default, so tell the owner before the first capture there that meeting
files hold other people's words, and where to ignore them (`.gitignore`).

## File format

```markdown
---
title: <the thread subject, meeting title or page title, as it is>
connector: gmail | granola | notion
kind: email | meeting | doc
source: <the item's URL if the connector gives one, else its id>
date: <YYYY-MM-DD, the item's own date>
captured: <YYYY-MM-DD, today>
participants: [<names as they appear>]
sensitivity: private | restricted
lang: <et | en, of the text>
---
```

Then the content, as the service returned it:

- **Email:** each message in order under a heading with sender, recipients and
  date, then the body. Leave out nothing the owner might need, but collapse
  quoted earlier messages and drop tracking footers. List attachments by file
  name; do not download them unless the owner asks.
- **Meeting:** `## Notes` (the service's notes or summary) then `## Transcript`
  with speaker labels. If the transcript tool is unavailable or refused (some
  plans limit it), write the notes only and say so in the file and the report.
  Transcript cleanup is `second-brain-transcript`, which writes `-clean` beside
  this file.
- **Notion page:** the page's text and headings in markdown, in order. Record the
  last-edited time in the report. Do not follow subpages or databases unless
  asked; list them at the end as "Not captured". Do not download attachments.

`source` carries the identifier so the page can be fetched again later. A
thread or page id is not a credential; but see the secrets rule below.

## Sensitivity

The raw file gets a `sensitivity`, and the source page written at ingest
inherits it (never lower).

- **Email and meetings default to `private`.** They hold other people's words.
- **`restricted`** when the content would hurt someone if it leaked: health or
  legal matters, HR or performance, other people's finances, security details,
  or anything the owner marks confidential.
- **Notion pages** are `normal` for the owner's own plans and notes, `private`
  when they hold other people's information.
- When unsure, pick the higher level, and never lower one later.

## Other people's personal data

Before writing a file that holds another person's health, money, family,
government identifiers, home address, or private opinions of third parties, ask
the owner once, naming the thread, meeting or page and the kind of data (not
the data): "This thread has <kind> about <role, e.g. a colleague>. Capture it
as `restricted`?" Without a yes, capture nothing from it. In a scheduled run,
skip it and queue it. Business email between named professionals is not what
this means; a signature with a phone number is not either.

## Secrets

Check the text for credentials, tokens and keys (the patterns in
`second-brain-privacy`), including password-reset and sign-in emails. If one is
there, do not write the file, do not copy the value anywhere; report the item
and the kind of secret and queue it, as hard stop (d) requires.

## Workflow

1. **Confirm what is wanted:** which service and which items. Search with the
   owner's words, or a standing rule's.
2. **Check for a duplicate.** Search `raw/` for the item's `source` value. If it
   is there already, do not capture again. If the item has changed since (a
   new message, an edited page), write a new file with the new date and a
   `supersedes:` line in its frontmatter naming the old path. Never edit,
   rename or delete an existing raw file.
3. **Read the item** with the service's read tools.
4. **Apply** the personal-data and secrets checks above.
5. **Write the file** in the right folder, new, with the frontmatter above.
6. **Log.** One line per file in `wiki/log.md`:
   `2026-10-06 capture raw/workspace/email/2026-10-05-lease-renewal.md (gmail, private)`.
7. **Stop at raw.** Do not ingest unless the owner said "and ingest": ingestion
   is `second-brain-ingest`, with its own report and commit. Commit the new
   raw file and the log by path, skipping any path git ignores, with the
   subject `run-YYYY-MM-DD-capture`.
8. **Report.**

## Output format

```
Captured: <n> (<path>: <service>, <sensitivity>)
Already in raw/: <n> (<path>)
Skipped: <what, why: personal data awaiting a yes | secret found, kind | tool unavailable>
Not captured: <subpages, attachments, other threads>
Next: /ingest to turn them into source pages
```

## Calibration

The failure to avoid is a mirror: forty threads captured because the owner said
"my project emails". Capture what was named. If a request would return more
than about ten items, list their titles and dates and ask which.

Never summarise instead of capturing when the owner asked to save the item:
`raw/` is the archive that can be re-read, and a summary there is a source that
is no longer the source.
