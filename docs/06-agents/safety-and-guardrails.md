# Guardrails

The rule this whole section rests on:

**Keys, not prompts.**

Telling an agent not to do something is a preference. It is not a boundary. If
the agent technically can delete a file, empty a folder or send an email, then
one day, in a context you did not anticipate, it will.

Control what is possible at the permission level. Then the instruction in
`CLAUDE.md` is a preference sitting on top of a boundary, rather than the only
thing between your notes and a bad run.

## Scope write access

The agent needs write access to the vault. It does not need write access to your
home directory, and a scheduled task running with broad filesystem permissions is
a large blast radius for a small convenience.

Same principle for connectors: read-only wherever the option exists. A calendar
connector that can only read cannot cancel a meeting, no matter what a
misinterpreted instruction says.

## Archive, never delete

Deletion is the one operation you cannot recover from by reading a diff, because
the content is gone and only the absence remains.

Rule: retire a page by moving it to `archive/`, keeping its path, and write a
line in `log.md` naming it and why. Merges count: the absorbed page is archived
with a `merged_into` field, its aliases move to the survivor and inbound links
are repointed. Applied consistently, a page that vanishes is always traceable
and restorable by moving it back, and "where did that page go" stops being an
unanswerable question.

The [vault template](../../vault-template/CLAUDE.md) goes further and treats
deleting files as a hard stop. The agent never hard-deletes anything, never
touches `raw/`, `journal/` or `output/` destructively, and never archives hubs,
the index, the log or anything in `wiki/systems/`. Imports that would have
dropped material (a chat export's "delete" pile, for instance) skip it and
record it instead.

## A worked example: settings and a hook

The [vault template](../../vault-template/README.md#what-is-enforced-and-what-is-not)
ships two files that turn some of its rules into boundaries. Both are copied
into the vault's `.claude/` folder.

- **`.claude/settings.json`** holds permission rules in three lists, `deny`,
  `ask` and `allow`. A deny rule wins over an ask rule, and an ask rule over an
  allow rule. The syntax is in the
  [permissions documentation](https://code.claude.com/docs/en/permissions).
- **`.claude/hooks/guard.py`** is a PreToolUse hook. Claude Code runs it before
  each file edit or shell command, including PowerShell (partially covered), and
  exit code 2 blocks the call. It runs once more when the session stops, to warn
  about uncommitted paths; that one only warns. The protocol
  is in the [hooks documentation](https://code.claude.com/docs/en/hooks). The
  hook exists because permission rules cannot say "existing files only", which
  the append-only `raw/` folder needs.

What this enforces, per the template's own table:

- no push, remote change, hard reset, `--amend`, rebase or `revert --abort`;
- no `rm`, `git rm`, `git clean` or `find -delete`;
- moves and copies stay inside the vault and never overwrite protected paths;
- `journal/`, `scripts/` and `.claude/` are owner-only, so the agent cannot
  write a script and then run it;
- no changes to existing files in `raw/`; new files are allowed;
- `CLAUDE.md` editable only in its Profile block;
- no staging of `raw/workspace/`;
- curl and wget uploads are denied, and web access asks first;
- by tool-name pattern, no writes through connected services.

What stays at the prompt level: the checkpoint, the log entry, the report and
the queue, secrets, and merging people. Neither layer reads a script's insides,
so a Python file the agent writes and runs can still delete things. The ask rules
are skipped in `bypassPermissions` mode, so don't run the vault in it; the deny
rules and the hook still apply. For operating-system enforcement, turn on Claude
Code's sandbox. Check the connector
patterns against the tool names your own connectors expose, because they differ
by server.

The rest of this page is the prompt level. It still matters, but it sits on top
of these boundaries and does not replace them.

## Git is the real safety net

Every guardrail above is preventive. Git is what saves you when one fails.

The vault has to be its own git repository for this to work. The template's
rules:

- **Checkpoint before destructive steps.** Before a merge, prune, archive,
  rename, split or any batch rewriting more than a few existing pages, the agent
  commits exactly the paths it is about to change, by path, with a message
  `checkpoint: <op> <run id>`. If the checkpoint fails, it queues the problem and
  carries on with non-destructive work only.
- **One commit per run,** staging only the paths that run wrote, by path. Never
  `git add -A` or `git add .`, which would sweep in your own uncommitted edits
  and anything git-ignored. The message starts with the run id, such as
  `run-2026-10-05-ingest`.
- **Restore by path.** A bad ingest is a revert of that run's commit, or a
  restore of the paths it listed. `git checkout .` and `git reset --hard`
  discard your own unrelated work along with the agent's, so they are not
  the fix. `/rollback` reverts that run's own commit only.
- **Never stage a file in which a secret was found.** Report the file and kind,
  not the value.

Read the diffs from scheduled runs occasionally, especially in the first weeks.
That is how you learn what your agent actually does at 7am, which is reliably
different from what you assumed.

## A queue and hard stops

A scheduled run cannot ask a question. The template gives it somewhere to put
one: `wiki/systems/needs-owner.md`, a page where each skipped item is recorded
with what it was, why it stopped and what the agent needs from you. The agent
searches the page first and updates the date on an existing entry instead of
adding a second one. You answer an entry and the agent moves it to Done.

Items go there when they hit a hard stop. In a live session the agent asks; in a
scheduled run it skips and queues. The template's hard stops:

- writing to any connected service, pushing to a remote, or publishing, which
  happens only when you ask for that specific action in a live session
- any web request or API call carrying a person's name or email, or content from
  `private` or `restricted` pages
- anything irreversible: deleting files, force-push, rewriting history,
  `git clean`, emptying `archive/`
- credentials, tokens or account numbers in any file
- changing `CLAUDE.md` (except the Profile block), skills, commands or schedule
  prompts
- merging two people, or two pages whose identity is uncertain

## Dry runs

For anything that touches many files, run it once in report-only mode.

```
Do a dry run: list every page you would create, update or archive, and the links
you would add. Write nothing.
```

The output takes a minute to read and catches misread instructions before they
become four hundred edits.

## Watch for scope creep

Agents extend the job. Asked to ingest, an agent may also tidy an unrelated page,
fix formatting, rename something for consistency. Each is defensible; together
they mean you cannot tell what a run did without reading everything.

Instruct explicitly: do the job asked, list anything else you noticed, change
nothing else.

## What not to put in the vault

Credentials, API keys, anything you are under obligation to keep confidential,
other people's private information.

Not because the agent will leak it, but because the vault is a single file tree
that gets synced, committed, backed up and occasionally shared. Every copy is
another place that content exists. See
[privacy](../09-maintenance/privacy-and-secrets.md).

## Next

[Retrieval](../07-retrieval/README.md), for getting answers out of what all this
built.
