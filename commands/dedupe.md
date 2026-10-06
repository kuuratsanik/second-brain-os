---
description: Find near-duplicate pages
argument-hint: "[folder]"
---

Scan $ARGUMENTS, or the whole wiki, for near-duplicates by title, alias overlap and shared inbound links. Propose merges with reasoning. Merge nothing.

Follow the `second-brain-lint` skill.

`python3 scripts/link_check.py ~/brain --duplicates` lists the pages whose names match once punctuation is ignored, and the pages that share an alias.
