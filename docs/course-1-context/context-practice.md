# Context in practice

You know the mechanics and [the four places](the-four-places.md). This page is the working session: audit an existing agent, restructure it, and add the two upgrades that matter past a certain size.


> The whole audit below is also packaged as a skill: install [the course plugin](../../plugins/README.md) and run `/agents-course:context-audit` in your project.

## Audit the window

Do this against a real agent, not from memory.

1. Capture one full request payload — log the exact JSON your framework sends to the model on a mid-conversation turn.
2. Token-count each section separately: system prompt, tool definitions, message history, retrieved content, current query. Write the five numbers down.
3. Circle every dynamic value inside the system prompt — timestamps, user names, injected memories. Each one is a guaranteed cache miss on every call.
4. Check whether the tool list is identical on turn 1 and turn 20. If it changed mid-run, you paid a full cache invalidation each time.
5. Find the largest single item in the history. It is almost always a verbatim tool result that should have been a file path.
6. Locate the current goal. If it appears only in the opening message, it now lives in the weak middle of the window.
7. Read `cache_read_input_tokens` from the [usage object of the API response](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). Zero on a warm conversation means something in your prefix is moving.

## Restructure to the four places

Work through the audit findings in order. Strip the system prompt to what is true on every call and move every circled dynamic value into the message history. Freeze the tool list at conversation start and replace any mid-run removal with a blocked call that returns a refusal string. Rewrite fat tools to write their output to disk and return the path plus a one-line receipt. Then add the tail: after every few tool results, append one line restating the current goal. Re-run the audit; the five numbers should shift visibly towards a small stable prefix and a short live tail.

## Switch to tool search past twenty

Anthropic's [Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use) post (November 2025) reports that keeping all definitions loaded stops scaling: with the tool search tool enabled instead, Opus 4 went from 49% to 74% on their MCP evaluation, and Opus 4.5 from 79.5% to 88.1%. Their own threshold is ten-plus tools or over 10K tokens of definitions; this course draws the hard line at twenty. Keep a small always-used core loaded (the API docs suggest the three to five most used tools), mark the rest with `defer_loading: true`, and let the model search for definitions on demand; see the [tool search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) docs. The API docs add that tool selection degrades past 30 to 50 available tools. The prefix shrinks and, per those numbers, selection accuracy rises with it.

## Add a summarising subagent

A subagent is a context firewall. When a task requires reading fifty files, do not read them in the main window — spawn a subagent whose own window absorbs the fifty files and hands back a one-page summary. The main agent keeps the conclusion, not the evidence. The same pattern fits any bulk read: log trawls, large diffs, document piles. The [harness handbook](../track-harness/context-engineering.md) covers wiring firewalls into a real setup.

## Tips

- Restate the goal in the tail every three to five steps.
- No verbatim tool result over about 2,000 tokens survives in the history; path plus receipt instead.
- Block tools, never remove them.
- Treat system prompt changes as releases; diff them.
- Watch cache metrics in production — a silent cache miss bills the prefix at ten times the cache-read rate or more.

## Prove it to yourself

1. Plant one invented fact in the middle of a 30K-token transcript and ask about it; then move the same fact into the final message and ask again. Compare the answers.
2. Send an identical request twice and read `cache_read_input_tokens`; then add a timestamp to the top of the system prompt and watch it drop to zero.
3. Run the same fifty-file summarisation once in your main window and once through a subagent; compare final context size and answer quality.

Next module: [loops versus workflows](../course-2-loop/loops-vs-workflows.md).

Go deeper → the [harness handbook's context engineering page](../track-harness/context-engineering.md): the same discipline wired into a real setup.
