---
name: second-brain-archive
description: >-
  Move pages that no longer belong in a second-brain vault's active wiki to
  archive/ reversibly: pruning candidates (one source, no inbound links after a
  year, stubs never filled), orphans the linter found no home for, and cold
  material the owner names. Use this skill whenever the user asks what is safe
  to remove, to prune, archive or clean out the vault, or when a scheduled
  archive or prune pass fires. Do NOT use to delete anything, to merge
  duplicates, which is second-brain-merge, to find and link orphans or fix
  broken links, which is second-brain-lint, or to list stale pages, which is
  second-brain-graph.
---

# Archive cold pages

A vault that only grows gets slower to read and harder to trust. Removing the
wrong page is worse than leaving a dead one, so removal here is always a move.

## Core rule

Archive, never delete. Propose first. Move a page only when the vault's
`CLAUDE.md` grants that autonomy or the owner approves in this session.

## Workflow

1. **Select candidates.** Each command is a different cut:

   | Cut | Selects | Result |
   |---|---|---|
   | Orphans | Pages `second-brain-lint` found with no inbound links and nowhere to link them from | Archive candidates |
   | Prune | Concept pages with one source and no inbound links after a year; stubs under about 40 words that never filled | Archive candidates |
   | Archive | Cold material the owner names, or pages untouched for a year that nothing links to | Archive candidates |

   Use `scripts/link_check.py` and `scripts/vault_stats.py` for orphans and
   stubs where they exist. Stale pages (not updated in 90 days) are not a cut:
   listing them is `/stale`, and a stale page with new sources waiting needs
   updating, not archiving.
2. **Apply the protections.** Never archive hubs, `index.md`, `log.md`,
   anything in `wiki/systems/`, `journal/`, `raw/` or `output/`. Never archive a
   page with five or more inbound links, a page marked `maintained_by: human`
   (name it and ask), or a page you cannot explain archiving in one sentence. A
   page that still has an inbound link from a live page is not archived: report
   the link instead.
3. **Propose.** For each candidate: path, why, inbound count, source count, last
   updated, recommended action (link it, update it, archive it, leave it).
4. **Checkpoint, then move** only if allowed. Commit exactly the paths you will
   change as `checkpoint: archive <run id>` (the second-brain-commit rules; if
   they are already committed, HEAD is the checkpoint). Move each page with
   `git mv`, never plain `mv`, under `archive/` keeping its path below it. Create
   the folder first: for `wiki/concepts/x.md`, run `mkdir -p archive/wiki/concepts`,
   then `git mv wiki/concepts/x.md archive/wiki/concepts/x.md`. Name every file
   exactly, one `git mv` per page: no globs, since the vault's guard hook blocks
   a destination it cannot check. Add `archived: YYYY-MM-DD`,
   `archived_reason` and `archived_from` to its frontmatter. Remove it from
   `index.md`. Move its aliases to the page that now covers the topic, if there
   is one.
5. **Log** one line per page in `log.md`:
   `YYYY-MM-DD archive wiki/concepts/x.md -> archive/wiki/concepts/x.md (reason; checkpoint a1b2c3d)`.
6. **Commit the run** by path, following `second-brain-commit`, with the subject
   `run-YYYY-MM-DD-archive` (old and new path of every moved page, plus
   `index.md` and `log.md`). A proposal-only run changes nothing, so commits
   nothing.
7. **Report.**

## Output format

```
Candidates: <n> (<n> orphans, <n> prune, <n> cold)
Archived: <n> | Proposed only: <n> | Linked instead: <n> | Left alone: <n>

<path> - <reason> - <inbound> in, <sources> sources, updated <date> - <action>

Restore (owner step): <exact commands, below>
```

## Calibration

When the vault does not grant autonomy, a scheduled run has nobody to ask:
write the proposal to `output/archive-<date>.md` (or the owner queue the vault
keeps, `wiki/systems/needs-owner.md` in the template), move nothing, and report
the path. If a cut finds nothing, say so in one line.

Thin is not the same as unneeded. A one-source page that three live pages link
to is doing its job. The test is whether anything would notice it gone.

Restoring is the owner's step. The vault's guard hook blocks moves out of
`archive/`, so never run a restore yourself and never in a scheduled run. When
asked, list the exact commands for the owner to run or approve in a live
session: `git mv archive/wiki/concepts/x.md wiki/concepts/x.md`, remove the
`archived`, `archived_reason` and `archived_from` keys, add the page to
`index.md` again, and move its aliases back from the page that took them.

If the checkpoint cannot be made (no git, nested repository, no identity), do
not move pages: propose only and say why.
