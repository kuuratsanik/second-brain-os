# Two Kinds of Checks

The previous modules built an agent that plans, calls tools, and edits your vault. This one is about knowing whether it works — before your users tell you. Everything in agent evaluation rests on one distinction: checks on the outcome versus checks on the behaviour. You need both, and they answer different questions.


![Diagram of one agent run with four steps: get_order, ask_approval, refund and reply. Behavioural checks read the steps: it looked up first and asked before acting. The end-to-end check reads only the result: the right outcome.](fig-two-checks.svg)

## End-to-end checks

An end-to-end check asks a single question: did the final answer come out right? Run the input, take the last message or the resulting state, score it — exact match, a rubric, a judge. This is the check users would design, because it measures the thing they experience.

Its strength is also its limit. When the pass rate drops from 84% to 71% after a prompt edit, an end-to-end suite tells you the score moved. It does not tell you why. The failing transcripts still have to be read one at a time, because the failure could be in retrieval, in tool arguments, in a skipped verification step, or in the final phrasing. Google's [Agent Quality whitepaper](https://www.kaggle.com/whitepaper-agent-quality) treats this as black-box evaluation — "did the agent achieve the user's goal?" — and pairs it with a glass-box view of the path taken, on the principle it summarises as "the trajectory is the truth".

## Behavioural checks

A behavioural check asks whether one specific thing happened on the way to the answer. Did the agent call search before answering? Did it ask a clarifying question when the request was ambiguous? Did it verify the file exists before claiming the task was done? Each check is narrow, binary, and cheap — an assertion, not a judgement.

The payoff is diagnosis. Two agents that produce the same refund email are not the same agent if one looked up the order first and the other guessed. An end-to-end check scores them equal; a behavioural check separates them today, before the guesser meets an order it guesses wrong.

## The trace is the substrate

Behavioural checks run on the trace: the full record of model turns, tool calls with their arguments, tool results, and retries. No trace, no behavioural checks — which is why the whitepaper argues agents should be instrumented for evaluation from the first line of code, with logs, traces, and metrics as the three pillars of observability. If your agent is a Claude Code setup, the transcript already is the trace: Claude Code [writes every session](https://code.claude.com/docs/en/agent-sdk/sessions), tool calls and results included, to a JSONL file under `~/.claude/projects/`, so keep it. What to assert over it — tool choice, argument extraction, ordering constraints, error handling — is covered in depth in [agent evals](../track-evals/agent-evals.md).

## The speed budget

Split the suite into two tiers. The fast tier is deterministic behavioural assertions only: no model calls, no network, just code reading traces. Keep it fast enough that nobody decides whether to run it — a few seconds, call it five, is a workable budget. Beyond that, it becomes a thing you run before merging instead of after every edit, and the feedback loop dies. The slow tier — end-to-end runs with judges — goes nightly and before releases. The single-file structure in [build the suite](../track-evals/build-suite.md) extends naturally into this split.

## Where each kind earns its keep

End-to-end checks earn their keep at decision points: shipping a release, swapping a model, comparing two prompts. Behavioural checks earn theirs during development, where you change one thing and want to know within seconds what it disturbed.

One trap to avoid from day one: watch individual checks, not the overall pass rate. An aggregate can rise while one behaviour quietly breaks — five flaky cases start passing, and the agent stops asking approval before refunds. The aggregate says progress; check-level history says incident. Grading the slow tier is its own problem, which is where [judges and golden sets](judges-and-golden-sets.md) come in.
