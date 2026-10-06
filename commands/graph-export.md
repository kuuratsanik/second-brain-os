---
description: Export the graph for outside analysis
argument-hint: "[format]"
disable-model-invocation: true
---

Run `scripts/graph_export.py` for $ARGUMENTS, defaulting to CSV edges, and summarise what the export contains. If the vault has no `scripts/` folder (the kit is installed as the `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/graph_export.py` instead; Claude Code fills in that path only for a plugin install.

Follow the `second-brain-graph` skill.
