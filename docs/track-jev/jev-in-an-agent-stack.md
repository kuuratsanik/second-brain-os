# Jev in an Agent Stack

The most credible early use of Jev is not replacing an LLM but sitting next to one. Agent loops are full of small bounded decisions — which model, which tool, is this safe, are we done — and today each one costs a full LLM call. The emerging pattern, visible in LangChain's [`langchain-typesafe` package](https://pypi.org/project/langchain-typesafe/) and its [harness writeup](https://www.langchain.com/blog/building-a-harness-with-jev) (the writeup could not be re-checked), is to hand those decisions to a System One model and keep the LLM for the parts that need language. Background in [system one models](system-one-models.md).

## Jev in front of the loop

- **Router.** Jev classifies the incoming request and routes it: cheap fast model for simple lookups, expensive reasoning model for hard cases. `langchain-typesafe` ships an experimental `ModelRouterMiddleware` that does this with a `Choice` question. At 70–500ms claimed latency, the routing step is nearly free relative to the call it saves; an independent benchmark measured p95 latency of 653–693 ms through a gateway (see [what Jev is good for](what-jev-is-good-for.md)), so measure your own.
- **Triage gate.** A `Noul` question ("does this need a human?") in front of the agent keeps junk out of the loop entirely.

## Jev inside the loop

- **Tool-call guardrails.** LangChain's experimental `AutoModeMiddleware`, in `langchain-typesafe`, classifies calls to explicitly configured tools and blocks risky calls before execution — a typed judgement, not a second LLM opining on the first. The package says its experimental APIs may change without notice.
- **State checks.** "Is the task complete?", "did that tool call succeed?", "is the user frustrated?" — each is a typed question over the transcript, and because Jev answers all questions in one parallel pass, asking ten costs barely more time than asking one.

The LangChain integration exposes this as `TypeSafeClassifier`, a LangChain `Runnable`: you pass `.invoke()` a mapping with a `state` and a dict of questions and get back typed answers (`result.choices[...]`, `result.nouls[...]`, `result.scores[...]`) with probabilities, which your code — not a model — then acts on. The package was at version 0.0.1a3, an alpha, when checked ([README](https://pypi.org/project/langchain-typesafe/)).

## Failure handling with confidence thresholds

The probability on every answer is the design's load-bearing part. The pattern TypeSafe's own [agent skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md) recommends is to use probabilities to guide behaviour with thresholds evaluated on your own data and the consequences of error:

- Set a threshold per decision, priced by the cost of being wrong. Auto-approving a refund might need 0.98; picking a support queue might be fine at 0.7.
- Below threshold, escalate — to an LLM, to a human, or to a safe default. Jev becomes the fast path, not the only path.
- Log the probabilities. Jev gives no rationale, so the state you sent plus the scores you got back are your entire audit trail. Keep them.

One honest caution: this whole scheme assumes the probabilities are genuinely calibrated, which is TypeSafe's central claim. Independent tests are mixed: one found probabilities near calibrated on public benchmarks but overconfident on a rule the text did not state, with boolean answers underconfident and choice and score answers overconfident ([jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration)), and that study notes the probabilities are quantised to 0.01 and frequently exactly 0 or 1. Sceptics note that a confident score is not by itself evidence the prediction deserves trust. Start with conservative thresholds and measure against your own labels. Practical setup in [getting started](getting-started.md); task fit in [what Jev is good for](what-jev-is-good-for.md).
