# GraphRAG and where it fits

GraphRAG is the approach of building a graph from a corpus first, then answering
questions against the graph rather than against raw chunks. Microsoft Research
published the best-known version, [From Local to Global: A Graph RAG Approach to
Query-Focused Summarization](https://arxiv.org/abs/2404.16130).

In outline: extract entities and relationships from every document, group
densely connected entities into communities, summarise each community, and
answer from the summaries. This page covers how that compares with a vault. The
four stages, their cost and the cheaper successors are in the
[GraphRAG handbook page](../track-graph/graphrag.md).

## Why it exists

It targets a specific failure of chunk retrieval: questions about the corpus as
a whole. "What are the main themes here" cannot be answered by retrieving the
five most similar chunks, because no chunk contains the answer. It has to be
assembled from everything.

That class of question is exactly what people want from a second brain and
exactly what similarity search is worst at.

## What your vault already has

Read the pipeline again against a well-maintained wiki and most of it is already
built.

Entity extraction is what ingestion does when it writes entity pages.
Relationships are the wikilinks, with types if you added them. The graph is the
vault. What is missing is the community layer: the detection of clusters and the
summaries over them.

And that missing piece has a manual equivalent you are already writing.
Synthesis pages are community summaries, produced by a model that read the
sources rather than by an algorithm clustering entities.

## Whether to run it

Probably not, at personal scale, and the honest reason is size. The approach
earns its cost on corpora too large to have been curated by hand. A few thousand
curated pages with real links do not need automated community detection to find
their own themes; you can see the clusters in the graph view.

There is a case for it as an audit rather than as a retrieval system. Running
community detection over your exported graph and comparing the algorithmic
clusters against your synthesis pages tells you where the vault has themes you
have not noticed. That is a once-a-quarter exercise, not infrastructure.

## Related research worth reading

[HippoRAG](https://arxiv.org/abs/2405.14831) applies personalised PageRank over a knowledge graph for multi-hop
questions, which is a more direct analogue of what an agent does walking links
outward from a starting page.

Read the papers themselves rather than summaries of them. Both are specific
about the conditions their results hold under, and those conditions are what
decide whether the approach transfers to your situation.

For the implementation side, see the handbook's [GraphRAG](../track-graph/graphrag.md)
and [building graphs with LLMs](../track-graph/building-graphs-with-llms.md).

## Next

[Exporting the graph](exporting-your-graph.md)
