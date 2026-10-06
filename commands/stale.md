---
description: Find concept pages nobody has touched
---

List concept pages whose `updated` date is older than ninety days, sorted oldest first, with how many sources arrived on their topic since. Report only; stale does not mean remove. A page with new sources waiting needs updating. To retire pages use `/prune` or `/archive`; for pages with no inbound links use `/orphans`.

Follow the `second-brain-graph` skill.

For a plain list, `python3 scripts/link_check.py ~/brain --stale 90` prints each page's path, date and age in days, oldest first.
