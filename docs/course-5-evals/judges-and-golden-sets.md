# Judges and Golden Sets

Behavioural checks are code, and code is trustworthy. End-to-end grading usually is not code: "is this reply correct and grounded" needs a grader that reads, which in practice means another LLM. A judge is a measurement instrument, and no instrument ships calibrated. This page covers checking the judge, then building the set of cases it grades.

## Judges need judging

Two properties decide whether a judge's number means anything.

First, agreement with hand labels. Label outputs pass/fail yourself, run the judge on the same outputs, and measure agreement per class — a judge that always says pass scores 90% raw accuracy on mostly-good data while catching nothing. Read every disagreement: half the time the rubric was woolly, half the time your own label was. The full procedure, plus the documented bias failure modes (position, verbosity, self-preference), is in [llm as judge](../track-evals/llm-as-judge.md).

Second, repeat-run variance. Run the same judge on the same inputs several times and see how much the verdicts move. Airbnb learned this expensively: their pipeline regenerated model-written reference answers on every eval run, and [their engineering blog](https://airbnb.tech/ai-ml/from-weeks-to-a-day-how-we-made-llm-evaluation-fast-enough-to-iterate-on/) reports that roughly three quarters of those references differed across labelling runs on identical inputs. A two-point score movement could mean the agent improved, the judge drifted, or the references had been rerolled — the eval was measuring its own noise. Their fix is worth copying: cache references and judge verdicts keyed by input and configuration, so identical inputs return identical results and regeneration only happens on purpose.

## Building the golden set

The golden set is the fixed collection of cases both tiers run against. Airbnb's [eval-driven development write-up](https://airbnb.tech/ai-ml/eval-driven-development-lessons-from-evaluating-genai-at-scale/) recommends 50–100 examples, and is blunt about composition: the set must include bad examples, not just good ones, because you cannot test discernment without them. A suite fed only happy paths certifies that the agent handles what it already handles.

Google's Agent Quality whitepaper adds the maintenance rule: every production failure, once captured and annotated, becomes a permanent test case. Failures are not embarrassments to fix and forget; they are the highest-value cases you will ever own, because each one is a real user hitting a real edge. Mining traces into cases is the practical work of the [next page](evals-practice.md). The Airbnb figures on this page (three quarters of references differing, 50–100 examples, 5% daily sampling, three to five judges) carry this note: *Not re-checked on 5 October 2026: the page could not be fetched, and the figures here were confirmed only from search-result summaries of it.*

Keep the grading machinery small while the set grows. Airbnb's related advice: three to five well-calibrated judges, each targeting one correctness dimension, beat twenty or thirty noisy ones.

## Production sampling and set decay

A golden set is a photograph of your users at the moment you took it, and users move. New phrasing arrives, new document types land in the vault, a feature launch shifts what people ask for. Six months on, a suite can pass at 95% while covering half of what production actually sees.

The countermeasure is a standing feed from live traffic. Airbnb samples 5% of de-identified production traffic daily and runs programmatic checks and judges over it — not to gate releases, but to find the failures the golden set does not yet contain. Whatever your scale, the shape transfers: sample a slice of real runs on a schedule, grade it, and promote anything that fails into the golden set. The set should grow a little every week; a golden set whose newest case is three months old is a decayed one.

Between calibrated judges, a set with failures in it, and a sampling loop that keeps the set honest, the measurement itself becomes something you can trust. The [practice page](evals-practice.md) turns all of this into an afternoon of concrete steps, starting from your own agent's twenty most recent failures.
