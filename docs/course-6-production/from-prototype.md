# From Prototype to Production

Every module so far ends with something that works on your machine. This one is about what happens when other people — or a scheduler at 3am — start depending on it. Google's *Prototype to Production* whitepaper (Kaggle, November 2025) opens with the honest version: "Building an agent is easy. Trusting it is hard." Its estimate is that roughly 80% of the effort in shipping an agent goes into infrastructure, security, and validation — not into making the agent smarter.

## What breaks when a demo meets traffic

A demo runs when you are watching it, on inputs you chose, with your own credentials. Production removes all three comforts at once. The failure list is predictable:

- **Reliability.** Providers time out, rate-limit, and occasionally return garbage. Without retries with backoff and idempotent tools, one flaky call ruins a whole run — and a retried non-idempotent tool sends the email twice.
- **Cost.** A loop that costs 40 cents when you babysit it costs whatever it wants when you don't. Unbounded runs need [turn and dollar ceilings](../course-2-loop/loops-vs-workflows.md) before anything else.
- **Inputs.** Real traffic contains malformed files, hostile text, and edge cases your three test prompts never covered.
- **Change.** In a demo, the prompt lives wherever you last pasted it. In production, an untracked prompt edit is an unreviewable deploy.

The whitepaper frames the shift as a discipline it calls AgentOps: manual spot-checks become automated gates, ad-hoc tweaks become versioned prompts and tools, and "it seemed fine" becomes logs, traces, and metrics.

## Three deployment shapes, one agent

Production agents get invoked three ways: on a **schedule** (the nightly digest), on an **event** (a file lands, a webhook fires), or behind an **API** (a person or another system asks right now). Palantir's AIP architecture describes exactly this trio — schedule-based automations, near real-time event-driven automations, and API-driven operations — all running against the same underlying data and action layer.

The design consequence: keep the agent's logic separate from its trigger. One agent definition, three thin adapters. If your scheduled version and your API version are two codebases, every fix now has to land twice, and one of them will drift.

## One gateway in front of every model call

The single highest-leverage piece of infrastructure is a gateway — one choke point that every model call passes through, no exceptions. It does four jobs:

- **Masking.** Strip or pseudonymise sensitive fields before they leave your boundary.
- **Caching.** Return cached completions for repeated prefixes and identical calls.
- **Retries and failover.** Backoff, provider fallback, and a kill switch in one place.
- **Token accounting.** Every call tagged with who triggered it and what it cost.

This is the pattern grown-up stacks converge on: Palantir routes all LLM access through a secure integration layer with token consumption tracking and uniform audit logging, rather than letting each application call providers directly. You do not need Palantir to copy the shape — a 200-line proxy gets you most of it.


![Diagram of a production agent: schedule, webhook and API call triggers all feed one gateway that masks, caches, retries and counts, then one agent with its tools, with a trace of every run. One agent sits behind every trigger, and evals gate each change.](fig-production.svg)

## The path the whitepaper draws

The whitepaper's production path is a lifecycle, not a launch: development (fast experimentation), staging (automated testing and simulated load), production (gradual rollout with monitoring). Releases go out as canary or blue-green deployments with instant rollback, never a 100% switch. Evaluation suites run in CI and block the deploy when scores drop — the [two kinds of checks](../course-5-evals/two-kinds-of-checks.md) from module 5 become the gate, not a dashboard. And the loop closes: production traces feed the eval set, which hardens the next release.

None of this is exotic. It is ordinary software discipline applied to a component that happens to be probabilistic. The next page covers the operating side: [watching, paying for, and securing the thing once it runs](operating-agents.md).
