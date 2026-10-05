# The four parts of a loop

Every loop that survives production has the same four parts: a goal with a testable definition of done, a checker that lives outside the model, a stop rule, and a budget counted in both turns and dollars. Remove any one and you have not simplified the loop; you have removed its brakes. This page takes each part in depth, then annotates the canonical skeleton.


![Diagram of a loop with a goal and a definition of done. The agent acts and a checker tests the result: pass ends the loop, fail retries unless it is stuck or over budget, in which case it falls back to a workflow. The checker lives outside the model.](fig-four-parts.svg)

## A goal with a testable done

"Improve the error handling" cannot terminate a loop, because nothing can ever say it is finished. "All tests under `tests/` pass and the linter reports nothing" can. The goal must be phrased so that a program — not a person, not the model — returns true or false against it. If you cannot write done as a check, you do not have a loopable task yet; you have an interactive session. Writing done as a forty-line script is a skill in itself, built concretely in [the goal test build page](../track-loop/build-goal-test.md).

## A checker outside the model

The checker is a test suite, a compiler, a linter, a schema validator — anything mechanical that judges the result without asking the model's opinion. Self-review is not a checker. The evidence here is direct: Huang et al., ["Large Language Models Cannot Self-Correct Reasoning Yet"](https://arxiv.org/abs/2310.01798) (ICLR 2024), found that models struggle to correct their own reasoning without external feedback, and that performance sometimes gets worse after self-correction. A model grading its own work is the same weights making the same mistake twice, now with more confidence. External checkers are therefore non-negotiable: the feedback that makes a loop converge has to come from outside the thing that produced the error. This is why coding is the best-behaved loop domain — the compiler and the test runner are free, fast, external checkers that come with the territory.

## A stop rule

Three exits, any of which ends the run: the checker passes (success), the turn limit is hit (out of attempts), or two consecutive attempts are identical (the loop is spinning and more turns will only spend money). That last one matters because spin is quiet — the same failing test, the same empty diff, attempt after attempt. The full menu of brakes, including ratchets and fingerprinting, is in [stop conditions](../track-loop/stop-conditions.md).

## A budget in turns and dollars

Turns and dollars fail differently, so cap both. A turn cap bounds attempts; a dollar cap bounds damage when a single turn balloons — one tool call that returns a huge payload can cost more than ten normal turns. A loop with a turn cap but no spend cap is a bill with an unknown ceiling.

## The skeleton, annotated

```python
for turn in range(MAX_TURNS):                      # budget, part one: turns
    action = model.next_step(goal, history)        # the model chooses the step
    result = run(action)                           # the world responds
    history.append(result)                         # the observation survives
    if checker(result):                            # external judge, never the model
        break                                      # stop rule 1: done
    if repeated(history, 2):                       # stop rule 2: spinning
        break
    if spent() > BUDGET:                           # budget, part two: dollars
        break
else:
    fallback_workflow(goal)                        # turns exhausted: fixed path
```

Read the exits carefully. The `else` on a Python `for` runs only when the loop finishes without a `break`, so as written it catches exactly one failure mode: turns exhausted. The `repeated` and budget breaks leave without a result, so in production you route every exit that is not a checker pass to the same place — the fallback workflow, a deterministic path that produces a defensible answer without the model. The practice page wires that version up completely in [loop practice](loop-practice.md).

Notice also what the skeleton omits: there is no "ask the model if it is satisfied". The model chooses the next step; it never gets a vote on whether the work is done.
