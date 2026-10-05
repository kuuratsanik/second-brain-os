---
name: second-brain-schedule
description: >-
  Propose scheduled maintenance for a second-brain vault: which jobs to run, how
  often, on which kind of scheduled task, and the exact prompt for each. Use this
  skill whenever the user asks to automate the vault, schedule ingest, review or
  lint, wants the vault to maintain itself overnight, or asks what cadence to
  use. Do NOT use to run a job now, to change CLAUDE.md or the rails a run
  follows, or to create a task without the owner choosing where it runs.
---

# Propose a schedule

A scheduled run is an unattended write to the owner's notes, and nobody is
there to say stop. The prompt and the rails have to carry everything.

## Core rule

Propose, with the exact prompt text for each task, and let the owner create it.
Only the 16 schedulable commands can be fired as slash commands:
`/ingest`, `/link`, `/lint`, `/review`, `/weekly`, `/monthly`, `/metrics`,
`/health`, `/commit`, `/stale`, `/orphans`, `/prune`, `/archive`, `/dedupe`,
`/backfill` and `/index`. Every other command sets
`disable-model-invocation: true`, which stops a scheduled task running it from
Claude Code v2.1.196. For those, write a plain-language prompt.

## Workflow

1. **Read the vault.** `CLAUDE.md` (does it grant autonomy, and what rails does
   it set), the owner queue, how many raw items are pending, how many pages, and
   whether the vault is a git repository. If you cannot tell whether the owner
   has granted autonomy, they have not: schedule read-only and proposal jobs
   only (step 4).
2. **Pick where it runs.** Check the current Claude Code documentation first
   (https://code.claude.com/docs/en/scheduled-tasks and the pages it links);
   these features change. As of the pages read when this skill was written:

   | | Cloud (routines) | Desktop | `/loop` |
   |---|---|---|---|
   | Runs on | Anthropic cloud | The owner's machine | The owner's machine |
   | Machine must be on | No | Yes, app open and awake | Yes, session open |
   | Sees local files | No, a fresh clone of GitHub repositories each run | Yes | Yes |
   | Minimum interval | 1 hour | 1 minute | 1 minute |
   | Permission prompts | None, runs autonomously | Set per task | Inherits session |
   | Missed runs | Not stated | One catch-up run on wake | No catch-up |

   Cloud routines work from a GitHub clone and push to `claude/` branches
   unless the prompt says otherwise, and `raw/workspace/` is git-ignored, so a
   cloud run cannot see it. A cloud routine includes all of the account's
   connectors by default, and can write through them. Use cloud only if the
   owner already keeps the vault in a GitHub repository and has decided that is
   acceptable for what is in it. A local vault that should never leave the
   machine means Desktop, or `cron` or Task Scheduler running Claude Code
   headless. `/loop` expires recurring tasks after seven days and is for
   polling inside a session, not for maintenance.
3. **Choose the jobs and cadence.** Start from these, then adjust to volume:

   | Job | Command | Cadence |
   |---|---|---|
   | Ingest | `/ingest` | Daily, overnight, after a week of running it by hand |
   | Link | `/link` | Weekly, after a week of ingestion |
   | Lint | `/lint` | Weekly, after link |
   | Review | `/review` or `/weekly` | Weekly, on the morning the owner plans |
   | Metrics | `/metrics` | Monthly |
   | Archive pass | `/archive` | Monthly |
   | Backlog over 100 | `/backfill` | One batch per run until clear |

   `/commit` is rarely needed as its own task, because every run commits itself.
   Do not schedule `/monthly` and `/metrics` as well: `/monthly` records the
   snapshot. Schedule ingest last. Pick a start minute that is not `:00`, since
   scheduled starts on the hour can be late.
4. **Write the prompt for each.** Give it in two forms: the slash command, and
   a self-contained plain-language prompt for older Claude Code versions or for
   anything outside the 16. Every prompt must say, whether or not `CLAUDE.md`
   already does:
   - the job and its limit (for ingest, the 20 oldest pending items);
   - checkpoint by path before any merge, archive, rename or batch rewrite;
   - archive, never delete;
   - skip and queue anything that hits a hard stop (a secret, a connected
     service write, a person's details leaving the vault, two pages you cannot
     tell apart);
   - one commit for the run, by explicit path, with the run id in the message;
   - a report in counts and names.
   If `CLAUDE.md` grants no autonomy, the prompt says instead: do not change
   existing pages, write what you would do to `output/<job>-<date>.md`, and
   report the path.
5. **Name the setup steps** for the chosen surface, and the first check: run each
   task once by hand, read the log entry and the commit, and only then let it
   run on its own.

## Output format

```
Where: <cloud | desktop | headless cron> - <why, in one line>

| Job | Cadence | Slash command | Needs |
|---|---|---|---|

Prompt, <job>:
<exact text, ready to paste>

Before you enable it: <what to verify>
Not scheduled, and why: <jobs left manual>
```

## Calibration

A scheduled run that produces nothing the owner reads gets switched off. Every
prompt ends with a report, even one line, in counts.

Never write a prompt that tells an unattended run to message, email, post or
publish. Writing to a connected service, pushing and publishing are for a live
session when the owner asks.

Claude Code also has a built-in `/schedule` for creating cloud routines. If it
opens that flow instead of this skill, say so and continue here in plain
language. Creating or editing a scheduled task is the owner's act: do not do it
from inside a scheduled run.
