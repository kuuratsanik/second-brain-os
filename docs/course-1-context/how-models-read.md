# How models read context

A bigger context window looks like free capacity. It is not. The model reads every token you send, but it does not weigh them equally, and past a point each extra token makes the answer worse as well as slower and dearer. This page covers the mechanics; [The four places](the-four-places.md) covers the discipline built on top of them.

## Attention has a shape

In [Lost in the Middle](https://arxiv.org/abs/2307.03172) (Liu et al., 2023), models answered questions over a pile of retrieved documents while the single document containing the answer was moved through the pile. With 20 documents, GPT-3.5-Turbo scored 75.8% when the answer sat in the first document, 53.8% when it sat in the middle, and 63.2% at the end. The closed-book baseline — the same question with no documents at all — was 56.1%. With the answer physically present in the window but buried in the middle, the model did worse than with nothing.

The same U-shaped curve held across GPT-3.5-Turbo (4K and 16K), Claude 1.3 (including the 100K variant), MPT-30B-Instruct and LongChat-13B, and across piles of 10, 20 and 30 documents. Models attend strongly to the start of the window (primacy) and to the end (recency), and weakly to everything between. Newer models flatten the curve; none has removed it. Google's whitepaper [Context Engineering: Sessions & Memory](https://www.kaggle.com/whitepaper-context-engineering-sessions-and-memory) (Milam and Gulli, November 2025) calls the broader failure "context rot": as context grows, the model's ability to pay attention to critical information diminishes.


![Chart of accuracy by position of the relevant document in the window. Accuracy is highest at the start, dips lowest in the middle and recovers partly at the end. A reference line marks accuracy with no documents at all.](fig-lost-middle.svg)

## Every token costs four ways

The same whitepaper lists four practical limits on long context: the hard window limit, API cost, latency, and quality. The window limit is the one people fear and the one that bites last. Cost, latency and quality degrade continuously from the first unnecessary token.

Cost compounds in agent loops. Every turn resends the entire history, so a loop of N turns pays for its context roughly N times over. A 30-turn run carrying 20,000 tokens of dead weight does not waste 20,000 tokens; it wastes around 600,000. Latency scales the same way, and quality falls as the signal you care about drifts towards the weak middle of the window.

## Prompt caching pays for stillness

Providers will re-serve an unchanged prefix at a steep discount. Anthropic's [prompt caching](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching) prices cache reads at 0.1x the base input rate for most models — ten times cheaper — while a cache write costs 1.25x for the default 5-minute lifetime (2x for a 1-hour cache).

The catch is severity: a cache hit requires the prefix to be 100% identical, byte for byte, up to the cache breakpoint. The cache is hierarchical — tools, then system prompt, then messages — so editing one tool definition invalidates everything after it, and any change to the system prompt invalidates the whole message history cache. A timestamp in the system prompt guarantees a miss on every single call, silently costing you the full 10x. There is also a minimum cacheable length, between 512 and 4,096 tokens depending on the model, below which caching is skipped without any error.

## The shape of the fix

The mechanics point one way. Content that never changes belongs at the very front, where it is cheap (cached) and well attended (primacy). Content that matters right now belongs at the very end, where recency works for you. Everything large or transient belongs out of the window entirely, on disk, fetched when needed. That placement discipline is the next page, and the harness handbook has a [deeper treatment](../track-harness/context-engineering.md) of wiring it into a real agent.
