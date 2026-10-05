# Five layers, one system

Think of an agent as a new employee on his first day. He is bright, fast, and knows nothing about your company. Everything that decides whether he succeeds is the system you build around him — and that system has exactly five layers.

The field talks about these layers as if they were rival schools: context engineering, loop engineering, JEV engineering, harness engineering, eval engineering. Five buzzwords, five conference tracks, five people telling you the other four are hype. They are not competing approaches. They are five layers of one system, and each answers one question: what it sees, who decides, who sorts, what it can reach, how you know.


![Diagram of five layers around a model: the gate, the harness (tools, keys, sandbox), context (what it sees) and the loop (who decides next), with evals running the same test after every change.](fig-five-layers.svg)

## Context: what it sees

What is on his desk when he starts the task. The brief, the relevant files, the one page of history that matters — and nothing else. The model reasons only over what is in the window; everything outside it does not exist. Without this layer the agent guesses, invents plausible answers to questions it was never shown, and asks again for things it was already given. Bad context is routinely misdiagnosed as a bad model.

## Loop: who decides

Does he work from a checklist, or does he decide the next step himself? A checklist is a workflow: cheap, predictable, dead at the first surprise. Self-directed steps are an agent loop: flexible, expensive, capable of wandering. Without deliberate loop design you get one failure or the other — a script that breaks on anything unforeseen, or a wanderer that burns tokens circling the same three files.

## Gate: who sorts

The front desk sorting the mail. Not every request deserves the expensive employee: a small, fast decision — a classifier, a cheap model, a rule — routes the trivial away and the real work in. Without a gate, everything hits the costliest path, including the junk, the duplicates, and the traffic that should never reach an agent holding keys at all.

## Harness: what it can reach

His office: the tools on the desk, the keys on the ring, and the person who checks his work before it goes out. Permissions, sandboxes, timeouts, review. Without a harness the agent is either useless — it can decide but not act — or dangerous: it can act on everything, and nobody looks before the action lands.

## Evals: how you know

The same test, every month. Not a demo, not a vibe check after a prompt change — a fixed set of tasks with known answers, run on every version. Without evals you can only feel whether a change helped, and your regressions are discovered by your users.

## The map

A failure in one layer wears the mask of another: missing context looks like a stupid model, a missing gate looks like runaway cost, missing evals look like nothing at all until production. Each layer gets a module of this course, and four get a handbook. The split is the contract of this whole site: the module teaches the idea once, in order; the handbook holds the full menu of techniques, tools and builds, for when that layer starts hurting.

| Layer | Question | Module | Handbook |
| --- | --- | --- | --- |
| Context | What does it see? | [Module 1: how models read](../course-1-context/how-models-read.md) | Module 1 is the deep dive |
| Loop | Who decides the next step? | [Module 2: loops vs workflows](../course-2-loop/loops-vs-workflows.md) | [What loop engineering is](../track-loop/what-loop-engineering-is.md) |
| Gate | Who sorts the incoming work? | [Module 3: cheap decisions](../course-3-gate/cheap-decisions.md) | [System-one models](../track-jev/system-one-models.md) |
| Harness | What can it reach? | [Module 4: the office](../course-4-harness/the-office.md) | [What a harness is](../track-harness/what-a-harness-is.md) |
| Evals | How do you know it works? | [Module 5: two kinds of checks](../course-5-evals/two-kinds-of-checks.md) | [Why evals](../track-evals/why-evals.md) |

## Check yourself

- Your agent keeps re-requesting a file that was in its context two steps ago. Which layer is broken, and why does it look like a model problem?
- A teammate insists eval engineering has replaced prompt engineering. Using the five questions, explain why the claim is a category error.
