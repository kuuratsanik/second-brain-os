# Jev Resources

Jev launched on 15 September 2026 (per the launch post, which could not be re-checked). Links were checked on 21 September 2026; on 5 October 2026 the checking environment could not reach typesafe.ai, LangChain, Wikipedia, DataCamp, dev.to, MindStudio, KDnuggets, Substack, Pydantic, LiteLLM, Cloudflare, Netlify, Vercel or OpenRouter, so those entries and their descriptions are not re-verified. This page will age fast. Concepts in [system one models](system-one-models.md).

## Official

- [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) — the launch post; claims, pricing, naming
- [TypeSafe docs](https://docs.typesafe.ai/) and [System One concepts](https://docs.typesafe.ai/concepts/system-one) — API shape, primitives, limits
- [HTTP API reference](https://docs.typesafe.ai/api) and [workflow evals](https://evals.typesafe.ai/) — the vendor's own benchmark methodology
- [Console](https://console.typesafe.ai/) — waitlist, keys, playground
- SDKs: [JavaScript](https://github.com/typesafe-ai/typesafe-sdk-js), [Python](https://github.com/typesafe-ai/typesafe-sdk-python)
- [WorkflowEvals](https://github.com/typesafe-ai/WorkflowEvals) — code to reproduce the evals.typesafe.ai results
- [TypeSafe agent skills](https://github.com/typesafe-ai/skills) — an official skill for designing System One workflows from Claude Code and other agents
- [system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python) — a drop-in `TypeSafeClient` replacement backed by OpenAI, Anthropic or Gemini LLM APIs, for comparing cost and quality against Jev

## Third-party explainers and writeups

- [Wikipedia: Jev (AI model)](https://en.wikipedia.org/wiki/Jev_(AI_model)) — neutral summary; company, funding, versions
- [LangChain: building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev) — the agent-stack integration; see [Jev in an agent stack](jev-in-an-agent-stack.md)
- [DataCamp: System One models and Jev](https://www.datacamp.com/blog/system-one-models-jev) — a comparative benchmark table; its numbers are secondary, so check the primary eval before quoting them
- [Valyu: how to use Jev](https://dev.to/valyuai/how-to-use-jev-a-practical-guide-to-typesafes-system-one-model-g5e) — a practical guide with patterns and gotchas
- [MindStudio launch coverage](https://www.mindstudio.ai/blog/jev-system-one-model-launch) — simulator demos with real cost numbers
- [AI News: ChatGPT pioneer launches Jev](https://www.artificialintelligence-news.com/news/chatgpt-pioneer-launches-jev-model-for-programmatic-logic/) — founder background
- [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev) — community-maintained link list, demos, integrations
- [langchain-typesafe](https://pypi.org/project/langchain-typesafe/) — the LangChain integration: `TypeSafeClassifier` plus experimental router and guardrail middleware
- Gateway integrations: [Vercel AI Gateway](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway), [OpenRouter](https://openrouter.ai/labs/jev/compile), [Pydantic AI](https://pydantic.dev/docs/ai/models/typesafe/), [LiteLLM](https://docs.litellm.ai/docs/pass_through/typesafe), [Cloudflare](https://developers.cloudflare.com/ai/models/typesafe/jev/), [Netlify](https://www.netlify.com/changelog/typesafe-jev-ai-gateway/)

## Independent evaluations

None of these are affiliated with TypeSafe, and each covers specific tasks and one point in time. Read their protocols before carrying a number across.

- [Jevals](https://github.com/Jevals/jevals-data) — Jev against six LLMs on PubMedQA, Banking77 and HelpSteer2, with per-decision logs; release of 18 September 2026
- [JevBench](https://github.com/fstandhartinger/jevbench) — cross-model benchmark of typed-decision systems; its README states it is not affiliated with or endorsed by TypeSafe
- [jev-calibration-audit](https://github.com/jujumilk3/jev-calibration-audit) — abstention, question-shape and language tests, with per-call logs
- [jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration) — calibration on public benchmarks and on synthetic tickets with an unstated rule

The community [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev) index lists many more.

## Sceptical takes

- [Anthony Maio: the language model that won't talk](https://anthonymaio.substack.com/p/jev-the-language-model-that-wont) — best critical read; calibration and distribution shift remain unproven
- [KDnuggets: what everyone is getting wrong about Jev](https://www.kdnuggets.com/what-everyone-is-getting-wrong-about-typesafe-ais-jev) — "zero hallucinations" means zero out-of-schema outputs, not zero wrong answers
- [MindStudio: RLCD vs RLHF](https://www.mindstudio.ai/blog/typesafe-jev-rlcd-vs-rlhf) — what the training claim actually asserts

Bear in mind that the headline speed and cost multipliers still trace back to TypeSafe's own evals. At launch there were no independent evaluations; the ones above appeared within weeks, are small and task-specific, and do not reproduce the vendor's workflows. Treat them as a reason to run your own test, not as a verdict.

## Start here

1. Read the launch post, then Maio's sceptical piece straight after — vendor claim and counterweight in one sitting.
2. Work through [what Jev is good for](what-jev-is-good-for.md) and decide whether any of your workloads are Jev-shaped.
3. Join the waitlist, then run the triage eval from [getting started](getting-started.md) against your own labelled data before believing any benchmark.
