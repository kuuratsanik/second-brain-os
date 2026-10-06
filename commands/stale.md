---
description: Find concept pages nobody has touched
---

List concept pages whose `updated` date is older than ninety days, sorted oldest first, with how many sources arrived on their topic since. Report only; stale does not mean remove. A page with new sources waiting needs updating. To retire pages use `/prune` or `/archive`; for pages with no inbound links use `/orphans`.

Follow the `second-brain-graph` skill.

For a plain list, run `scripts/link_check.py . --stale 90`, which prints each page's path, date and age in days, oldest first. The date is `updated`, then `created`, then the file's modification time. If the vault has no `scripts/` folder (the kit is installed as the `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/link_check.py` instead; Claude Code fills in that path only for a plugin install.
