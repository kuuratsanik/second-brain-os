---
description: Make spaced-repetition flashcards from concept pages
argument-hint: "[page or topic]"
disable-model-invocation: true
---

Write flashcards for $ARGUMENTS, or for concept pages updated in the last 30 days with no deck yet, in the Obsidian Spaced Repetition plugin's syntax (`question::answer`, and `?` between multi-line sides). Cards go in `output/flashcards/<concept>.md`, never in the page itself. Pages with `maintained_by: human` are queued, not carded, and `restricted` pages are skipped. To test yourself in chat instead, use `/quiz`.

Follow the `second-brain-flashcards` skill.
