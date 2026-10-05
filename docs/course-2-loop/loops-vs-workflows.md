# Loops versus workflows

A workflow is a sequence you wrote in advance: step one, step two, step three, done. A loop is different in exactly one place — the next step is chosen at run time, by the model, based on what just happened. The cycle is think, act, observe, decide, on repeat: the model proposes an action, the action runs, the result lands back in the history, and something decides whether to go round again. Google's "Introduction to Agents" whitepaper (Kaggle, 2025) draws the same cycle as get the mission, scan the scene, think it through, take action, then observe and iterate, running on a triad of model, tools and orchestration. The vocabulary varies; the shape does not.

## Who chooses the next step

That is the entire distinction. In a workflow, you chose every step at design time; the code merely replays your decisions, and the same input takes the same path every run. In a loop, the model chooses at run time, so two runs of the same input can take different paths — which is the point, and also the problem. The Google whitepaper frames it as the developer moving from bricklayer to director: you stop laying each step and instead set the goal, pick the tools, and let the system route itself. Directing costs more than bricklaying, and it is harder to audit.


![Two diagrams. In a workflow you chose every step, from step 1 to step 2. In a loop the model chooses: think, act, observe, decide.](fig-workflow-vs-loop.svg)

## When each wins

A workflow wins whenever you can enumerate the steps. Known input shapes, known failure modes, a path you could draw on a whiteboard — write it as ordinary code. It runs in milliseconds, costs nothing per branch, never hallucinates a step, and fails loudly in a debugger. Most of what gets built as an "agent" today should be a workflow with one or two model calls inside it.

A loop wins only when the path genuinely cannot be written down: debugging an unfamiliar failure, investigating an alert whose cause could be one of a hundred things, editing code until an external test passes. The unknown is the branching, not the work. If you find yourself writing "the agent will first check X, then Y, then Z", you have just written the workflow — ship that instead.

## The cost math

Autonomy is priced in tokens. Anthropic's engineering write-up of its multi-agent research system (June 2025) measured the ratios directly: agentic loops use roughly four times the tokens of a single chat interaction, and multi-agent systems roughly fifteen times. So a loop must clear a value bar about 4x a plain call, and a crew of agents about 15x, before it earns its keep. The bill compounds with unpredictability: Google's "Prototype to Production" whitepaper notes that because agent trajectories are assembled dynamically, cost and latency are unpredictable per run — and that roughly 80% of production effort goes on infrastructure, security and validation rather than the agent's intelligence. You are not just paying more per run; you are paying for the machinery to keep runs bounded.

## A decision rule

Ask one question: can I write the steps in advance?

- Yes, completely — workflow. No model in the control flow.
- Yes, except one judgement — workflow with a single model call at that point.
- No, the path depends on what each step reveals — a loop, bounded by the four parts in [the four parts](the-four-parts.md): a testable goal, an external checker, a stop rule and a budget.

Default to the cheapest structure that survives contact with the task, and promote only on evidence. The discipline of designing that bounded cycle — rather than prompting it by hand — is [loop engineering](../track-loop/what-loop-engineering-is.md), and the production pattern that ties both structures together (filter first, loop briefly, fall back) is built end to end in [loop practice](loop-practice.md).
