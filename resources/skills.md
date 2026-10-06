# Skills and agents

Counted individually: a repo shipping fifteen skills counts as fifteen, because
that is what you install. Skill, command and subagent counts for other
repositories were read from each repository's folder listing or README on
5 October 2026. Where the two disagree, the entry says so. Star counts are from
the GitHub API as of 5 October 2026.

## This repo

| Type | Count | Where |
|---|---|---|
| Skills | 25 | [`skills/`](../skills/README.md). One per workflow in the guide |
| Commands | 75 | [`commands/`](../commands/README.md). Scoped entry points into those skills |
| Subagents | 6 | [`agents/`](../agents/README.md). Four of them read-only by design |
| Scripts | 4 | [`scripts/`](../scripts/README.md). Link check, stats, graph export, chat import |

Plain `SKILL.md` files, so they work with any agent that reads the Agent Skills
format.

## Implementations of this pattern

| Repo | Stars | Ships |
|---|---|---|
| [AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | 15,364 | 15 skills, 3 subagents. Self-organizing vault with role presets |
| [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) | 4,676 | 47 commands on eight platforms, per its README |
| [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) | 2,418 | 1 skill covering the full ingest, compile, query, lint loop |
| [ballred/obsidian-claude-pkm](https://github.com/ballred/obsidian-claude-pkm) | 1,875 | 10 skills, 4 subagents. A complete starter kit |
| [coleam00/second-brain-starter](https://github.com/coleam00/second-brain-starter) | 795 | 1 skill that interviews you and generates a build plan |
| [NicholasSpisak/second-brain](https://github.com/NicholasSpisak/second-brain) | 735 | 4 skills, npm installer, close to the original gist |
| [micuintus/llm-wiki](https://github.com/micuintus/llm-wiki) | 28 | 1 skill, deliberately minimal, no dependencies. Good counterpoint |

The last one is small on purpose and still worth reading. Star count measures
reach, not quality, and in this corner of the ecosystem it mostly measures who
posted about it.

## General skill libraries

Not second-brain specific, but this is where the format itself is defined and
where the best-written examples live.

| Repo | Stars | Ships |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 295,627 | 15 skills. An agentic skills framework and development methodology |
| [anthropics/skills](https://github.com/anthropics/skills) | 179,781 | 19 skills. The official reference for the format |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 55,105 | Commands, hooks, workflows and tooling for Claude Code |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 35,238 | A curated index of 1,000+ community skills |

## Graph builders

| Repo | Stars | What it does |
|---|---|---|
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | 124,043 | A `/graphify` skill that turns any folder of code, docs, PDFs and screenshots into a queryable graph. Every edge labelled extracted or inferred |

Graphify is built around a folder of mixed files such as `raw/`. Per its
[README](https://github.com/Graphify-Labs/graphify/blob/v8/README.md), code is
parsed locally with tree-sitter, with no model call. Docs, PDFs and images go
through your assistant's model, or an API key you configure. It writes an
interactive `graph.html` and can write an Obsidian-openable folder with
`--obsidian`. Edges are tagged `EXTRACTED` or `INFERRED`. The README's
benchmark table is the project's own, and some of its samples are small
(n=6 to n=300), so treat the figures as unreplicated.

## Writing your own

Three properties make a skill worth writing: you do it repeatedly, you have
opinions about how, and the opinions are not obvious enough for a model to
guess.

Read `anthropics/skills` for the format and one of the small implementations
above for a full worked example. Details in [skills and
commands](../docs/06-agents/skills-and-commands.md).
