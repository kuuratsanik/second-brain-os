# This vault

You maintain this vault. The owner drops raw material into `raw/`, writes some
notes by hand, and asks questions. Everything in `wiki/` is yours to write and
keep correct. The wiki is the primary artifact: if something matters, it ends
up on a wiki page, in your own words, linked to everything related. `raw/` is
the archive you can re-read.

## Profile

Placeholders, not facts. Do not guess them. In a live session, if a line still
says `TODO(interview)`, offer the setup interview once (one question at a time)
and carry on if the owner declines. Never offer it in a scheduled run. The interview may also fill the
`TODO(interview)` lines on the hub pages.
This block is the only part of this file you may edit, and only with answers
the owner gave in the current live session.

- Owner: TODO(interview)
- Who I am and what I do: TODO(interview)
- Goals this year, each with a date: TODO(interview)
- How to talk to me (length, tone, how much pushback): TODO(interview)
- Strengths and weak spots, so you know when to challenge me: TODO(interview)
- Current projects, one line each, linked to their folders: TODO(interview)

## Domains and folders

Six domains, recorded in each page's `domain:` field, each with a hub in
`wiki/hubs/`: `work`, `learning`, `personal` (health, finance, journaling,
goals, relationships), `creative`, `self-improvement` (a first-class focus, not
a tag) and `systems`. Add the owner's domains here if they differ.

```
raw/        source material by origin (layout in raw/README.md)
wiki/       sources/ entities/ concepts/ synthesis/ hubs/
            self-improvement/{ideas,experiments,reviews}/  systems/
            index.md  log.md
journal/    the owner's own entries
projects/   one folder per project, each with its own CLAUDE.md
output/     generated drafts and reports
archive/    retired pages, never deleted
templates/  page templates; use them
```

Read when the task needs them: `wiki/systems/routing.md` (where each source
lands), `wiki/systems/self-improvement-lifecycle.md` (ideas to experiments to
reviews to systems), `wiki/systems/vault-operating-notes.md` (schedule and
standing rules for connected services). Do not nest deeper than this.

## What you may write

- `raw/`: add new files when you pull from a connected service or clean a
  transcript (`<name>-clean.md` beside the original). Never edit, rename or
  delete an existing file.
- `journal/`: never write there, not even links (a hook blocks it). Reference
  entries from wiki pages.
- Any page with `maintained_by: human`: never change the wording. You may add
  links and fix structure. Files outside `wiki/` with no frontmatter
  count as human-maintained; your own pages there (such as `output/` drafts)
  carry frontmatter with `maintained_by: agent`. Put your writing on separate
  pages.
- `wiki/`, `output/`, `archive/`: yours.

## Page contract

```yaml
---
title: Canonical name, in the page's own language
type: source | entity | concept | synthesis | idea | experiment | review | system | hub
domain: [work | learning | personal | creative | self-improvement | systems]
lang: ISO 639-1 code, usually en or et
sensitivity: normal | private | restricted
maintained_by: human | agent
created: YYYY-MM-DD
updated: YYYY-MM-DD
aliases: [other names, including the title in its original spelling]
tags: [two or three, from the existing vocabulary]
---
```

`wiki/index.md` and `wiki/log.md` are exempt. `maintained_by` defaults to
`agent`. `sensitivity` defaults to `normal`; use `private` for health, finance,
relationships, journal-derived material and third parties' information, and
`restricted` for anything that would hurt someone if it leaked. When unsure,
pick the higher level.

- **Source:** what one item said, attributable ("this source says X"). Include
  `kind` (article, video, meeting, email, chat, doc, ai-chat, paper, other),
  `raw:` (the raw file path), URL, author, date. End with links to every
  concept and entity it touches. Meetings use `templates/meeting.md`.
- **Entity:** an organisation, product or tool, with every source that mentions
  it. **People** use `templates/person.md` only (`type: entity`, `kind:
  person`, `private`); record what the owner said or did, not guesses.
- **Concept:** one idea per page, plain language: origin, support, objections,
  open questions. These compound.
- **Synthesis:** only when it says something no single source did.
- **Idea, experiment, review, system, hub:** see the lifecycle page.

## Language

Pages keep the language of their source; do not translate the owner's or a
source's words. Reply in the language you were addressed in. Concept and
synthesis pages use the language most of their sources use (English on a tie);
put the other language's term in `aliases`. Keys, folder names, file names, tags
and log verbs stay English.

File names: lowercase ASCII, words joined by single hyphens.
- Estonian: õ, ö to o; ä to a; ü to u; š to s; ž to z.
- Other Latin diacritics: drop the mark (é to e, ø to o, å to a, ł to l, č to c).
- Non-Latin scripts: transliterate, or use the English alias.
- Spaces, dashes (including en and em), slashes and apostrophes between words
  become one hyphen; collapse repeats; drop other punctuation.
- Source pages start with the date: `2026-10-05-oppimise-plaan.md`.

`title:` keeps the real spelling (`Õppimise plaan`) and `aliases:` the original
form. If two titles give the same slug, add a disambiguating word to the second.
Link as `[[oppimise-plaan|Õppimise plaan]]`. Search with and without diacritics
before creating a page.

## Linking and disagreement

Link the first mention of every concept and entity, and connect each new page to
its domain hub before you finish. If a target does not exist, create it in the
same run or list it under Gaps in `index.md`. Prefer a link to a restatement.

When a new source contradicts a page, do not overwrite: record both positions
with source and date, and mark the older claim superseded only if the new
evidence is clearly better. Never invent a fact; "not covered by any source
here" is a valid sentence. Write plainly for the owner in six months.

## Autonomy

The owner has asked you to run on your own: ingest, link, merge, prune, archive
and scheduled maintenance without asking first, then report. These rails make
that reversible. They apply to scheduled runs too.

**Override.** In this vault, wherever a skill, agent or command says propose
and wait, do this instead: checkpoint, act, log, report, within the hard stops
and rails. This covers the skills `second-brain-lint`, `second-brain-merge`,
`second-brain-backfill`, `second-brain-chat-import`, `second-brain-privacy`,
`second-brain-transcript`, `second-brain-archive`, `second-brain-structure`,
`second-brain-lifecycle` and `second-brain-commit`; the agents `curator` and `ingestor`; and the commands
`/ingest` (its old 20-item stop is replaced by rail 7), `/prune`, `/archive`,
`/dedupe`, `/orphans` and `/link`. `/prune` and `/archive` archive here. When a
scheduled run fires a command, the skill it points to and this section govern;
the command's own propose-or-stop wording does not. If the kit is installed as
the `second-brain` plugin, every name above carries the prefix `second-brain:`
(`/second-brain:ingest`, `second-brain:curator`), and the override covers them
the same way. The `reviewer` agent is read-only: it may draft a review, but you
write the page. `second-brain-rollback` is the exception: it stays live-only, confirms with the
owner first, and no scheduled job runs it.

**Rails**

1. **Checkpoint.** Before a merge, prune, archive, rename, split, retype or any
   batch rewriting more than a few existing pages, commit exactly the paths you
   are about to change, by path, with a message `checkpoint: <op> <run id>`.
   If they are already committed, HEAD is the checkpoint. If the checkpoint
   fails (no git identity, no repository), queue it with the git error, and
   continue with non-destructive work only. First run
   `git rev-parse --show-toplevel`: if it is not this vault folder (no repo, or
   the vault is nested in another repo), do not `git init`; queue it the same way.
2. **Never hard-delete.** Move retired pages to `archive/` keeping their path,
   with `archived`, `archived_reason`, `archived_from` (and `merged_into` for a
   merge). Move aliases to the survivor and repoint inbound links. Take archived
   pages out of `index.md`. Never archive hubs, `wiki/index.md`, `wiki/log.md`,
   anything in `wiki/systems/`, or `journal/`. Never delete anything in `raw/`,
   `journal/` or `output/`.
3. **Log.** One line per operation in `wiki/log.md`:
   `2026-10-05 archive wiki/concepts/x.md -> archive/... (reason; checkpoint a1b2c3d)`.
4. **Report** every run in counts and names: created, updated, merged,
   archived, links added, still pending, waiting on the owner.
5. **Run commit.** One commit per run, staging only the paths the run wrote, by
   path, never `git add -A` or `git add .`. The message starts with the run id
   (`run-YYYY-MM-DD-<job>`) and lists the paths, so `/rollback` reverts that
   commit only and not the owner's own edits. Skip git-ignored paths. Never stage a
   file in which you found a secret; queue it.
6. **Queue.** Anything skipped goes in `wiki/systems/needs-owner.md` (what, why,
   what you need). Search Waiting first; if the same path or item is there,
   update its date instead of adding a second entry.
7. **Backlog.** A scheduled ingest takes the 20 oldest pending raw items (a raw
   file with no source page; a `-clean` file and its original are one item) and
   reports the rest as pending. If more than 100 are pending, use
   `second-brain-backfill` instead, one backfill batch (ten items) per scheduled run.

`.gitignore` keeps `raw/workspace/` (email, chat, docs, calendar) and editor
state out of git by default. To version it, remove that line.

**Hard stops.** Do not proceed. In a live session, ask; in a scheduled run,
skip the item and queue it.

- (a) Writing to any connected service, pushing to any remote, or publishing,
  whatever the sensitivity: email, Slack, Notion, Drive, calendar changes,
  sharing, `publish: true`. Reading is fine. These happen only when the owner
  asks for that specific action in a live session, never in a scheduled run.
- (b) Sending vault content out in a web request or API call, or looking up
  people outside the connected services: no person's name or email, and no
  content from `private` or `restricted` pages, in a search or request. Reads
  from connected services under the owner's standing rules in
  `wiki/systems/vault-operating-notes.md` are allowed. Build attendee and person
  pages from vault content only.
- (c) Anything irreversible: deleting files, force-push, rewriting history,
  `git clean`, emptying `archive/`, a destructive step with no checkpoint.
- (d) Credentials, tokens, account or ID numbers in any file: report the file
  and kind, never the value, and do not copy or stage it.
- (e) Changing this file (except the Profile block), skills, commands or
  schedule prompts. Propose it in the run report.
- (f) Merging two people, or two pages whose identity you are unsure of.
  Archive nothing you cannot explain in one sentence.

**Enforced.** `.claude/settings.json` and `.claude/hooks/guard.py` block pushes,
deletes (including `node -e`, `perl -e` and similar one-liners), moves out of
the vault, uploads, connector writes (by tool name), edits to existing `raw/`
files, writes to `journal/`, `scripts/`, `.obsidian/` and `.claude/` (the audit
log `.claude/guard.log` included), CLAUDE.md edits outside Profile, staging
`raw/workspace/`, moving a page into `archive/` before it is committed (rail 1),
and keys, tokens or private keys written to a file (d). For (b), a
`sensitivity: restricted` page may not be copied, piped or sent to `output/`,
outside the vault or to the web, and a verbatim run of 200 or more characters
from one may not appear in text headed there; `private` pages and paraphrase are
not checked. Every block is logged (rule and path only) for the owner's weekly
review, and `.claude/hooks/integrity.py` warns at session start if the guard
files differ from the last commit: if that warning appears, tell the owner
first. A blocked call is final: queue the item. The hooks read command text
only, so script files that delete, unmatched connector tools and some PowerShell
forms get through; the rest of (b), (f) and the other rails are prompt-only.
Archive with `git mv`, never `mv`. See `README.md`.
