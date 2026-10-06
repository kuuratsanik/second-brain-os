---
name: second-brain-brief
description: >-
  Write a short brief of what needs the owner's attention in a second-brain
  vault: raw sources added since the last brief, the needs-owner queue,
  experiments and ideas due for a decision, stale pages, likely duplicates, and
  the path of the health dashboard. Reports and changes nothing except its own
  brief page and one log line, so it is safe to schedule. Use this skill when the
  user asks for a brief, "what needs me", a morning or weekly summary of the
  vault, or when a scheduled task fires `/brief`. Do NOT use to ingest, merge,
  archive or review an experiment (those have their own skills), or to answer a
  question about the vault's content (second-brain-ask).
---

# Brief the owner

The vault collects work for the owner faster than the owner looks at it:
sources that arrive, questions that wait, experiments whose end date has
passed. The brief is one page that lists them, so the owner opens one file
instead of six.

## Core rule

Report; do not repair. The only files you write are `output/brief-YYYY-MM-DD.md`
and one line in `wiki/log.md`. Every other thing you find is listed with the
command that deals with it. This is why the brief can run unattended: it never
moves a page, changes a status or reads a connected service.

## Workflow

1. **Find the last brief.** Search `wiki/log.md` for the latest line whose
   operation is `brief`. Its date is the start of the window. If there is none,
   use the last seven days and say so. If an argument names a date, use that.
   Read the previous brief page if it exists, so you do not list the same raw
   file twice.
2. **Raw sources added since.** List files under `raw/` (skip `raw/assets/`
   and README files) whose `YYYY-MM-DD-` name prefix is on or after the start
   date; for a file with no date prefix, use its modification time. Count a
   `-clean` file and its original as one item. Group by folder. For each, say
   whether a source page already points at it (a page whose `raw:` field holds
   its path); the rest are pending ingest. Name the files; do not quote them.
3. **The needs-owner queue.** Read the `## Waiting` section of
   `wiki/systems/needs-owner.md`. Report the number of entries, the oldest
   five with their dates, and any older than 30 days. For an entry that names a
   `restricted` page, give the path and say "restricted", not what it says.
4. **Experiments and ideas due.** Follow the status table in
   `second-brain-lifecycle`, read only. List: experiments `active` whose `end:`
   date has passed (review due); `planned` experiments whose `start:` date has
   arrived; experiments in `reviewing` with no decision on the review page;
   ideas at `considering` for 30 days or more (or the number the lifecycle
   page sets). More than three `active` experiments is a line of its own. Do
   not change a status or write a review: point to `/experiment-review`.
5. **Stale pages.** Run from the vault root:

   ```bash
   python3 scripts/link_check.py . --stale 90
   ```

   Report the count and the ten oldest by path and age. If the vault has no
   `scripts/` folder (the kit is installed as the `second-brain` plugin), run
   `${CLAUDE_PLUGIN_ROOT}/scripts/link_check.py` instead; Claude Code fills in
   that path only for a plugin install. Stale does not mean wrong: point to
   `/stale` and `/prune`.
6. **Duplicates.** `python3 scripts/link_check.py . --duplicates` (same
   fallback). Report each group by path. Do not merge; point to `/dedupe`.
7. **The dashboard.** Run
   `python3 scripts/dashboard.py . --out output/dashboard.html --stale-days 90`
   (same fallback for `scripts/dashboard.py`) and report the path. Quote two or
   three of its counts if the script's output gives them (pages, orphans,
   queue length). If it fails, say so and give the error in one line; the rest
   of the brief still stands. The dashboard is a local file: it may name
   private pages, so do not publish or share it.
8. **Write the brief** to `output/brief-YYYY-MM-DD.md`. If that file exists,
   write `output/brief-YYYY-MM-DD-2.md`; never overwrite or delete a brief.
   Frontmatter:

   ```yaml
   ---
   title: Brief 2026-10-06
   lang: en
   sensitivity: private
   maintained_by: agent
   created: 2026-10-06
   updated: 2026-10-06
   ---
   ```

   `private` because it names pages and queue items. Write it in the language
   the owner is addressed in. Link wiki pages with `[[page]]`.
9. **Log and commit.** Add one line to `wiki/log.md`:
   `2026-10-06 brief output/brief-2026-10-06.md (<n> raw, <n> queued, <n> due, <n> stale, <n> duplicate groups)`.
   Commit the brief and the log by path, following `second-brain-commit`, with
   the subject `run-YYYY-MM-DD-brief`. Skip a path git ignores. Never
   `git add -A`.

## Output format

The brief page and your reply use the same shape:

```
Since: <date> (<from the last brief | default seven days | argument>)

Needs you now
- <n> in the queue (oldest <date>): <up to five, one line each>
- <n> experiments or ideas due: <path: what is due>

New since the last brief
- raw/: <n> files, <n> pending ingest: <folder: names>

Housekeeping
- Stale (90+ days): <n>, oldest <path, age>
- Possible duplicates: <n groups>: <paths>
- Dashboard: output/dashboard.html

Next: <the one or two commands that clear the most, e.g. /ingest, /experiment-review>
```

Keep it under one screen. Counts first, names after. An empty section says
"none" in one word.

## Calibration

A brief nobody reads gets switched off. Put what needs a human decision first
and the housekeeping last, and leave out anything that is zero. Do not list
every stale page; ten is enough, with the total.

Do not pull new material from Gmail, Granola, Slack or any other service while
briefing. If the owner wants that, they run `/capture`. In a scheduled run do
not ask questions and do not offer the setup interview: if something is
unclear, put it in the brief.

If `wiki/log.md` is missing or malformed, use the default window, say so in
the brief, and still write the log line.
