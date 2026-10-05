# plugins

Claude Code plugins that ship the course's tools. This repo is a plugin
marketplace: add it once, install what you need.

```bash
claude plugin marketplace add kuuratsanik/second-brain-os
claude plugin install agents-course@second-brain-os
```

## agents-course

Each tool does the practice page of one course module, in your own repo.

| Tool | Invoke as | Module |
|---|---|---|
| Context audit | `/agents-course:context-audit` | [1 · Context](../docs/course-1-context/context-practice.md) — measure the four places, find cache killers and window bloat |
| Goal test | `/agents-course:goal-test` | [2 · Loop](../docs/course-2-loop/loop-practice.md) — turn a task into a testable done, generate the script and the bounded loop |
| Gate check | `/agents-course:gate-check` | [3 · The gate](../docs/course-3-gate/gate-practice.md) — find the decisions that do not need the big model, propose fail-closed gates |
| Harness audit | `/agents-course:harness-audit` | [4 · Harness](../docs/course-4-harness/harness-practice.md) — walk the four rings, state the blast radius, rank the hardening list |
| Evals bootstrap | `/agents-course:evals-bootstrap` | [5 · Evals](../docs/course-5-evals/evals-practice.md) — mine real failures into cases, generate the trace checker |
| Loop critic | agent `agents-course:loop-critic` | [2 · Loop](../docs/course-2-loop/the-four-parts.md) — a checker outside the model: reviews loop results in a clean context |

The skills are plain `SKILL.md` files, so they also work copied into
`~/.claude/skills/` or with any harness that reads the Agent Skills format.
