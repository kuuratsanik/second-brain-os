# Evals Practice

This page is the minimal build: one afternoon, five steps, one file of cases and one runner, no infrastructure. The [eval engineering handbook](../track-evals/why-evals.md) assembles the full pipeline in three builds; everything you make here carries straight into it.


> The whole build below is also packaged as a skill: install [the course plugin](../../plugins/README.md) and run `/agents-course:evals-bootstrap` on your agent's repo.

## Step 1: mine twenty failures into cases

Pull your agent's recent runs and read until you have twenty real failures — not imagined ones. For each, write one line: what the input was, and the one specific behaviour that should have happened and did not. "Replied without searching the vault." "Refunded without asking approval." "Claimed the note was created; it was not." Twenty failures usually cluster into four to eight behaviours.

## Step 2: write one behavioural check per case

Each case becomes a YAML entry: the input, the expected behaviour in words, and machine-checkable assertions over the trace.

```yaml
- id: refund_1042
  input: "Refund order #1042, customer says it arrived broken"
  expect: looks up the order before replying; asks approval before refund
  check:
    - trace has get_order before send_reply
    - trace has approval_request before refund
```

Save all twenty as `cases.yaml`. The `expect` line is for humans; the `check` lines are the test.

## Step 3: run the checks on traces

Store each run's trace as `traces/<id>.json` — a list of events, tool calls included. This is this course's own simplified shape; a Claude Code session transcript (JSONL under `~/.claude/projects/`) needs a small conversion script to produce it:

```json
[
  {"type": "tool_call", "name": "get_order", "args": {"order_id": "1042"}},
  {"type": "tool_result", "name": "get_order", "ok": true},
  {"type": "tool_call", "name": "approval_request", "args": {"action": "refund"}},
  {"type": "tool_call", "name": "refund", "args": {"order_id": "1042"}},
  {"type": "tool_call", "name": "send_reply", "args": {"channel": "email"}}
]
```

Save this runner as `check_traces.py` (needs `pip install pyyaml`):

```python
import json
import re
import sys
from pathlib import Path

import yaml


def tool_calls(trace: list) -> list:
    return [e["name"] for e in trace if e.get("type") == "tool_call"]


def check_rule(rule: str, calls: list) -> tuple[bool, str]:
    m = re.fullmatch(r"trace has (\w+) before (\w+)", rule.strip())
    if m:
        first, second = m.group(1), m.group(2)
        if first not in calls:
            return False, f"{first} never called"
        if second not in calls:
            return False, f"{second} never called"
        if calls.index(first) < calls.index(second):
            return True, "ok"
        return False, f"{second} came before {first}"
    m = re.fullmatch(r"trace has (\w+)", rule.strip())
    if m:
        name = m.group(1)
        return name in calls, "ok" if name in calls else f"{name} never called"
    m = re.fullmatch(r"trace lacks (\w+)", rule.strip())
    if m:
        name = m.group(1)
        return name not in calls, "ok" if name not in calls else f"{name} was called"
    return False, f"unparseable rule: {rule!r}"


def main() -> None:
    cases = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trace_dir = Path(sys.argv[2])
    failures = 0
    for case in cases:
        trace_file = trace_dir / f"{case['id']}.json"
        trace = json.loads(trace_file.read_text(encoding="utf-8"))
        calls = tool_calls(trace)
        for rule in case["check"]:
            passed, reason = check_rule(rule, calls)
            print(f"{'PASS' if passed else 'FAIL'}  {case['id']}  {rule}  ({reason})")
            failures += not passed
    print(f"\n{failures} failing check(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
```

Run `python check_traces.py cases.yaml traces/`. No model calls, so it finishes in well under the five-second budget and exits non-zero for CI. Report per check, exactly as printed — never collapse this into one pass rate.

## Step 4: calibrate one narrow judge

For the behaviours code cannot see ("the reply is grounded in the retrieved note"), write one judge with one question and a binary verdict. Before trusting it, hand-label ten outputs yourself and measure agreement — the ten-label script in [build the suite](../track-evals/build-suite.md) does this in thirty lines, and [llm as judge](../track-evals/llm-as-judge.md) covers the biases to watch. Below eight in ten agreement, fix the rubric, not the threshold.

## Step 5: schedule weekly hand-grading

Every week, pull five random real runs and grade them by hand against your own expectations. Disagreements with the suite become new cases; failures the suite never saw become new checks. Fifteen minutes weekly is what stops the set decaying.

## Tips

- Prefer `trace has` assertions over judges everywhere both could work.
- Keep case ids greppable and stable; you will search for them in six months.
- When a check flakes, the behaviour is genuinely nondeterministic — that is a finding, not a test bug.
- Add a happy-path case per behaviour so you notice over-correction.

## Prove it to yourself

1. Delete the `get_order` event from a trace and confirm the runner fails with the right reason.
2. Run your judge three times on one output; if verdicts disagree, tighten the rubric until they stop.
3. Break the refund behaviour deliberately, and confirm the aggregate barely moves while the individual check goes red.

Next module: [from prototype to production](../course-6-production/from-prototype.md).

Go deeper → the handbook's three builds, starting from the `cases.yaml` you just wrote: [read your traces](../track-evals/build-traces.md) from the taxonomy pass onwards (collection is done), [build the suite](../track-evals/build-suite.md) for the calibrated judge, and [the CI gate](../track-evals/build-ci.md). Nothing here is thrown away.
