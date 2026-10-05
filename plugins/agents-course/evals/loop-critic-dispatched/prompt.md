---
tags: [trigger, behaviour, loop-critic]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Agent]
---

My loop just finished attempt 3 of "make the parser reject empty input". The
worker says it is done. Before I accept it, have an independent critic with a
clean context review the result. There is no repository in this directory, so
the critic should say what it can and cannot check.
