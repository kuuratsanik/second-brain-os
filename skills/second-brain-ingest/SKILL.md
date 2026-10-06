---
name: second-brain-ingest
description: >-
  Turn raw source material in a second-brain vault into linked wiki pages:
  read the source, split it into concepts and entities, write or update pages,
  connect them to existing pages, and record the run in the log. Use this skill
  whenever the user drops a file into raw/, pastes an article, PDF or cleaned
  transcript and asks to add it to the vault, says "ingest this", "add this to
  my second brain", "process raw", or asks to catch up on unprocessed sources,
  even if they do not name the ingest command. Do NOT use for answering
  questions from an existing vault, for linting or repairing pages, for
  cleaning a raw transcript first (second-brain-transcript), or for editing
  notes the user wrote by hand.
---

# Ingest a source

A summary page alone makes a vault grow without getting smarter. The value is
in connecting new material to what exists; an unlinked page is invisible
within a week.

## Core rule

Nothing is ingested until it is linked. Every run ends with the new pages
connected to existing pages in both directions.

## Workflow

1. **Read the source completely** before writing anything. Partial reads
   produce pages built from the introduction, which is where sources are least
   specific.
2. **Check what already exists.** Search the wiki for the main entities and
   concepts. Ingesting into an empty vault and ingesting into a vault of 300
   pages are different jobs: in the second, most of your work is updating
   pages, not creating them. Compare names by the key under "Slugs and
   aliases" below, not by eye.
3. **Write the source page** in `wiki/sources/`. Record claims as claims, with
   the source attached.
4. **Extract concepts and entities.** One page per idea. If a concept page
   exists, add what this source contributes and update `updated:`. If it
   contradicts what is there, record both positions rather than replacing.
5. **Link in both directions.** The source page links to every concept and
   entity it touches; each of those links back. Add any missing target pages,
   or list them under Gaps in `index.md`.
6. **Update `index.md` and append to `log.md`** in the same run, because an
   index that lags is how a vault starts drifting.
7. **Commit the run** by path, following `second-brain-commit`, with the
   subject `run-YYYY-MM-DD-ingest`.
8. **Report** what changed.

## Slugs and aliases

Two names are the same page when their keys match. The key is the name
normalised to Unicode NFC, case-folded, with everything but letters and digits
removed, which is how `scripts/link_check.py --duplicates` compares file names,
`title:` and `aliases:`. `LLM wiki`, `LLM-Wiki` and `llm_wiki` share one key.

- Before creating a page, compute the key of the proposed file name and title
  and look for it among every page's file name, title and aliases. A match means
  update that page. When you are unsure whether two names are one page, create
  nothing and add no alias: queue the pair in `wiki/systems/needs-owner.md` and
  name both pages in the report (merging people or uncertain identities is a
  hard stop in the vault `CLAUDE.md`).
- The key keeps diacritics, so `Õppimine` and `Oppimine` differ under it.
  Search both spellings by hand, as the vault `CLAUDE.md` says, before you
  create.
- The file name follows the vault `CLAUDE.md` (lowercase ASCII, hyphens). The
  key ignores the hyphens, so two titles that differ only in punctuation or
  case will collide: give the second a disambiguating word.
- Set `aliases:` whenever a title has a common variant: an acronym and its
  expansion, a spelling or hyphenation variant, the original-language name, a
  short form people use in text. Include the title as it appears in the source.
  An alias that already belongs to another page is a duplicate, not an alias:
  stop and update or merge instead (`second-brain-merge`).
- **Two languages.** If the owner writes in two languages (the template assumes
  Estonian and English), set `lang:` to
  the language the page is written in (`et` or `en`; the page keeps its
  source's language). When the owner uses both languages for a thing, in the
  source, on another vault page or in what they have told you, add the title in
  the other language as an alias (`Õppimise plaan` on a page titled `Learning
  plan`, or the reverse). Do not translate a title yourself to invent one: an
  alias is a name the owner or a source actually uses. Compute the key of the
  new alias and check it against every page, as above, so it does not collide
  with another page. The file name follows the vault `CLAUDE.md`. This is what lets `/ask` and `vault_search`
  find a page from either language.
- Alias changes to existing pages are mechanical: add them and log each as
  `lint` in `wiki/log.md`. A page marked `maintained_by: human` is not edited,
  not even its frontmatter: queue the alias in `wiki/systems/needs-owner.md`
  and name the page in the report.

## Output format

End every run with this exact shape:

```
Ingested: <source name>
New pages: <n> (list)
Updated pages: <n> (list)
Links added: <n>
Contradictions found: <none | description>
Gaps created: <list of linked pages that do not exist yet>
Aliases added: <n> (list; name collisions found: <none | description>)
```

## Calibration

Over-extraction is the common failure: ten thin concept pages from one article,
each a restated paragraph. A source usually yields one to three concepts worth
their own page. If a candidate concept cannot be explained without referring
back to this one source, it belongs inside the source page instead.

Under-extraction shows up as source pages that contain three separate ideas and
link to nothing. If a page needs section headings for unrelated topics, split
it.

## Example

Input: the user drops `raw/karpathy-llm-wiki.md`, a clipped gist, into a vault
that already has pages for `[[Obsidian]]` and `[[Claude Code]]`.

Output: one source page; a new concept page `[[LLM wiki]]` explaining the
pattern in plain language; an entity page `[[Andrej Karpathy]]`; updates to
`[[Obsidian]]` and `[[Claude Code]]` noting their role in the pattern; a link
from the existing `[[Personal knowledge management]]` concept to the new one;
index and log updated; report showing 3 new, 3 updated, 11 links.
