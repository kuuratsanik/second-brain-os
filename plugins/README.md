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

## Running the evals

The plugin ships an eval suite in `agents-course/evals/`, in the format of
Claude Code's built-in plugin evals ([format and options](https://code.claude.com/docs/en/plugin-evals);
needs Claude Code v2.1.269 or later and the same login your sessions use, so
runs count against your plan or API bill). From this repo:

```bash
cd plugins/agents-course
claude plugin eval . --allow-tools Write Edit --threshold 0.8
```

Pass `--allow-tools Write Edit`. Without it those tools are removed from every
run, the `evals-bootstrap` and `goal-test` cases cannot create their files, and
the read-only guard on the audit skills passes trivially. The suite never
grants `Bash`, so no sandbox backend is needed.

Each case runs three times with the plugin and three times without it. One run
of the whole suite with `--runs 1`, both arms, 12 cases, cost $1.72 at list
prices when this suite was written. The default three runs per case should
cost about three times that, roughly $5, plus run-to-run variation. For a
cheap check while editing a skill, run one arm once:

```bash
claude plugin eval . --case 'context-audit-*' --runs 1 --ablation none
```

The twelve cases:

| Case | Checks |
|---|---|
| `context-audit-fires` | The skill fires on a cache and context-layout question; it never calls `Edit` or `Write`; the reply names the dynamic values and the tool count |
| `harness-audit-fires` | The skill fires on an unattended-run safety question; it never edits; the reply states the blast radius and the containment ring |
| `gate-check-fires` | The skill fires on a model-cost question; a judge model checks that only the bounded decisions get a cheaper gate |
| `goal-test-fires` | The skill fires on a vague loop goal and writes `goal-test.*` |
| `evals-bootstrap-fires` | The skill fires on a request for evals; `cases.yaml` and `check_traces.py` exist, the cases use the `trace has` rule language, and the runner calls no model |
| `loop-critic-dispatched` | Claude dispatches the `loop-critic` agent when asked for an independent review, and its output has the `VERDICT` / `defects` shape |
| `*-ignores-unrelated` (four skills) | An unrelated question does not fire the skill |
| `gate-check-ignores-evals-request` | A request for a regression suite does not fire `gate-check` |
| `loop-critic-not-dispatched-for-unrelated` | An unrelated question does not dispatch the critic |

The cases paste their inputs into the prompt instead of using fixture projects,
because fixtures need `--scaffold`, which runs a script as you. Each run starts
in an empty workspace, so the audit skills read the pasted text.

The `no-edit` and `no-write` graders test the plugin's wiring, not the model:
they mean something only while `Edit` and `Write` are granted, and the prompts do not ask
for a change, so they catch a skill that loses its `disallowed-tools` line.

A `Δ` of `0.00` on a case means the plugin did not change the score on that
case. In a first run on 2026-10-05 the content checks of `context-audit-fires`
and `gate-check-fires` also passed without the plugin (those cases have since
gained checks on each skill's own output format, not yet run); the trigger graders
(`tool_used: Skill`) are excluded from the score in a two-arm run, so only the
content checks count there. Read those two as regression guards, not as proof
of lift. Results go to `evals/results/`, which is git-ignored.
