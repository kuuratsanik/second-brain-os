---
tags: [trigger, behaviour, harness-audit]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Is it safe to let my coding agent run unattended overnight? Setup: it runs
directly in my main checkout on my laptop, with my own shell environment
(that includes AWS_PROFILE=prod and a GitHub token with push rights). The
settings allow every Bash command without asking. AGENTS.md says "be careful
with production". There is no test hook; it is told to run `make check`
when it remembers. What could a bad session break?
