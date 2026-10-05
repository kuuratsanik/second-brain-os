---
description: Pull knowledge into a project
argument-hint: "[project]"
disable-model-invocation: true
---

Find the concept pages relevant to the project in $ARGUMENTS, starting from the pages its `CLAUDE.md` links and the goal it states. Save a briefing into the project's `Inputs/`: one line per page, why it matters here, and where its sources disagree. Link to the pages; copy a page into `Inputs/` only when the project needs it frozen. Write nothing outside `Inputs/`, and give the briefing frontmatter with `maintained_by: agent`.
