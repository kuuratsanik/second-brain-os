---
description: Find near-duplicate pages
argument-hint: "[folder]"
---

Scan $ARGUMENTS, or the whole wiki, for near-duplicates by title, alias overlap and shared inbound links. Propose merges with reasoning. Merge nothing.

Follow the `second-brain-lint` skill.

To list candidates first, run `scripts/link_check.py . --duplicates`, which groups pages whose names match once case and punctuation are ignored, and pages that share an alias. If the vault has no `scripts/` folder (the kit is installed as the `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/link_check.py` instead; Claude Code fills in that path only for a plugin install.
