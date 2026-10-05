# What an agent is

Google's [Introduction to Agents](https://www.kaggle.com/whitepaper-introduction-to-agents) whitepaper (Kaggle, November 2025) defines an agent as an application that makes plans and takes actions to achieve a goal — not a model that answers a question. The definition sounds bland. The consequence is not: the model is one component of four, and usually not the one that fails.

## Model, tools, orchestration

The whitepaper names four components. The model is the brain: the reasoning engine that decides what to do next. Tools are the hands: APIs, code execution, database queries — anything that lets reasoning touch the world. The orchestration layer is the nervous system: the loop that assembles context, calls the model, executes what it asked for, and feeds the result back in. Deployment is the body: hosting, logging, monitoring, the unglamorous rest.

The loop is the part people underestimate. The paper describes a think–act–observe cycle: the agent receives a mission, surveys what it has, plans a step, takes it, looks at what happened, and goes round again until the goal is met. Strip away the branding and an agent is a loop that keeps rebuilding the model's context between steps.


![Diagram of the agent loop: a request goes to the model, which calls tools and gets results back, repeating until the goal is met, then returns an answer.](fig-agent-loop.svg)

## Five levels of agency

Rather than a binary, the paper grades systems:

- Level 0 — the bare model, reasoning from training data alone. No tools, no memory.
- Level 1 — the connected problem-solver: model plus tools, so it can fetch what it does not know.
- Level 2 — the strategic problem-solver: multi-step plans and deliberate context engineering.
- Level 3 — the collaborative multi-agent system: specialist agents that treat each other as tools.
- Level 4 — the self-evolving system: builds new tools or agents when it finds a capability gap.

Most of what ships in production today sits at levels 1 and 2. That is not a criticism; it is where the return is.

## Not a chatbot, not a workflow

A chatbot answers one message at a time and the human decides every next step. A workflow — in Anthropic's definition — is a system where model calls and tools run along code paths you wrote in advance. An agent is a system where the model directs its own process: it decides the next step from what it just observed. The dividing question is always the same: who decides what happens next — the human, your code, or the model?

## Where agents pay off

The whitepaper's own examples span the range. At the small end, a customer-support agent resolving "where is my order?" by calling the order-lookup and tracking APIs itself, instead of a scripted decision tree. At the large end, Google's Co-Scientist, where a supervisor delegates to specialist agents — generation, reflection, ranking, evolution, meta-review — that refine scientific hypotheses over hours or days; and AlphaEvolve, which proposes and tests candidate algorithms and has produced improvements in data-centre efficiency and matrix multiplication.

The common shape: the steps could not have been written down in advance, but the result can be checked. Where the steps can be written down, write them — that argument is [agents or workflows](agents-or-workflows.md). And the four components are only the anatomy of one worker; the system around it is [the five layers](five-layers.md).

## Check yourself

- Name the four components the whitepaper gives an agent. Which one contains the think–act–observe loop?
- Your system calls a model three times in a fixed order with no branching. Which level is it, and is it an agent?
