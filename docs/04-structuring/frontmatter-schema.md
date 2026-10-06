# Frontmatter schema

Frontmatter is what makes the vault queryable by something other than text
search. It costs nothing to write and it is what Dataview, scripts and the agent
itself use to find things by shape.

## The schema

```yaml
---
title: Canonical name
type: source | entity | concept | synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
aliases: [other names this is known by]
tags: [two or three]
---
```

Source pages add:

```yaml
url: https://...
author:
published: YYYY-MM-DD
```

Entity pages add `kind: person | org | product | tool`.

That is the minimum the method needs. The [vault
template](../../vault-template/CLAUDE.md) makes a stricter choice, because it is
built for several domains, mixed languages and an agent that works unattended:

```yaml
---
title: Canonical name, in the page's own language
type: source | entity | concept | synthesis | idea | experiment | review | system | hub
domain: [work | learning | personal | creative | self-improvement | systems]
lang: ISO 639-1 code, usually en or et
sensitivity: normal | private | restricted
maintained_by: human | agent
created: YYYY-MM-DD
updated: YYYY-MM-DD
aliases: [other names, including the original spelling]
tags: [two or three]
---
```

The extra fields:

- `domain` says which area of life or work the page belongs to, and which hub
  links to it. A page can have more than one.
- `lang` is the language the page is written in. Pages keep the language of their
  source and are not translated.
- `sensitivity` decides what may leave the vault. `private` is for health,
  finance, relationships, journal-derived material and third parties'
  information; `restricted` is for anything that would hurt someone if it
  leaked. When unsure, use the higher level.
- `maintained_by: human` marks pages whose wording the agent must not change. It
  may add links and fix structure only. The default is `agent`.
- `status` appears on idea, experiment and system pages and tracks where they
  are in their lifecycle. Ideas use `new`, `considering`, `promoted` or
  `dropped`; experiments `planned`, `active`, `reviewing`, `adopted` or
  `dropped`; systems `draft`, `active` or `retired`. `scope` on a review page names the period
  it covers (`experiment`, `week`, `month`, `quarter`, `year`).
- `kind` on a source page is `article`, `video`, `meeting`, `email`, `chat`,
  `doc`, `ai-chat`, `paper` or `other`. On an entity, `kind: person`.
- `raw:` on a source page is the path of the raw file it came from, so a page can
  be traced back and refreshed.
- `archived`, `archived_reason`, `archived_from` and, for a merge, `merged_into`
  are written when a page moves to `archive/`. See [safety and
  guardrails](../06-agents/safety-and-guardrails.md).
- `publish: true` is the explicit opt-in described in [publishing and
  export](../08-outputs/publishing-and-export.md). Only the owner sets it, in a
  live session.

`wiki/index.md` and `wiki/log.md` are exempt from the schema. If you do not need
several domains or languages, leave these fields out; the method still works.

## Why each field earns its place

`type` drives every structural query and every lint check. Without it you cannot
ask how many concepts you have, or find sources with no concepts attached.

`updated` is what makes review possible. Stale concept pages are the main way a
vault rots, and you cannot find them without a date.

`aliases` is what makes wikilinks resolve when the same thing has three names.
See [naming and aliases](naming-and-aliases.md).

`url` on a source page is what separates a citation from a claim. A source page
without it is unverifiable.

## Tags

Two or three per page, from a small controlled vocabulary you actually maintain.

Tags fail in one specific way: the vocabulary grows until it is meaningless.
Fifty tags used once each are worse than no tags, because they create the
impression of a taxonomy while doing none of the work.

Keep the list in `CLAUDE.md` and instruct the agent to use existing tags or
propose a new one explicitly rather than inventing them silently.

Folders and links carry the structural load. Tags are for cross-cutting
qualities that do not fit either: `unverified`, `to-revisit`, `disputed`.

## Empty fields

Leave a field out rather than filling it with a guess. An absent `published`
means unknown, which the agent can say honestly. A guessed date becomes a fact
in a concept page three weeks later.

## Keep it stable

Adding a field to the schema means either backfilling every page or living with
a mixed vault where queries miss the older half.

Decide the schema early, keep it small, and change it rarely. When you do change
it, run a backfill pass over the whole vault in one go rather than letting the
change apply only to new pages.

## Next

[Naming and aliases](naming-and-aliases.md)
