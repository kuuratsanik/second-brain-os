---
description: Answer a specific question from the vault
argument-hint: "[question]"
disable-model-invocation: true
---

Answer the question in $ARGUMENTS from vault pages only. Search with `scripts/vault_search.py` in both Estonian and English, read the top pages, and cite every claim as `[[page]]` plus `path:line`. Say "the vault doesn't say" where the pages are silent, never quote `restricted` pages, and answer in the language of the question. Offer to file a good answer as a wiki page. The default for a question you want answered; `/know` is for a topic with no question, and `/trace` is the same question with the list of pages read. If the vault has no `scripts/` folder (the kit is installed as the `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/vault_search.py` instead; Claude Code fills in that path only for a plugin install.

Follow the `second-brain-ask` skill.
