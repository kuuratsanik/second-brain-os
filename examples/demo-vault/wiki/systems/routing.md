---
title: Routing
type: system
status: active
domain: [systems]
lang: en
sensitivity: normal
maintained_by: human
created: 2026-08-13
updated: 2026-09-27
aliases: [Where each source lands]
tags: [vault]
---

# Routing

> Fictional. This page belongs to the demo vault; the people, organisations and articles in it are invented.

Where each kind of material lands and what it becomes. The agent reads this
when ingesting. Rules for page contracts, language and linking are in
`CLAUDE.md`; these are the per-source details. The owner edits this page; the
agent proposes changes in its run report.

| Source | Arrives in | Becomes | Notes |
|---|---|---|---|
| Web articles (Obsidian Web Clipper) | `raw/clippings/` | Source page, `kind: article`, plus concepts and entities | Domain follows the content, usually `learning` or `work`. Estonian articles keep their language: ASCII file name, original title in `title:` and `aliases:`. |
| YouTube | `raw/youtube/` | Source page, `kind: video` | Clean the transcript first with `second-brain-transcript`; write `<name>-clean.md` beside the original. Keep coarse timestamps. |
| Meetings and calls (Granola) | `raw/meetings/` | Meeting page (`templates/meeting.md`), person pages, action items | Usually `work`. Personal calls are `private`. Do not paste the transcript. |
| Email (Gmail) | `raw/workspace/email/` | Source page, `kind: email` | Pull only what the standing rules in [[vault-operating-notes]] allow or the owner asks for. Do not mirror the inbox. Summarise; do not copy other people's messages in full. |
| Chat (Slack) | `raw/workspace/chat/` | Source page, `kind: chat` | Same rule as email. The owner does not use Slack yet. |
| Docs (Notion, Google Drive) | `raw/workspace/docs/` | Source page, `kind: doc` | Record the doc's location so the page can be refreshed. |
| Calendar (Google Calendar) | `raw/workspace/calendar/` | No pages of its own | Not used yet; see [[vault-operating-notes]]. |
| AI chat exports | `raw/ai-chats/` | Source page, `kind: ai-chat`; ideas, decisions, concepts | Use `second-brain-chat-import`. Keep what the owner thought, decided or asked; drop the assistant's boilerplate. Self-improvement ideas become idea pages. |
| The owner's notes on their own systems and routines | `wiki/systems/`, or `raw/inbox/` | System page, `maintained_by: human` | The owner's wording stands. |
| Journal | `journal/` | Concept, idea or review pages, `private` | Extract patterns and decisions. Do not quote at length. |
| Anything else | `raw/inbox/` | Whatever fits; if nothing does, say so in the run report | PDFs and papers use their own ingest skills. Notes typed in Obsidian land here (see `.obsidian/app.json`). A file containing a secret is queued in [[needs-owner]], not ingested. |

When an item fits two domains, give it both in `domain:` and link it from both
hubs. When an item contains a resolution, a habit idea or an "I should try",
capture it as an idea page and link it to the source.

## What "systems" means here

The owner listed "system" as an input without saying what it meant. On
2026-09-16 the owner confirmed the reading below: their own notes about their
routines, workflows and tool setups, plus the vault's operating notes. The
[[friday-review]] page is the first example.

Part of [[hub-systems|Systems]].
