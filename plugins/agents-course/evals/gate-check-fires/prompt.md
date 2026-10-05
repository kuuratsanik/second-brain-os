---
tags: [trigger, behaviour, gate-check]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our support pipeline sends every incoming email to Claude Opus. For each
email it decides: is this spam, which of five queues it belongs to, whether
a human must see it, and then writes the reply. We process about 20,000
emails a day and the bill is too high. Where can we cut it down without
hurting the replies?
