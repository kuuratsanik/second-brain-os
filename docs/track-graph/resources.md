# Resources

Curated, not comprehensive. Paper venues, repositories and package versions were checked against the projects' own READMEs and PyPI pages on 5 October 2026. The checking environment could not reach arXiv, Neo4j, DeepLearning.AI, Medium, Microsoft's documentation site or Gephi, so links to those were last confirmed live in September 2026 and their descriptions below are not re-verified.

## Papers

- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) — the Microsoft GraphRAG paper. Read it for the problem framing as much as the method; the [GraphRAG](graphrag.md) page is the short version.
- [HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models](https://arxiv.org/abs/2405.14831) — knowledge graph plus personalised PageRank for multi-hop retrieval, NeurIPS 2024 per the [HippoRAG repository](https://github.com/OSU-NLP-Group/HippoRAG). The closest formal analogue to an agent walking links outward from a page.
- [From RAG to Memory: Non-Parametric Continual Learning for Large Language Models](https://arxiv.org/abs/2502.14802) — HippoRAG 2, ICML 2025. The repository says it improves multi-hop retrieval and sense-making without sacrificing performance on simpler tasks; that is the authors' claim, not an independent result.
- [LightRAG: Simple and Fast Retrieval-Augmented Generation](https://arxiv.org/abs/2410.05779) — dual-level graph-plus-vector retrieval with incremental updates; the [repository](https://github.com/HKUDS/LightRAG) lists it as an EMNLP 2025 paper.
- [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) — the design paper behind Graphiti; the best written account of why agent memory needs time on its edges.
- [When to Use Graphs in RAG](https://arxiv.org/abs/2506.05690) — ICLR 2026 per its [benchmark repository](https://github.com/GraphRAG-Bench/GraphRAG-Benchmark), which says GraphRAG frequently underperforms vanilla RAG on many real-world tasks. A comparative analysis of where graph retrieval helps and where it is overhead; read it after the papers above.

## Guides and courses

- [Knowledge Graphs for RAG](https://www.deeplearning.ai/courses/knowledge-graphs-rag) — DeepLearning.AI short course with Neo4j. A few hours, hands-on, Cypher included.
- [Neo4j GraphAcademy: knowledge graphs and GraphRAG](https://graphacademy.neo4j.com/knowledge-graph-rag/) — free, deeper, self-paced.
- [Building Knowledge Graphs with LLM Graph Transformer](https://medium.com/data-science/building-knowledge-graphs-with-llm-graph-transformer-a91045c49b59) — Tomaz Bratanic's walkthrough of schema-constrained extraction; the single most useful practical article on the topic.
- [Implementing "from local to global" GraphRAG with Neo4j and LangChain](https://neo4j.com/blog/developer/global-graphrag-neo4j-langchain/) — the full pipeline reproduced step by step, so you see the costs concretely.
- [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/) — Microsoft Research on deferring indexing cost to query time.

## Repos worth reading

Read [Graphiti](https://github.com/getzep/graphiti) for temporal edge handling and entity resolution done properly; [LightRAG](https://github.com/HKUDS/LightRAG) for a compact end-to-end pipeline you can hold in your head; [microsoft/graphrag](https://github.com/microsoft/graphrag) as the frozen reference implementation. The live survey is in [tools](tools.md).

## Start here

1. Read [why graphs](why-graphs.md) and apply the threshold test to your actual corpus and actual questions. If you fall below the line, stop; your wiki links already are the graph.
2. Take the DeepLearning.AI short course, then run LightRAG over a hundred of your own documents and read the extracted triples. Nothing teaches extraction's failure modes faster.
3. Read the Zep paper, then decide your store deliberately using [graph stores](graph-stores.md) — files first, server only when concurrent writers force it.
