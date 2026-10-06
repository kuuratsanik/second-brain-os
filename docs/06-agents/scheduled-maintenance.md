# Scheduling

Scheduled runs are what make the vault feel alive. You wake up and it has filed
what you clipped, noticed a contradiction, and left you three lines about what
changed.

They are also unattended writes to your notes, so the order matters: get the
[guardrails](safety-and-guardrails.md) right first, then schedule.

## Cadence per job

**Ingest, daily.** Overnight, on whatever accumulated in `raw/` during the day.
Daily is right because a batch gives the agent a chance to notice that three
things you saved are about the same idea. Hourly does not.

**Link, weekly.** Connections need material to connect. Run it after a week of
ingestion.

**Lint, weekly.** After the linker, so it catches what that pass broke.

**Review, weekly.** The one output you actually read, written as a review page
in the vault rather than a chat message. Put it on the morning you plan.

**Metrics, monthly.** Four numbers appended to a note. See
[metrics](../05-graphs/metrics.md).

**Archive pass, monthly.** Retire pages that have one source, no inbound links
and have sat for a year, and stubs that were never filled. They move to
`archive/`; nothing is deleted.

## Setting one up

In Claude Desktop, Code tab, then Routines, New routine, Local. The form takes a
name (unique across your tasks), a description, the instructions, and a schedule;
you pick the working folder, your vault, under the instructions (see the
[desktop scheduled tasks documentation](https://code.claude.com/docs/en/desktop-scheduled-tasks)):

```
Name:          vault-ingest
Schedule:      Daily, 7:00am
Instructions:  File the 20 oldest pending items in raw/ into the wiki
               following CLAUDE.md. Before any merge, archive or batch
               rewrite, commit a checkpoint of the paths you will change.
               Link what you create to existing pages. Update index.md and
               log.md. Do not delete anything; archive instead. If an item
               hits a hard stop (a secret, a connected service, a person's
               details leaving the vault, two pages you cannot tell apart),
               skip it and record it in wiki/systems/needs-owner.md. Make
               one commit for the run, staging only the paths you wrote,
               by path, with the run id in the message. Then write me three
               lines in counts and names: created, updated, archived, still
               pending, waiting on you.
```

A Desktop scheduled task runs on your machine, only while the app is open and
the computer is awake. A run missed while the machine slept is skipped; on wake,
Desktop starts one catch-up run for the most recent missed time and discards
older ones ([documentation](https://code.claude.com/docs/en/desktop-scheduled-tasks)).
"Overnight" therefore means a machine that is on overnight.

A scheduled task can fire a slash command only from the 16-command maintenance
set listed in [`commands/README.md`](../../commands/README.md) (`/ingest`,
`/link`, `/lint`, `/vault-review`, `/weekly`, `/monthly`, `/metrics`, `/health`,
`/commit`, `/stale`, `/orphans`, `/prune`, `/archive`, `/dedupe`, `/backfill`
and `/index`). The other commands set `disable-model-invocation: true`, and from
Claude Code v2.1.196 that also stops a scheduled task from running them
([skills documentation](https://code.claude.com/docs/en/skills)). Anything else
needs a plain-language prompt like the one above, and on an older version none
of the commands can be relied on. If you installed the kit as the `second-brain`
plugin, the commands carry the plugin prefix (`/second-brain:ingest`); see
[plugins](../../plugins/README.md#second-brain).
The backlog limit of 20 and the rest of the rails come from the [vault
template](../../vault-template/CLAUDE.md), which applies them to scheduled runs
too.

Or ask for it in a session: "set up a daily task at 7am that ingests raw/ and
summarises what changed".

From a terminal, `cron` or Task Scheduler calling Claude Code headless works the
same way, and is the better option if you want the run inside a git commit
automatically.

### Let the skill propose it

The `second-brain-schedule` skill, or the `/maintenance-schedule` command that
points at it, reads your vault and proposes the jobs, cadence, where each should
run and the exact prompt for each. It proposes only; you create the tasks. The
command is not called `/schedule` because that would shadow Claude Code's
built-in `/schedule`, which creates cloud routines.

### Why not cloud for a template vault

A cloud routine runs on a fresh clone of a GitHub repository, per Anthropic's
[routines documentation](https://code.claude.com/docs/en/routines). For a vault
that means four things:

- It cannot see git-ignored folders, so `raw/workspace/` (email, chat, docs and
  calendar pulls) is absent.
- It pushes its changes to `claude/` branches by default, so the run commit
  does not reach your local history until you merge that branch. The template
  treats pushing as a hard stop.
- The account's connectors are available by default, and a connector that can
  write will write without asking. The template treats writing to a connected
  service as a hard stop.
- It runs without permission prompts.

For a vault that follows the template, use Desktop scheduled tasks or headless
Claude Code, which run in your vault folder. These
features change, so check the documentation before relying on any of it.

### Permission mode for unattended runs

In the default permission mode, a headless run with the template refuses every
page write, because nobody is there to approve it. A Desktop run in Manual mode
stalls until you approve the action. Start the run
with `--permission-mode acceptEdits`, set the task's permission mode in the
Desktop form, or set `permissions.defaultMode` in `.claude/settings.json`. The
deny rules and the hook still apply. See the "Scheduled runs" paragraph in the
[vault template README](../../vault-template/README.md#what-is-enforced-and-what-is-not).

## What a run must produce

Three things, every time.

**A log entry.** Otherwise you cannot audit what happened while you were asleep.

**A commit.** One per run, with the run named in the message, staging only the
paths the run wrote. This is what makes a bad run revertible in one command
instead of an evening, without touching your own edits.

**A report to you.** Even one line. A scheduled task that produces nothing
visible is one you stop trusting and then stop reading.

## Detecting silent failure

The failure mode is not a crash. It is a run that completes and does nothing
useful: the source was empty, the API call failed halfway, the instructions
matched no files.

Two cheap checks. Have the run report counts, not just completion, so "ingested
0 sources" is visible. And look at commit frequency once a month: a week with no
commits from the daily task means it has been failing quietly since Tuesday.

## Start manual

Run each job by hand for a week before scheduling it. You are checking that the
output is good enough to accept without reading it closely, because that is
exactly what scheduling means.

Schedule the ingest last. It is the one that writes most.

## Next

[Subagents and parallel work](subagents.md)
