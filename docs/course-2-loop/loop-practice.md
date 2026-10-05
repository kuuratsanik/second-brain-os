# Loop practice: filter, loop, fall back

The production pattern is not "run the agent on everything". It is filter first, loop briefly, fall back. Atlan's engineering write-up, [Loop Engineering in Production: Putting AI Agents on Call](https://blog.atlan.com/engineering/loop-engineering-in-production-putting-ai-agents-on-call/), shows the shape at scale: a deterministic, non-LLM filter suppressed roughly 85% of about 11,000 alerts a month before a single token was spent, so only the remainder ever reached the agent; the agent then reasoned for about three cycles, and when confidence stayed below roughly 50% it escalated to a deterministic fallback workflow in plain Python. Investigations that had taken over ten minutes and a few dollars came down to about two minutes and $0.28 each. Cheap code handles the common case; the model handles the residue; a fixed path catches whatever the model cannot close. *Not re-checked on 5 October 2026: the page could not be fetched, and the figures here were confirmed only from search-result summaries of it.*


> The goal-test half of this pattern is packaged as a skill: install [the course plugin](../../plugins/README.md) and run `/agents-course:goal-test`; the checker role ships as the `loop-critic` agent.

One frame before the code: this build is the triage shape — filter, loop briefly, fall back. The other production shape, a loop wrapped around a coding agent and driven by a goal test, is the [loop handbook's build](../track-loop/build-goal-test.md); same four parts, different body.

## The build

The whole hybrid fits in one file. It runs as-is; swap `model_next_step` for a real API call and the control flow does not change.

```python
"""Hybrid alert triage: deterministic filter, bounded loop, fixed fallback."""

MAX_TURNS = 3          # Atlan runs about three reasoning cycles before escalating
BUDGET_USD = 0.10      # spend ceiling per alert
COST_PER_TURN = 0.02   # replace with real usage figures from your API responses

ALERTS = [
    {"id": 1, "source": "cron", "message": "nightly backup finished OK"},
    {"id": 2, "source": "api", "message": "TimeoutError in /sync after 30s"},
    {"id": 3, "source": "api", "message": "intermittent 502 from payments"},
]

def prefilter(alert):
    """Deterministic, costs nothing. Returns a verdict, or None for the loop."""
    message = alert["message"].lower()
    if alert["source"] == "cron" or "finished ok" in message:
        return {"cause": "known-benign pattern", "next_step": "close", "via": "filter"}
    return None

def checker(diagnosis):
    """External judge: a diagnosis must name a cause and a concrete next step."""
    return bool(diagnosis.get("cause")) and bool(diagnosis.get("next_step"))

def model_next_step(alert, history):
    """Stub standing in for the model call. Swap in a real API call here."""
    if "timeout" in alert["message"].lower():
        return {"cause": "client timeout on /sync", "next_step": "raise limit to 60s"}
    return {"cause": "", "next_step": ""}   # the stub cannot close this one

def fallback_workflow(alert):
    """Fixed path, no model: always produces a defensible answer."""
    return {"cause": "unresolved by agent", "next_step": "page on-call with raw alert",
            "via": "fallback"}

def triage(alert):
    verdict = prefilter(alert)
    if verdict is not None:
        return verdict                                   # most alerts stop here
    history, spent = [], 0.0
    for turn in range(MAX_TURNS):
        diagnosis = model_next_step(alert, history)
        history.append(diagnosis)
        spent += COST_PER_TURN
        if checker(diagnosis):
            diagnosis["via"] = "loop, turn %d" % (turn + 1)
            return diagnosis                             # exit 1: checker passed
        if len(history) >= 2 and history[-1] == history[-2]:
            break                                        # exit 2: spinning
        if spent > BUDGET_USD:
            break                                        # exit 3: over budget
    return fallback_workflow(alert)                      # every other exit lands here

if __name__ == "__main__":
    for alert in ALERTS:
        print(alert["id"], triage(alert))
```

Alert 1 never touches the model, alert 2 closes on the loop's first turn, and alert 3 spins twice and lands in the fallback. Every path returns the same shape, so the caller never knows which layer answered.

## Tips

- Grow the filter, not the loop. Every diagnosis the loop produces twice is a candidate rule for `prefilter`.
- Log `via` on every result. The ratio of filter to loop to fallback is your health metric; a rising fallback share means the loop is failing quietly.
- Keep the fallback boring. Its job is a defensible answer with no model, not a second attempt at cleverness.
- Make the checker stricter than feels polite — it is the only part the model cannot talk its way past. Hardening it against a real coding agent is [the goal test build page](../track-loop/build-goal-test.md); the full menu of brakes is [stop conditions](../track-loop/stop-conditions.md).

## Prove it to yourself

1. Run the file, then set `MAX_TURNS = 0` and run it again. Every unfiltered alert should land in the fallback — if anything crashes instead, an exit path was missing.
2. Make `model_next_step` return the same wrong answer forever. Confirm the spin check exits on turn two, not turn three.
3. Add a fourth alert your filter catches, and log how many model calls the whole batch now makes. That number falling while coverage holds is the entire economics of the pattern — and deciding which decisions deserve a model at all is the next module, [cheap decisions](../course-3-gate/cheap-decisions.md).

Go deeper → the [loop engineering handbook](../track-loop/what-loop-engineering-is.md): stop conditions, critics, context hygiene, and an overnight loop you can trust by morning.
