# Getting Started With Jev

This page was written from what was published as of 21 September 2026 and re-checked on 5 October 2026, when TypeSafe's own site, docs and eval pages were unreachable from the checking environment. Facts about the SDKs come from the official [Python](https://github.com/typesafe-ai/typesafe-sdk-python) and [JavaScript](https://github.com/typesafe-ai/typesafe-sdk-js) repositories; vendor claims that could not be re-checked are marked. Expect it to date quickly.

## Access

Jev is in waitlisted early access. You sign up at [console.typesafe.ai](https://console.typesafe.ai/), and TypeSafe says it is admitting developers off the waitlist in batches. API keys live at `console.typesafe.ai/settings/keys`. TypeSafe also describes a free playground on the console. Neither could be re-checked. Other platforms list Jev too (Vercel AI Gateway, Netlify AI Gateway, Cloudflare Workers AI, OpenRouter), each with its own request shape, credentials and billing; the community [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev#choose-where-to-call-jev) table links each provider's page, which this page did not check.

## The API shape

The entire API is one endpoint — `POST https://api.typesafe.ai/v1/systemone` — with the default model `jev-latest` (currently `jev-1.13.0`). The base URL, path and default model come from the Python SDK's [constants](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/src/typesafe_sdk/constants.py); `jev-1.13.0` is the default in TypeSafe's [WorkflowEvals](https://github.com/typesafe-ai/WorkflowEvals) repository. Official SDKs: `pip install typesafe-sdk` (0.7.2, Python 3.10 or newer) and `npm install @typesafe-ai/sdk` (Node.js 20 or newer), both reading `TYPESAFE_API_KEY` from the environment.

A request is a `state` (string, JSON object, or array of text — text only for now) plus named questions using three primitives:

```python
from typesafe_sdk import Choice, Score, Noul, TypeSafeClient

questions = {
    "team": Choice(instructions="Which team should handle this",
                   criteria={"billing": "Payment issues", "technical": "Bugs"}),
    "frustration": Score(instructions="Customer frustration level",
                         criteria=["Calm", "Frustrated but civil", "Very angry"]),
    "refund": Noul(instructions="Customer explicitly requesting a refund"),
}

with TypeSafeClient() as client:
    response = client.system_one(
        state="I was charged twice and I am furious. Refund me today.",
        questions=questions,
    )

print(response.choices["team"].choice, response.choices["team"].probabilities)
print(response.scores["frustration"].score)  # expected level, may fall between integers
print(response.nouls["refund"].noul)         # probability of yes, 0 to 1
```

The call and the response fields (`choices`, `scores`, `nouls`, and per-answer `choice`, `probabilities`, `confidence`, `score`, `noul`) are from the Python SDK's README and source. The question objects were constructed and serialised locally with SDK 0.7.2; the call itself was not run against the live API.

All questions are answered in one parallel pass. Limits TypeSafe documents, which could not be re-checked: 64k tokens of state, 32k for state plus the longest question, up to 255 options per `Choice`. The SDK's schema does confirm that output tokens are "currently free of charge"; the $0.042 per million input tokens figure is TypeSafe's published price and could not be re-checked.

## A realistic first project

Support-ticket triage is the canonical starter: take 200 historical tickets you have already labelled, ask Jev the three questions above, and compare its answers and probabilities against your labels. This gives you the two things that matter — accuracy on *your* distribution, and whether the confidence scores are honest enough to set thresholds against, per [Jev in an agent stack](jev-in-an-agent-stack.md). Treat your own eval as the real milestone.

Mind the reported gotchas: third-party guides say Jev reads literally (negations bite), cannot count, does not order dates, and degrades with bloated context, so retrieve and filter in code before sending state. TypeSafe's own [agent skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md) says to treat demo results as examples to evaluate, not as permanent model limitations, and to keep API credentials server-side in web apps. Test adversarial injection if state includes user text.

## What is still unknown or unreleased

Plainly: at launch, architecture, model size, and weights were undisclosed, and TypeSafe published no self-hosting, fine-tuning, image/audio/video input, rate-limit or SLA documentation; none of that could be re-checked. Independent evaluations now exist: [JevBench](https://github.com/fstandhartinger/jevbench) states it is not affiliated with TypeSafe, and [Jevals](https://github.com/Jevals/jevals-data), [jev-calibration-audit](https://github.com/jujumilk3/jev-calibration-audit) and [jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration) publish their data. Their results are task-specific and mixed; see [resources](resources.md). Nobody has shown the pricing is sustainable rather than subsidised. No general-availability date was announced as of 21 September. If any of these are blockers, wait — see [what Jev is good for](what-jev-is-good-for.md) for whether it is worth queueing for, and [resources](resources.md) for the docs.
