---
tags: [trigger, behaviour, evals-bootstrap]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Write]
---

I want evals for my customer-support agent so a prompt or model change can't
silently break it. I have no trace logging yet. Three failures I remember:
1. It refunded order #1042 without asking for approval first.
2. It replied to a billing question without looking up the order.
3. It sent a reply that included another customer's email address.
Set up a first suite for me. Put `cases.yaml` and `check_traces.py` in the
current directory.
