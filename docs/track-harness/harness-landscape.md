# Harness Landscape

A survey of what is alive in September 2026, with one honest take each. They all run the same loop described in [what a harness is](what-a-harness-is.md); they differ in how much machinery they wrap around it and whose opinions you inherit.

## The main options

- **[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)** (Anthropic, Python/TS). The Claude Code loop as a library: permissions, hooks, subagents, skills, compaction included. The most complete harness you can adopt wholesale — at the price of Anthropic's opinions and Anthropic's models doing their best work in it. Detailed in [Claude Code as harness](claude-code-as-harness.md).

- **[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)** (Python, TS lagging). Lightweight: agents, handoffs, guardrails, sessions. The April 2026 update added native sandboxing and a "model-native harness" tuned for GPT-5-class models. Part of the broader [AgentKit](https://openai.com/index/introducing-agentkit/) bundle — note the drag-and-drop Agent Builder is being retired November 2026, so bet on the SDK, not the canvas.

- **[LangGraph](https://www.langchain.com/langgraph)** (LangChain, Python/JS). Agents as explicit state graphs, 1.0 since October 2025 (PyPI [langgraph 1.0.0](https://pypi.org/project/langgraph/) was released on 17 October 2025), durable execution and human-in-the-loop interrupts. Genuinely production-proven, and genuinely heavy. Choose it when you need auditable control flow, not because it is the famous one.

- **[Vercel AI SDK 6](https://ai-sdk.dev)** (TypeScript). Went from streaming toolkit to real harness: `ToolLoopAgent`, tool approval, full MCP support. The sensible default when your agent lives inside a web product. Release notes: [AI SDK 6](https://vercel.com/blog/ai-sdk-6). The `ai` package on [npm](https://www.npmjs.com/package/ai) has a 6.0.0 release dated 22 December 2025, and `ToolLoopAgent` appears in the [package changelog](https://github.com/vercel/ai/blob/main/packages/ai/CHANGELOG.md).

- **[smolagents](https://github.com/huggingface/smolagents)** (Hugging Face, Python). the [README](https://github.com/huggingface/smolagents) says the agent logic fits in ~1,000 lines; agents write Python code as their actions instead of JSON tool calls. The fastest route to a working loop and the best codebase for learning. Thin on production concerns by design.

- **[OpenHands](https://github.com/OpenHands/OpenHands)** (formerly OpenDevin; the org moved from All-Hands-AI to OpenHands). Its [README](https://github.com/OpenHands/OpenHands) now leads with Agent Canvas, "the self-hosted developer control center for coding agents and automations", which runs the open-source OpenHands agent by default and can drive other agents such as Claude Code and Codex, locally, in Docker, on VMs or on OpenHands Cloud. Earlier versions of this page described OpenHands as a sandboxed autonomous software-engineering agent; check the README for the current scope before choosing it. Heavier to self-host than a CLI.

- **[pi](https://github.com/earendil-works/pi)** (Mario Zechner, ex badlogic/pi-mono, now under Earendil; docs at [pi.dev](https://pi.dev)). A deliberately minimal terminal harness; its [README](https://github.com/earendil-works/pi) describes it as "a minimal, extensible agent harness" that skips sub-agents and plan mode, with extensions, skills and a TypeScript SDK. Databricks benchmarking reportedly found it beat heavier harnesses on pass rate while sending less context per turn (no primary source cited; exact ratio omitted) — minimalism as [context engineering](context-engineering.md), and proof the harness moves the numbers.

- **[Pydantic AI](https://ai.pydantic.dev)** (Python). Type-safe agents from the validation people. Boring in the best way; strong choice when structured outputs are the whole job.

## How to choose

Building on Claude: Agent SDK. TypeScript web product: Vercel AI SDK. Explicit workflow control: LangGraph. Learning: smolagents, then read pi's source. Self-hosted control over coding agents: OpenHands. Most teams need one harness and the discipline to feed it well — not a framework tour.
