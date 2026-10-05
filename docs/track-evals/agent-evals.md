# Agent Evals

A single completion is a function; an agent is a process. It plans, calls tools, reads results, and recovers (or doesn't) from its own mistakes. Evaluating the final answer alone is like reviewing a chess game by the last move. This page builds on [designing evals](designing-evals.md).

## Trajectories, not just outcomes

Log the whole trajectory: every model turn, tool call, tool result, and retry. Then evaluate at two levels:

- **Outcome**: did the task complete, and is the end state correct? Best checked against the *environment* (the file exists, the row was inserted, the tests pass), not the agent's claim that it finished. Agents declare victory fluently.
- **Trajectory**: was the path reasonable? Count steps, detect loops, flag tool errors that were silently ignored. Two agents with equal success rates are not equal if one takes 40 turns and burns 20x the tokens.

## Tool-call correctness

The most mechanical and highest-yield checks:

- Right tool chosen for the intent.
- Arguments valid and correctly extracted from context (IDs, dates, filters — this is where agents quietly fail).
- Ordering constraints respected (`search` before `answer`, `read` before `write`).
- Error handling: feed a tool failure mid-trajectory and check the agent retries or reports rather than hallucinating a result.

These are code assertions over the trace, not judge calls. Save the [llm as judge](llm-as-judge.md) for "was the plan sensible" questions.

## Environment-based evals

The gold standard: give the agent a sandboxed environment (a Docker container, a seeded database, a mock API) and grade the *state* afterwards with executable checks. Deterministic setup, programmatic teardown, no grader ambiguity. It is more work to build than a golden set of transcripts, and worth it for anything that mutates state.

## Harness benchmarks, 2026 edition

Public benchmarks are for comparing models and harnesses, not for measuring your product — but they show what good environment-based evals look like:

- [SWE-bench](https://www.swebench.com/) family — real GitHub issues, graded by the repo's tests; SWE-bench Verified is, per the [SWE-bench README](https://github.com/SWE-bench/SWE-bench), "a subset of 500 problems that real software engineers have confirmed are solvable". The leaderboard data in the [swe-bench.github.io repository](https://github.com/SWE-bench/swe-bench.github.io) lists entries to February 2026; the top Verified entry, 79.2%, is dated 5 December 2025; vendors report their own numbers for newer models, so check the model card and the harness behind any figure.
- [Terminal-Bench](https://www.tbench.ai/) — [2.0](https://github.com/laude-institute/terminal-bench-2) has 89 task directories, each with, in its README's words, "several hours of human and LM-assisted validation", run in containers and graded by executable tests. The cleanest template to steal from.
- [GAIA](https://arxiv.org/abs/2311.12983) — general assistant tasks needing web, tools and multi-step reasoning.
- [tau2-bench](https://github.com/sierra-research/tau2-bench) — tool-agent-*user* interaction: a simulation framework for customer-service agents in which the agent must follow a domain policy ([README](https://github.com/sierra-research/tau2-bench)).
- [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals) — roughly 130 evaluation directories (about 250 `@task` definitions) in the repository's `src`, including SWE-bench, GAIA and tau2, under one framework. New evals are being added through an external register rather than to `src`; the repo's EVAL_REGISTER.md announces that `src` stops accepting eval submissions as of 8 May 2026.

## CI integration

Evals belong in the pipeline, not a notebook:

- Small smoke suite (deterministic checks only) on every PR; full suite nightly and before releases.
- Gate merges on a threshold; run N trials per case and gate on the mean.
- Pin model versions in CI, and treat a model bump as a change that must pass the suite like any other.

Tooling that makes this less painful is surveyed in [tooling](tooling.md).
