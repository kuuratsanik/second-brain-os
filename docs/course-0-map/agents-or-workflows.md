# Agents or workflows

One decision comes before any building: can you write down the steps? If you can, write them. Code that runs known steps in a known order is a workflow, and a workflow beats an agent on every axis except one.

Anthropic's [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) draws the line cleanly: a workflow is a system where model calls and tools run along code paths you defined in advance; an agent is a system where the model directs its own process and decides its next step as it goes. Their advice is to find the simplest solution that works and add complexity only when it earns its place — agentic systems trade latency and cost for capability, and the trade has to be worth it.

## Why workflows win by default

Workflows are cheaper: each step carries only the context that step needs, not a growing transcript of everything so far. They run in parallel: independent steps fan out, while a loop is sequential by nature — each decision waits on the last observation. They are debuggable: a failed step has a name, an input, and a log line, where a failed loop has forty turns of transcript to read. And they are testable step by step, so a fix stays fixed.

## Where loops earn their cost

Loops belong where the steps are unknowable in advance. Research, where the next query depends on what the last one returned. Debugging, where nobody knows which of a thousand files holds the fault. Open-ended synthesis, where the shape of the answer emerges from the material. The signature is always the same: you cannot enumerate the branches beforehand, but you can check the result afterwards. If both halves do not hold, you are paying agent prices for workflow work.

## The cost reality

The multiplier is not folklore; Anthropic published it against their own traffic. In [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) they report that agents typically use about 4x the tokens of a chat interaction, and multi-agent systems about 15x — and that multi-agent architectures only make economic sense where the task's value covers the bill. The same post concedes that domains where all agents must share the same context, or that have many dependencies between agents, are not a good fit for multi-agent systems today, and notes that most coding tasks have fewer parallelisable pieces than research.

So the ladder runs: one model call, then a workflow, then a single agent, then multiple agents — and every rung must justify the climb to the next. Most systems should stop early. This course asks that question first.

## How to take this course

In order, and with something to build. This module is the map: what an agent actually is, the five-layer frame, and this decision. Modules 1 through 5 then take one layer each, in the order the questions arise — what it sees, who decides, who sorts, what it can reach, how you know. Each module gives you working defaults; the deep-dive handbooks carry the reasoning behind them, and you can descend into a handbook the moment its layer starts hurting in your own system. Read [what an agent is](what-an-agent-is.md) and [five layers, one system](five-layers.md) before anything else; the rest will keep.

- Module 0 — the map: this page and its two companions
- [Module 1 — context](../course-1-context/how-models-read.md): [how models read](../course-1-context/how-models-read.md)
- [Module 2 — the loop](../course-2-loop/loops-vs-workflows.md), with its handbook [what loop engineering is](../track-loop/what-loop-engineering-is.md)
- [Module 3 — the gate](../course-3-gate/cheap-decisions.md), with its handbook [system-one models](../track-jev/system-one-models.md)
- [Module 4 — the harness](../course-4-harness/the-office.md), with its handbook [what a harness is](../track-harness/what-a-harness-is.md)
- [Module 5 — evals](../course-5-evals/two-kinds-of-checks.md), with its handbook [why evals](../track-evals/why-evals.md)
- [Module 6 — production](../course-6-production/from-prototype.md): from demo to deployed, and the day-one plan
