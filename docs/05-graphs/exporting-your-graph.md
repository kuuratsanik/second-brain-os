# Exporting the graph

Obsidian's graph view is a viewer. To compute anything, you need the graph
outside it.

## Export

```bash
python3 scripts/graph_export.py ~/brain edges.csv
python3 scripts/graph_export.py ~/brain graph.graphml --format graphml
```

The script parses every wikilink into an edge list and has no dependencies. CSV
is a two-column `source,target` list for code. GraphML is for Gephi and also
carries each page's `type` as a node attribute.

## Analysis

```python
import networkx as nx, csv

g = nx.DiGraph()
with open("edges.csv") as f:
    next(f)
    g.add_edges_from(tuple(r) for r in csv.reader(f))

print(nx.number_weakly_connected_components(g))
print(sorted(nx.pagerank(g).items(), key=lambda kv: -kv[1])[:10])
print([n for n in g if g.in_degree(n) == 0])
```

Three questions in ten lines: how fragmented is the vault, which pages are
structurally central, and what is unreachable.

PageRank on a knowledge graph is worth running once. The top pages are what your
vault is actually about, which is reliably different from what you would say it
is about.

## Betweenness, the one worth the compute

```python
b = nx.betweenness_centrality(g)
```

Betweenness measures how often a page sits on the shortest path between two
others. High-betweenness pages are the bridges between clusters.

They matter for two reasons. They are your most valuable pages, holding
connections no single source contained. And they are the fragile points: if a
bridge page is wrong or gets deleted in a merge, two areas of the vault silently
stop informing each other.

## Graph databases

[Kuzu](https://github.com/kuzudb/kuzu) is an embedded, serverless graph database
with Cypher queries, and querying your own notes with it is a fun evening. Its
repository was archived by its owner on 10 October 2025 and is read-only; earlier
releases still work, but do not build anything long-lived on it without checking
the current state. [Neo4j](https://neo4j.com) is the full server version and is
overkill unless you are building something on top.

Be clear about what this is: an analysis layer, not a replacement. The markdown
stays canonical, the database is a rebuildable derivative. The moment you start
writing knowledge that exists only in the database, you have lost the
portability that made the whole approach worth choosing.

## Gephi

For looking rather than computing. Load the GraphML, run ForceAtlas2, size nodes
by degree, colour by type. It renders large graphs in a way Obsidian cannot, and
it is what to use if you want a screenshot worth showing.

## Keep it in sync

The export is a snapshot and it is stale immediately. Regenerate it rather than
maintaining it, and never edit the exported graph expecting the vault to follow.

## Next

[Graph metrics worth tracking](metrics.md)
