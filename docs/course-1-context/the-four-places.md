# The four places

[How models read](how-models-read.md) established the physics: attention favours the start and end of the window, every token costs, and caching only pays when the prefix never moves. The discipline that follows is simple to state. Every piece of context belongs in exactly one of four places, and most agent problems trace back to something sitting in the wrong one.


![Diagram of the context window in order: a byte-stable system prompt, a frozen tool set, history that grows and compacts, the goal, then a tail. Files on disk sit outside the window, and only their paths enter.](fig-four-places.svg)

## One: the system prompt

Only what is true on every call. Persona, hard rules, output format — nothing else. It must be byte-stable: no timestamps, no user names, no retrieved memories, no "current task". Anything dynamic in the system prompt breaks the cache on every request (system sits above messages in the [cache hierarchy](https://platform.claude.com/docs/en/build-with-claude/prompt-caching): tools, then system, then messages) and squanders the primacy slot on content that did not need it. Treat edits to it as releases, not tweaks.

## Two: the tools

The tool set is fixed for the whole conversation. Never add or remove definitions mid-run: tools sit first in the cache hierarchy, so touching one invalidates the entire cached prefix, and the model's behaviour shifts under it. When a tool must become unavailable, block the call instead — intercept it and return "this tool is disabled for this task" — leaving the definitions untouched. One sanctioned way to grow the visible tool set is tool search: deferred tools are appended inline as `tool_reference` blocks and, per the [API docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool), the cached prefix is untouched. The `inline-tools-2026-09-15` beta header is another: per the [prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), it lets you send a new definition in a `tool_addition` block in a mid-conversation system message, leaving `tools` as first sent, so the cached prefix still matches.

Definitions are expensive. Anthropic's [Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use) post (November 2025) measured a routine five-server MCP setup at 58 tools consuming roughly 55K tokens before the conversation starts, and saw 134K tokens of definitions internally before optimisation. Under about twenty tools, keep them all loaded; past that, switch to tool search, covered in [Context in practice](context-practice.md).

## Three: the disk

Anything large or long-lived goes in a file; only the path enters the window. Keep the key, not the content. A tool that fetches a 40,000-token page should not return the page:

```python
import hashlib, pathlib, urllib.request

def fetch_to_disk(url: str) -> str:
    text = urllib.request.urlopen(url).read().decode("utf-8", "replace")
    path = pathlib.Path("cache") / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return f"saved {len(text)} chars to {path}"
```

The agent reads slices of the file when it needs them. The window holds a 15-token receipt instead of the document.

## Four: the tail

The end of the window is the best-attended real estate you have. Restate the current goal there every few steps: one or two lines, appended after the latest tool results. In a long loop the original instruction has drifted into the weak middle; the tail restatement is what keeps the model on task for thirty tokens a turn.

## What survives the session

Google's [Sessions & Memory whitepaper](https://www.kaggle.com/whitepaper-context-engineering-sessions-and-memory) draws the line cleanly: the session is the workbench for one conversation; memory is the filing cabinet that persists across them. Its definition matters — memories are extracted information, not the raw dialogue. You do not archive transcripts; you run extraction (an LLM pulls out only facts matching defined topics — preferences, decisions, goals) and then consolidation, where new facts are compared against existing ones and merged, updated, or deleted when contradicted. Both run in the background after the reply is sent, never on the hot path. What you persist between sessions is the distilled record: stable preferences, standing decisions, hard-won facts. The transcript stays on disk as provenance.

## Compacting the window

For the live session the whitepaper names three strategies, in rising sophistication: keep the last N turns (a sliding window), token-based truncation (fill a budget newest-first), and recursive summarisation (replace older turns with a rolling summary prefixed to recent verbatim ones). Trigger compaction on a count threshold, on inactivity, or on task completion. The loop handbook's [context hygiene](../track-loop/context-hygiene.md) page goes deeper on compaction inside long-running loops.
