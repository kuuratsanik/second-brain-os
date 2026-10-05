# Cheap Decisions

An agent does two kinds of work. It writes — summaries, plans, replies, code — and it decides — is this urgent, which folder does this belong in, does this need a person. Writing is open-ended and genuinely needs a large model. Deciding is bounded: the answer comes from a set you already know. Most pipelines send both kinds of work to the same frontier model, which is paying the lawyer to sort the envelopes.

This module is about the gate: a cheap decision layer that sits in front of the expensive model and sorts the stream, so the frontier model only sees the items that actually need judgement.


A note on names: the module is called the gate, after the pattern. Its deep-dive handbook is [Jev engineering](../track-jev/system-one-models.md), after the class of System One models that most often stands in the gate — the pattern and one strong way to build it.

## Two kinds of work

Watch an agent process an inbox and count the decisions. Is this spam. Is this a newsletter. Which project does it touch. Does it need a reply. Only after all of that does any writing happen — and for most items it never does; the item is filed, archived, or dropped. A frontier model answering "is this a newsletter" burns seconds and real money to produce one bit of information. The decision was worth a fraction of a cent. The writing, on the rare item that needs it, is worth the full price.

## What a gate is

A gate asks one narrow question per item and routes on the answer. The shape is always the same: everything comes in; each item gets a bounded question — one of these labels, yes or no, a score; items the gate answers confidently and routinely are handled by cheap deterministic code; anything the gate is unsure about goes through to the main model. Unsure means escalate. The gate is never the only path, only the fast one.


![Diagram of a gate in front of an expensive model. Every request reaches the gate. Confident cases are answered cheaply, in milliseconds and fractions of a cent. Unsure ones go on to the expensive model, which takes seconds and real money.](fig-gate.svg)

## The taxonomy of gates

Four tools, in rising order of cost and fallibility:

- **Rules.** Regular expressions, sender allowlists, "has an unsubscribe link". Free, instant, and blind to anything you did not anticipate. Always the first layer, never the last.
- **A classic classifier.** Logistic regression or similar over TF-IDF features, trained on a few hundred of your own labelled examples. Runs in microseconds on your own machine, costs nothing per call, and its mistakes are inspectable.
- **A small LLM.** A Haiku-class model prompted to answer with one word. No training data needed and it copes with novelty, but it is the slowest and dearest of the cheap options, and you must parse text to get your answer.
- **A System One model.** Jev, released in waitlisted early access by TypeSafe AI in September 2026 (see [getting started](../track-jev/getting-started.md)), is the first of these: typed decisions — yes/no, one of up to 255 options, or a scalar on an ordered scale — each with a confidence score, and no text generation at all. Background in [system one models](../track-jev/system-one-models.md).

## Where gates belong

Anywhere the stream fans in. At ingestion, before anything reaches the main agent: spam, duplicates, and pure reference material should never cost a frontier token. Before expensive tool calls: "does this query need the web" is a gate. And around actions, as guardrails: "is this destructive" as a yes/no, blocked above a threshold. Layer them — rules first, classifier second, model only for what survives the first two.

The gate is an architecture decision, not a vendor decision. The architecture — narrow question, cheap answer, escalate on doubt — stays the same whichever tool fills the slot. Which tool that should be is an empirical question you answer with your own labels, and it is the subject of the next page: [gates in practice](gates-in-practice.md).
