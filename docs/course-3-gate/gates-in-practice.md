# Gates in Practice

A gate is only as good as two numbers: how often it is right, and how well it knows when it might be wrong. This page covers both, then the honest current state of the newest tool for the job.

## Thresholds and failing closed

Every gate answer carries a confidence score. The routing rule: take the cheap path only when the predicted label has a deterministic handler *and* the confidence clears a threshold. Everything else falls through to the main model. This is failing closed — the gate is allowed to be ignorant, it is not allowed to guess. An unfamiliar item should always land in front of the model with judgement, never in a handler chosen at 51% confidence.

The threshold itself is a business decision, not a modelling one. Price it by the cost of a wrong fast-path action against the cost of an unnecessary escalation. A misfiled newsletter is cheap, so its route can run at a low threshold; an auto-archived job offer is expensive, so that route runs high or not at all. Working code for the whole pattern is in [the confidence-gated router](../track-jev/build-router.md).

## Calibration on your own labels

A confidence of 0.9 does not mean nine-in-ten right unless someone made it mean that. Treat every confidence score, from any vendor, as a ranking until you have checked. The check is short: hold out labelled examples the gate has never seen, group its predictions into confidence bands, and measure accuracy per band. Put the threshold where band accuracy meets your tolerance.

One independent spam benchmark ([pniessen's jev-test](https://github.com/pniessen/jev-test), on the public SMS Spam Collection and Enron-Spam corpora) shows what a healthy gate looks like: predictions in the bottom and top confidence bands were 100% accurate and carried 83% of the traffic, while nearly all errors sat in a thin middle band. Escalating that middle left zero errors on 82.7% of messages. That is the gate pattern working exactly as designed — most of the stream handled cheaply, all of the doubt sent upward.

## Jev, honestly

The vendor claims 70–500ms end-to-end against seconds for LLM workflows, and $0.042 per million input tokens with output free. Independent testing has confirmed the price but not the floor: [priorbench's evaluation](https://github.com/priorbench/jev) measured a unit price of $0.042 per million tokens, and a fastest call of 347ms via a gateway from Europe against TypeSafe's advertised 70ms floor, which it attributes to the gateway rather than the model. In the weeks after launch, the first independent accuracy numbers appeared:

- **Spam detection.** In [bitnovus's jev-spam-eval](https://github.com/bitnovus/jev-spam-eval), on 18,514 unique emails in five-fold cross-validation, a TF-IDF logistic regression scored 98.39% to Jev's 98.33% once Jev was given detailed spam criteria — a tie with a decades-old method that trains in seconds on a laptop. Two limits apply: this is binary spam detection, not general email sorting, and the criteria were refined after error analysis. On the same repository's three-way test (legitimate, spam, phishing; 5,733 emails), the baseline led by 0.23 points, 98.87% to 98.64%.
- **Phishing detection.** On [anisselbd's jev-phishing-bench](https://github.com/anisselbd/jev-phishing-bench) (2,000 emails), Jev asked one compound question — is this phishing — scored 62.6% against Claude Haiku 4.5's 81.3%. Decomposed into five narrow signal questions combined by a logistic regression fitted on 1,000 labels, Jev reached 95.0% to Haiku's 93.2%, a gap that was not statistically significant (McNemar p = 0.063); the repository adds that neither beat a two-line regex rule at 91.8%. Accuracy is engineered through question design, not delivered by default.
- **"Zero hallucinations"** means schema conformance only, by TypeSafe's own footnote, as quoted in the [jev-usecases](https://github.com/vamsikrishna2421/jev-usecases) catalog (TypeSafe's own pages were not reachable when this was checked). Every answer is a valid option; choosing the wrong valid option is precisely what the accuracy figures above measure.
- **The confidence score is a ranking, not a calibrated probability**, out of the box. The priorbench report calls it "a ranking, not a probability": accuracy was flat from 0.50 to 0.95 confidence (97.92% to 97.26%) and reached 100% only at 0.99, covering 60.2% of traffic. Its overall calibration error was low (ECE 0.051), which is why you check bands rather than trust one summary number. Set thresholds on your own labelled data.

## When logistic regression simply wins

If your gate question is fixed, your domain is your own, and you can label a few hundred examples, logistic regression is free per call, runs locally, keeps your data private, is deterministic, and — on the evidence so far — loses to nothing above. Jev's genuine case is the cold start: no labels yet, many questions per item in one pass, wide option sets, or a distribution that drifts faster than you can retrain. But that case must be proven on your data, not the vendor's. Nothing enters the pipeline until it beats the thirty-minute baseline, which you build next: [gate practice](gate-practice.md).

The naming, settled: the gate is the layer; Jev is one way to build it. The [Jev engineering handbook](../track-jev/system-one-models.md) is the deep dive on that way — this module stays about the layer.
