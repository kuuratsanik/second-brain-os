# System One Models

Most AI products today are built on large language models: you send text in, the model writes text back, one token at a time. That is slow and expensive when all your software actually needs is a decision. "System One models" are a new category — introduced by TypeSafe AI on 15 September 2026 with a model called Jev — built for exactly that gap: fast typed decisions instead of slow text generation.


The course side of this subject is [Module 3: cheap decisions](../course-3-gate/cheap-decisions.md) — the gate pattern this class of models usually serves.

## The Kahneman framing

The name borrows from Daniel Kahneman's *Thinking, Fast and Slow*. System 1 is fast, intuitive judgement; System 2 is slow, deliberate reasoning. LLMs, in this framing, are System 2 machines: they reason out loud, in prose. TypeSafe's pitch is that a large share of what software asks a model to do — classify, route, score, gate — is System 1 work, and paying LLM latency and cost for it is waste. Their founder, Diogo Almeida (ex-OpenAI, worked on RLHF and ChatGPT), calls it "a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out".

## What Jev actually returns

Jev is non-autoregressive: it does not generate text at all. You send it a `state` (strings, JSON objects, or arrays of text) plus one or more typed questions, and it answers them all in a single parallel pass. Three primitives:

- `Choice` — pick one of the defined options; the answer is the chosen label plus a probability per option and a confidence value. TypeSafe's limit is 255 options, per the third-party [jev-usecases](https://github.com/vamsikrishna2421/jev-usecases) catalog; the SDK does not encode it.
- `Score` — place the input on an ordered scale you describe; the answer is the probability-weighted expected level, a confidence value and a probability per level. The SDK requires a non-empty ordered list of level descriptions; the same catalog gives a range of 2–10 levels.
- `Noul` — a yes/no judgement returned as the probability of yes, between 0 and 1

The answer shapes come from the [Python SDK source](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/src/typesafe_sdk/_schemas/models.py). TypeSafe says the probabilities are calibrated and that it trained for this with a method it calls RLCD (Reinforcement Learning for Calibrated Decisions), which optimises for honest confidence rather than pleasing a human rater. Its [agent skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md) says the models "are trained for calibrated decisions" and tells users to validate performance in their own domain.

## Honest caveats

At launch nearly every number was the vendor's own, and the headline numbers still are:

- The headline claims — roughly 200x faster and up to 400x cheaper than frontier LLMs — come from benchmarks built by TypeSafe's own team, which the company itself admits sit at the high end. The code for those evals is public ([WorkflowEvals](https://github.com/typesafe-ai/WorkflowEvals)).
- "Zero hallucinations" really means zero *out-of-schema* outputs. Jev cannot invent an option you did not define; it can still pick the wrong one.
- Architecture, model size, and weights were undisclosed at launch, and no peer-reviewed paper had been published. Calibration under distribution shift is contested: sceptics like Anthony Maio argued it was unproven, and independent tests since then are mixed. One found probabilities near calibrated on three public benchmarks but overconfident on an unseen rule ([jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration)); another found calibration changed sharply when the abstain option was removed ([jev-calibration-audit](https://github.com/jujumilk3/jev-calibration-audit)).

Treat the mechanism as real and the vendor's magnitudes as unconfirmed; the independent evaluations that now exist are listed in [resources](resources.md) and cover specific tasks, not the headline workflows. For what tasks it plausibly fits, see [what Jev is good for](what-jev-is-good-for.md); to try it, see [getting started](getting-started.md); for sources, see [resources](resources.md).
