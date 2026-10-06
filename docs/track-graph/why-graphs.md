# Why Knowledge Graphs

An agent's memory problem is not storage. It is that facts arrive connected and get stored flat. A knowledge graph keeps the connections: entities as nodes, relationships as typed edges, so that "what does X have to do with Y" is a walk rather than a guess.


This handbook is about graphs as agent memory in general; the second-brain guide's own [graphs section](../05-graphs/graph-basics.md) covers the vault-specific side — wikilinks as edges, typed links, Obsidian's graph view.

## What vector RAG cannot do

Embedding retrieval answers one shape of question well: "find me passages that sound like this". It fails predictably on two others.

- **Multi-hop questions.** "Which of my clients use the framework my colleague warned me about?" No single chunk contains the answer; it lives in the join. Similarity search retrieves fragments of each half and leaves the model to hallucinate the bridge.
- **Global questions.** "What are the recurring themes across everything I have read this year?" The answer is a property of the corpus, not of any five chunks.

Graphs handle both, because edges are joins you computed once at ingest, and the graph's cluster structure is the theme layer. [GraphRAG](graphrag.md) is the pattern built on exactly this observation.

## What graphs cannot do

The honest counterweight. Graphs are only as good as the extraction that built them, and extraction is lossy, expensive and occasionally wrong. Vector search needs no schema, tolerates any input, and its failures are visible at query time rather than baked in at ingest. Fuzzy recall — "something about pricing, maybe a podcast" — is embedding territory, and a graph is useless for it. The benchmark behind [When to Use Graphs in RAG](https://github.com/GraphRAG-Bench/GraphRAG-Benchmark) (ICLR 2026) starts from the observation that GraphRAG frequently underperforms vanilla RAG on many real-world tasks, which is why its authors set out to map where graphs help.

## Hybrid is the default now

The current frameworks mostly run both. Vectors find the entry points; the graph expands from them. [LightRAG](https://github.com/HKUDS/LightRAG) describes a dual-layer architecture that manages a knowledge graph and vector embeddings together, and [Graphiti](https://github.com/getzep/graphiti), the open-source core of Zep's hosted platform, combines semantic embeddings, BM25 keyword search and graph traversal in one retrieval step. The design question is no longer graph or vectors but where the graph lives and who writes it — see [graph stores](graph-stores.md).

## When not to bother

Skip the graph when:

- The corpus is small enough to fit in a context window. Read it instead.
- Questions are single-hop lookups. Vector or even grep-grade search wins on cost.
- Nobody will maintain the schema. A stale graph is worse than no graph, because it answers confidently from old edges.
- You already keep a curated wiki with typed links. That is a graph; you built it by hand, and it is probably better than one an LLM extracted.

The threshold is roughly this: bother when your questions join facts across documents more often than they retrieve facts from one. Below that line, the extraction pipeline in [building graphs with LLMs](building-graphs-with-llms.md) is cost without payoff.
