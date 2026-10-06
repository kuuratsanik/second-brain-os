---
name: second-brain-flashcards
description: >-
  Generate question and answer flashcards from a second-brain vault's concept
  pages, in the card syntax of the Obsidian Spaced Repetition plugin, and write
  them to a separate deck file under `output/flashcards/`. Skips
  `maintained_by: human` pages (it queues them instead) and `restricted` pages.
  Use this skill when the user asks for flashcards, a deck, spaced repetition
  cards or "cards from this page". Do NOT use for a one-off self-test in chat
  (second-brain-quiz), for editing concept pages, or for scheduling reviews:
  the plugin does that.
---

# Make flashcards

The plugin schedules reviews, so this skill only has to write cards that are
true, short and traceable to a page. A card the vault does not support teaches
the owner something false at the interval the plugin chooses.

## Where the cards go, and why

Cards go in a separate deck file, `output/flashcards/<concept-slug>.md`, one
file per concept page, and not under a `## Flashcards` heading in the concept
page. Reasons:

- The plugin writes review state into the file that holds the card, as an HTML
  comment after it, such as `<!--SR:!2024-08-16,51,230-->` (its
  [data storage docs](https://github.com/st3v3nmw/obsidian-spaced-repetition/blob/master/docs/docs/en/data-storage.md),
  read 2026-10-06). A concept page the plugin edits and the agent maintains
  would be changed by both. A deck file belongs to the plugin once it exists.
- A concept page marked `maintained_by: human` cannot be edited at all, not
  even to add a section. A deck file leaves the page as it is.
- The agent updates concept pages as sources arrive and bumps `updated:`.
  Card changes would keep resetting the date that stale-page checks read.
- A deck needs a tag (`#flashcards`, in the plugin's
  [decks docs](https://github.com/st3v3nmw/obsidian-spaced-repetition/blob/master/docs/docs/en/flashcards/decks.md),
  read 2026-10-06), and in a file with that tag any line that matches the card
  syntax becomes a card. Keeping that to a file made for it avoids stray cards
  from ordinary prose.

`output/` is the agent's folder for generated material, so this needs no new
folder in the vault's layout.

## Core rule

Every card comes from a claim the concept page makes, and the page must
support it. Never write a card from knowledge the page does not hold. Never
generate from, or about, a `restricted` page or a `maintained_by: human` page.

## Card syntax

From the plugin's
[Q&A cards docs](https://github.com/st3v3nmw/obsidian-spaced-repetition/blob/master/docs/docs/en/flashcards/q-and-a-cards.md)
and [overview](https://github.com/st3v3nmw/obsidian-spaced-repetition#readme),
read 2026-10-06. The separators are the plugin's defaults and can be changed in
its settings; if the owner changed them, use theirs.

| Kind | Syntax |
|---|---|
| Single line | `question::answer` |
| Single line, both directions | `term:::definition` (makes two cards) |
| Multi-line | question lines, a line holding only `?`, answer lines |
| Multi-line, both directions | the same with `??` |
| Deck | a tag such as `#flashcards/<name>` in the file; it applies to every card after it until the next tag |

Rules the docs give that affect how you write them:

- A blank line ends a multi-line card by default. Never put a blank line inside
  a card. If an answer needs one (a table), leave that card out.
- Both sides of `?` must touch it: no blank line between the question, the
  `?` line and the answer.
- The plugin also reads `==highlight==`, `**bold**` and `{{braces}}` as cloze
  cards when the owner has enabled them. Do not use those marks in card text
  except on purpose. Avoid `::` and a bare `?` line inside card text, for
  example in code.
- Do not write or edit `<!--SR:...-->` comments. They are the plugin's.

Not re-checked: the plugin's settings page, whose table could not be read as
text on 2026-10-06. The default separators and the blank-line end marker are as
the Q&A and blank-line pages state them.

## Workflow

1. **Pick the pages.** The ones the owner names, or with no argument the
   concept pages updated in the last 30 days that have no deck file yet. Read
   each page's frontmatter first.
2. **Filter.**
   - `sensitivity: restricted`: skip, say nothing about its content, list the
     path under "Skipped".
   - `maintained_by: human`: skip, and queue it in
     `wiki/systems/needs-owner.md` (search Waiting first and update the date if
     present): "Cards proposed for <path>; say yes and I will write
     `output/flashcards/<slug>.md`, which does not touch the page." On the
     owner's yes in a live session, treat it as agent-maintained for this one
     step: the deck file is a separate page.
   - Anything that is not a concept page (a source, an entity, a hub): skip.
     Sources are one document's claims, which change; the concept page is the
     vault's settled version.
3. **Choose the cards.** Up to eight per page. Take the definition, the
   distinguishing claims, a non-obvious cause or consequence, and what the page
   says argues against it. Each card tests one fact. Write the question so it
   can be answered without seeing the page. Where the page records two sources
   disagreeing, ask "What does [[source]] say about X?" so the card is true
   whichever is right. Do not make cards from open questions.
   - Write in the page's language (`lang:`). Do not translate. An Estonian
     page gives Estonian cards.
   - A fact the page states with a source keeps a link at the end of the
     answer: `answer [[concept]]`.
   - Use `:::` only when the reverse is also a good question (a term and its
     definition).
4. **Write the deck file** `output/flashcards/<concept-slug>.md`, using the
   concept page's file-name slug. New file:

   ```markdown
   ---
   title: Flashcards, Learning plan
   lang: en
   sensitivity: normal
   maintained_by: agent
   created: 2026-10-06
   updated: 2026-10-06
   ---

   Cards from [[learning-plan]]. Review state is written by the Obsidian Spaced
   Repetition plugin; do not edit it.

   #flashcards/learning-plan

   What does the page say is the main risk of a fixed schedule?::Skipping a day breaks the habit [[learning-plan]]
   ```

   `sensitivity` is the concept page's level, never lower. Put the tag in the
   body, not in the frontmatter `tags:`, so it does not enter the vault's tag
   vocabulary. `type:` is omitted: files in `output/` are not wiki pages.
5. **If the deck file exists,** never rewrite it. Append only cards whose
   question is not already there, at the end, and leave every existing card and
   its `<!--SR:` comment as it is. If a concept page now says something
   different from an existing card, append the new card and list the old one in
   the report for the owner to delete in Obsidian; deleting it here would lose
   its review history.
6. **Log and commit.** One line per deck in `wiki/log.md`:
   `2026-10-06 flashcards output/flashcards/learning-plan.md (6 cards from wiki/concepts/learning-plan.md)`.
   Commit the deck files, the queue page and the log by path, following
   `second-brain-commit`, with the subject `run-YYYY-MM-DD-flashcards`.

## Output format

```
Decks: <n> written, <n> extended
Cards: <n> new (<path>: <n>)
Skipped: <path>: restricted | maintained_by human, queued | not a concept page
Old cards that no longer match their page: <path: question>, for you to delete
Next: open the deck in Obsidian; the plugin's review command does the rest
```

## Calibration

Eight good cards beat thirty vague ones. A card that restates the page title is
not a test. If a page is too thin to yield three cards, write none and say so.

These files were not tested against a running copy of the plugin. If cards
do not appear, check that the deck tag matches a tag in the plugin's settings
(`#flashcards` is its default, per its decks docs).
