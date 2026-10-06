---
name: second-brain-lifecycle
description: >-
  Move the owner's self-improvement ideas through their lifecycle in a
  second-brain vault: capture an idea, turn it into a plan, track the
  experiment, review it against its stated success measure, and then adopt it
  as a system or drop it, recording each step in a `status:` field and a dated
  log line. Use this skill whenever the user shares an idea for improving how
  they work or live, asks how an experiment is going, asks you to review one,
  asks what is in flight or waiting on a decision, or when a scheduled review
  finds ideas or experiments that are due. Do NOT use for ordinary concept or
  source pages, for the periodic vault review itself (second-brain-review, which
  calls this skill), or to archive pages for other reasons (second-brain-archive).
---

# Run the idea lifecycle

Ideas for improving how the owner works and lives are a main reason the vault
exists. Left alone they pile up as notes nobody tests. This skill gives each one
a state, a next step and a date, and makes the decision at the end instead of
leaving the page open.

Read `wiki/systems/self-improvement-lifecycle.md` first. It is the owner's page
and wins over this skill wherever they differ.

## Core rule

You decide, you never delete. Every move is a status change on a page, a dated
line, a log entry and a commit by path. A page that leaves the active wiki goes
to `archive/` with `git mv`, as `second-brain-archive` describes. A failed
experiment is evidence and stays where it is.

## Stages and statuses

The stages use the status values the templates already define. There is no
separate `plan` status: a plan is an experiment page that is `planned`.

| Stage | Page | `status:` | Moves on when |
|---|---|---|---|
| Idea | `wiki/self-improvement/ideas/`, `templates/idea.md` | `new`, then `considering` | The owner sets `promoted`, or you drop it |
| Plan | `experiments/`, `templates/experiment.md` | `planned` | The owner's `start:` date arrives |
| Experiment | `experiments/` | `active` | The `end:` date passes |
| Review | `experiments/` plus a page in `reviews/`, `templates/review.md` | `reviewing` | The review page holds a decision |
| Adopted | `experiments/` plus a page in `wiki/systems/` | `adopted` | Final |
| Dropped | An idea moves to `archive/`; an experiment stays in place | `dropped` | Final |

Every status change adds a dated line at the bottom of the page under `## Log`
(add the heading to an idea page if it has none) and one line in `wiki/log.md`
with the operation `lifecycle`:

```
2026-10-06 lifecycle wiki/self-improvement/experiments/cold-shower.md -> active (start date reached)
```

Set `updated:` on every page you touch.

## Workflow

Do the steps the request names; a scheduled run does all of them in this order.

1. **Capture.** Write the idea with `templates/idea.md` in the owner's words,
   untidied, with `origin:` and the source or journal page it came from (link
   it, never write in `journal/`). Search the vault first. If a page already
   holds the idea, add to it instead of creating a second one. Fill "What
   supports it" and "What argues against it" from the vault, and say so when the
   vault holds evidence against the idea. Set `status: new`, link it to the
   self-improvement hub and the concepts it touches. Do not judge it at capture.
2. **Consider.** An idea that has a next step written moves from `new` to
   `considering`. An idea at `considering` for 30 days or more (a default; the
   owner may change it on the lifecycle page) gets a proposal in the run report:
   promote, keep, or drop, with the reason. You may drop it yourself only when
   the vault holds clear evidence against it or the owner has said no; otherwise
   queue the question in `wiki/systems/needs-owner.md`.
3. **Plan.** When the owner has set an idea to `promoted`, or asks for a plan in
   a live session, write `templates/experiment.md` into `experiments/` with
   `status: planned` and `idea:` linking back. Fill the change, the success
   measure and the `end:` date, and write what the owner expects, before any
   start date. Make the measure checkable from the vault (a count from the
   journal, a metrics line, a project `Feedback/` entry). If you cannot name one,
   write what you could not decide and queue it; do not invent a measure. Link
   the plan from the idea.
4. **Start.** You do not start experiments on your own judgment: a start changes
   how the owner lives. When `start:` is set and the date has arrived, set
   `status: active` and add the log line. If `start:` is empty, queue a request
   for it. Flag in the run report when more than three experiments are active
   (the lifecycle page lets the owner change that number).
5. **Track.** While an experiment is `active`, append to its `## Log` any
   evidence the vault gained since the last entry, each with a date and a link.
   Do not interpret it yet.
6. **Review.** When `end:` has passed, set `status: reviewing` and write the
   review with `templates/review.md`, `scope: experiment`. Compare the evidence
   with the written success measure and the written expectation, in that order,
   and quote both. Facts come from vault pages, each linked, not from
   recollection. Then decide, once, and write the decision and the reason on the
   review page:
   - **Adopt** when the measure was met on the evidence. Write a system page with
     `templates/system.md` in `wiki/systems/`, link experiment, review and
     system to one another, set the experiment to `adopted`.
   - **Adjust** when it was partly met or the plan was flawed. Extend `end:` once
     by the original length, recording the old date and the reason. A second
     adjustment is queued for the owner.
   - **Drop** when it was not met, or the evidence argues against continuing. Set
     `status: dropped`, say why, leave the page linked in place.
   - **No decision** when there is too little evidence to judge. Do not read
     silence as failure. Queue what evidence is missing and leave the status at
     `reviewing`.
7. **Drop an idea.** When an idea is dropped, record the reason on the page,
   then archive it. Take a checkpoint (the vault `CLAUDE.md` rail 1), then run
   the `second-brain-archive` steps for that one page: `mkdir -p` the folder
   under `archive/`, one `git mv`, add `archived`, `archived_reason` and
   `archived_from`, remove it from `index.md` and the hub, repoint inbound links
   to the archived path, and log it as `archive`. If the page is
   `maintained_by: human`, do not move it; set the status and queue the move.
8. **Keep the hub current.** Update the self-improvement hub with active
   experiments, ideas waiting for a decision and the next review due.
9. **Commit the run** by path, following `second-brain-commit`, with the subject
   `run-YYYY-MM-DD-lifecycle`. Never `git add -A`. Stage only the pages this run
   wrote, the system or review pages it created, `index.md`, the hub and
   `log.md`.

## Output format

```
Ideas: <n> new, <n> considering, <n> promoted, <n> dropped
Experiments: <n> planned, <n> active, <n> reviewing, <n> adopted, <n> dropped
Moved this run: <path>: <old status> -> <new status> (<reason>)
Decisions: <path>: adopt | adjust | drop | none yet - <one-line reason>
Waiting on the owner: <what, with the needs-owner entry>
Over the limit: <active experiments, if more than three>
```

## Calibration

Test dates against today's date, and write them in full (`2026-10-06`), never
"last week".

Do not flatter the owner. A review that reads the evidence kindly is worse than
none, because the next idea is built on it. If the success measure was vague,
say so in the review and set a sharper one in the next plan.

Health, mood and relationship material is `private`; set `sensitivity`
accordingly on the idea, experiment and review (see `second-brain-privacy`).
Describe what the owner reported. You are not a clinician; do not diagnose and
do not advise on treatment.

A plan may name actions in connected services, such as sending a message
weekly. Record the plan; do not carry it out. Those writes are a hard stop in
the vault `CLAUDE.md`.

If a checkpoint cannot be made, do not archive: set the status, queue the move
with the git error and carry on with non-destructive work.
