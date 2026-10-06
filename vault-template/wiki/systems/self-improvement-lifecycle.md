---
title: Self-improvement lifecycle
type: system
status: active
domain: [systems, self-improvement]
lang: en
sensitivity: normal
maintained_by: human
created:
updated:
aliases: [Ideas to experiments to reviews]
tags: [vault]
---

# Self-improvement lifecycle

The owner's ideas for improving how they work and live are a main reason this
vault exists. They move through four stages. The agent reads this page when it
captures an idea, writes a review or updates the hub. The owner edits it.

1. **Idea** (`wiki/self-improvement/ideas/`, `templates/idea.md`). Captured the
   moment it appears, in the owner's words, with where it came from. Capture
   without judging. `status: new | considering | promoted | dropped`.
2. **Experiment** (`experiments/`, `templates/experiment.md`). An idea the owner
   decided to try, written as a plan: what changes, for how long, how success is
   measured, what the owner expects. Fill the measure and end date before the
   start date. `status: planned | active | reviewing | adopted | dropped`.
3. **Review** (`reviews/`, `templates/review.md`). What happened, with evidence
   from the vault (journal, meetings, project `Feedback/`, metrics), not
   recollection. It ends with a decision: adopt, adjust or drop. Periodic
   reviews use the same template with `scope:` set to the period.
4. **System** (`wiki/systems/`, `templates/system.md`). An adopted experiment
   becomes a routine. The system page links to the experiment and review.

Rules for the agent:

- Link every idea to the concepts and sources that support or contradict it. If
  the vault holds evidence against an idea, say so. Do not flatter the owner.
- Do not start experiments. You may propose one when an idea has sat at
  `considering` for 30 days or more (change the number here if you like); the
  owner promotes it.
- Keep [[hub-self-improvement|the hub]] current: active experiments, ideas
  waiting, next review due. Flag it in the run report when more than three
  experiments are active. The owner may change that number here.
- Never delete a dropped idea or a failed experiment. A failed experiment is
  evidence: set `status: dropped`, say why, leave it in place and linked. A
  dropped idea is set to `dropped` with the reason, its links from live pages
  become plain text, and it is moved to `archive/` with `git mv` (never `rm`),
  so it stays searchable and restorable. Where the vault does not allow the
  agent to archive on its own, the move is queued for you.
- The skill `second-brain-lifecycle` carries out these steps: it moves a page
  between statuses, adds a dated line under `## Log` and a `lifecycle` line in
  `wiki/log.md`, and decides at review. It does not start an experiment on its
  own: it sets `active` only when you have put a `start:` date on the plan.
- Health, mood and relationship material is `private`. Describe it as the owner
  reported it. You are not a clinician; do not diagnose.
- The weekly review: you write the page from `templates/review.md`. The
  read-only `reviewer` agent may draft it for you; it cannot write the page.

Part of [[hub-systems|Systems]].
