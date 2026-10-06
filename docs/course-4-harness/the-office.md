# The Office

Hire the most brilliant engineer alive and put them in a bad office — no keys to the rooms they need, no documentation, no test suite, a manager who rubber-stamps everything — and you get bad work. An agent is a model plus a harness: the model is the hire, the harness is the office. [What a harness is](../track-harness/what-a-harness-is.md) covers the anatomy — loop, tools, prompts, permissions, context. This module covers the discipline: the office is a product you design and measure, not packaging around the clever part.

## You buy a model and a harness

Nobody runs a bare model. The moment you adopt Claude Code, LangChain's deepagents or your own seventy-line loop, you have bought a second product with its own quality curve. Vendors price the model per token and give the harness away, which tricks teams into treating it as free and therefore unimportant. The 2026 measurements say the opposite: Anthropic's infrastructure study notes that setup differences can exceed the margins that separate top models on a leaderboard, and LangChain moved a score by 13.7 points without touching the model.

## Six points from container resources

In February 2026 Anthropic reran Terminal-Bench 2.0 on a Google Kubernetes Engine cluster under six resource configurations, from strict enforcement of each task's CPU and memory spec up to fully uncapped — same model, same harness, same tasks. Uncapped resources lifted the score by 6 percentage points over strict enforcement (p < 0.01), and under strict enforcement 5.8% of tasks failed on infrastructure errors — containers killed by transient memory spikes, not the model getting the answer wrong. The write-up is [Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise). If the RAM ceiling alone is worth six points, the environment is not a detail. It is part of the score.

## Thirteen points from the harness alone

In February 2026 LangChain froze the model entirely — GPT-5.2-Codex throughout — and iterated only on the harness of their deepagents-cli: system prompt structure, tool design, and middleware such as loop detection and a pre-completion checklist. The agent went from 52.8 to 66.5 on Terminal-Bench 2.0, a 13.7-point gain with the model fixed. The post is [Improving Deep Agents with harness engineering](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering). *Not re-checked on 5 October 2026: the page could not be fetched, and the figures here were confirmed only from search-result summaries of it.*

## A cheaper model in a better office

The July 2026 sequel, [Tuning the harness, not the model](https://www.langchain.com/blog/tuning-the-harness-not-the-model-a-nemotron-3-ultra-playbook), applied the same playbook to NVIDIA's open-weights Nemotron 3 Ultra. Harness tuning alone took it to a best run of 0.86 on LangChain's Deep Agents suite against Claude Opus 4.8's best of 0.87 — at about $4.48 per run versus $43.48, roughly a tenth of the cost. One suite, scored by the harness's own authors, so hold it loosely; but the direction matches everything else measured this year. A strong office lets a cheaper hire do the job. *Not re-checked on 5 October 2026: the page could not be fetched, and the figures here were confirmed only from search-result summaries of it.*

## When you need one

The moment the agent touches anything real. A chatbot that answers badly costs you a wince and a retry; nothing happened until you acted on the text. An agent with a shell, a database connection or a send button acts on its own output — the wrong answer is now a pushed commit, a dropped table, a sent email. That is the line: while the output is text you review, prompt away and skip the ceremony. The day it becomes actions that simply happen, you need walls, guides, sensors and gates — in that order. [The four rings](the-four-rings.md) is that build order, and [harness practice](harness-practice.md) walks through hardening a real agent end to end.
