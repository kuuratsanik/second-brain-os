# Tools

The ecosystem survey. Status and release dates were checked against each project's README and PyPI page on 5 October 2026. Microsoft's batch-indexing GraphRAG is in maintenance mode; the incremental, memory-oriented projects below are where the releases are.

## Memory and graph-RAG frameworks

- [Graphiti](https://github.com/getzep/graphiti) — temporal knowledge graphs for agent memory, from Zep. Every edge carries a validity window, contradictions invalidate rather than overwrite, and point-in-time queries work. Built for long-running agent memory; it is the open-source core of Zep's hosted [memory platform](https://www.getzep.com). Supports Neo4j, FalkorDB and Amazon Neptune; Kuzu is deprecated.
- [Cognee](https://github.com/topoteretes/cognee) — self-hosted memory engine whose retrieval draws on graph, vector and code context. Python and TypeScript SDKs, an MCP server, Claude Code and Codex plugins, and a separate Rust implementation ([cognee-rs](https://github.com/topoteretes/cognee-rs)). Version 1.6.2 was released on 29 September 2026.
- [LightRAG](https://github.com/HKUDS/LightRAG) — the pragmatic GraphRAG: dual graph-plus-vector index, incremental updates, multiple storage backends (Neo4j, PostgreSQL, MongoDB). EMNLP 2025 paper; release 1.5.7 on 2 September 2026. Its default stores are in-memory and meant only for testing; use PostgreSQL, Neo4j or another backend beyond that.
- [fast-graphrag](https://github.com/circlemind-ai/fast-graphrag) — Circlemind's take, built on PageRank graph exploration. Last PyPI release 0.0.5, April 2025; last commit November 2025.
- [microsoft/graphrag](https://github.com/microsoft/graphrag) — the original, now maintenance-mode. Read it, do not build on it; context in [GraphRAG](graphrag.md).

## Framework integrations

- [LlamaIndex property graph index](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/) — the framework-native option for LlamaIndex users: pluggable extractors (including the schema-enforcing `SchemaLLMPathExtractor`, present in `llama-index-core` 0.14.25) and retrievers over property graph stores.
- [LangChain LLMGraphTransformer](https://reference.langchain.com/python/langchain-neo4j/graph_transformers/llm/LLMGraphTransformer) — documents in, graph documents out. The class exists in two packages, `langchain-neo4j` (0.10.0, the one linked) and `langchain-experimental` (0.4.2); they carry separate copies, so import from the package you pin.
- [Neo4j LLM Knowledge Graph Builder](https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/) — a point-and-click pipeline, with a hosted instance, from PDFs, documents, web pages, YouTube videos and Wikipedia to a Neo4j graph; an active Neo4j Labs project, Apache-2.0 ([repository](https://github.com/neo4j-labs/llm-graph-builder)). Good for a first look at what extraction does to your material before writing any code.
- [FalkorDB GraphRAG-SDK](https://github.com/FalkorDB/GraphRAG-SDK) — SDK over FalkorDB with optional ontology (schema) constraints on extraction. Version 1.0 was announced in April 2026; 1.4.0 is on PyPI from August 2026.

## Visualisers

[Gephi](https://gephi.org) remains the workhorse for offline analysis of an exported graph — load GraphML, run layout and community colouring, find the structure you did not know was there. Neo4j's bundled Browser and Bloom cover the database-native case.

## Obsidian graph tooling

The built-in graph view is a painting, not an instrument; plugins do the real work. [InfraNodus](https://github.com/noduslabs/infranodus-obsidian-plugin) adds proper network analysis over a vault — topical clusters, centrality, structural gaps — plus AI question generation over the gaps. [Extended Graph](https://github.com/ElsaTam/obsidian-extended-graph) upgrades the native view with filtering and per-type styling. The Obsidian Hub keeps a current [graph plugins list](https://publish.obsidian.md/hub/02+-+Community+Expansions/02.01+Plugins+by+Category/Graph+plugins).

## Choosing

Agent memory: Graphiti or Cognee. Query a document corpus: LightRAG. Already inside LlamaIndex or LangChain: their native extractors, writing to a store from [graph stores](graph-stores.md). Curated vault: your links are the graph; add InfraNodus when you want the analytics.
