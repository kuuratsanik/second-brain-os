---
tags: [trigger, behaviour, context-audit]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our agent is slow and expensive per turn and I think the prompt cache is not
hitting. Can you audit how its context is laid out? Its system prompt file is
below; there is no log of real requests.

```
You are SupportBot for Acme.
Current time: {{now}}
Logged-in user: {{user_name}} ({{user_email}})
Memories about this user: {{memories}}
Rules: be polite. Never promise refunds. Escalate legal threats.
(Followed by 40 tool definitions, loaded fresh each turn according to the user's plan.)
```
