---
name: second-brain-archive
description: >-
  Find pages that no longer belong in a second-brain vault's active wiki and
  move them to archive/ reversibly: orphans with nowhere to link, stale concept
  pages, pruning candidates (one source, no inbound links after a year, stubs
  never filled) and cold material. Use this skill whenever the user asks what is
  safe to remove, to prune, archive or clean out the vault, to list orphaned or
  stale pages, or when a scheduled archive or prune pass fires. Do NOT use to
  delete anything, to merge duplicates, which is second-brain-merge, or to fix
  broken links and frontmatter, which is second-brain-lint.
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
   | Orphans | Pages with no inbound links | Find where each should be linked from; archive only if there is nowhere |
   | Stale | Concept pages not updated in 90 days, with how many sources arrived on their topic since | Report only. A stale page with new sources needs updating, not archiving |
   | Prune | Concept pages with one source and no inbound links after a year; stubs under about 40 words that never filled | Archive candidates |
   | Archive | Cold material the owner names, or pages untouched for a year that nothing links to | Archive candidates |

   Use `scripts/link_check.py` and `scripts/vault_stats.py` for orphans and
   stubs where they exist.
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
   they are already committed, HEAD is the checkpoint). Move each page under
   `archive/` keeping its path below it (`wiki/concepts/x.md` becomes
   `archive/wiki/concepts/x.md`). Add `archived: YYYY-MM-DD`,
   `archived_reason` and `archived_from` to its frontmatter. Remove it from
   `index.md`. Move its aliases to the page that now covers the topic, if there
   is one.
5. **Log** one line per page in `log.md`:
   `YYYY-MM-DD archive wiki/concepts/x.md -> archive/wiki/concepts/x.md (reason; checkpoint a1b2c3d)`.
6. **Report.**

## Output format

```
Candidates: <n> (<n> orphans, <n> stale, <n> prune, <n> cold)
Archived: <n> | Proposed only: <n> | Linked instead: <n> | Left alone: <n>

<path> - <reason> - <inbound> in, <sources> sources, updated <date> - <action>

Restore: move the file back and delete the archived* keys.
```

## Calibration

When the vault does not grant autonomy, a scheduled run has nobody to ask:
write the proposal to `output/archive-<date>.md` (or the owner queue the vault
keeps, `wiki/systems/needs-owner.md` in the template), move nothing, and report
the path. If a cut finds nothing, say so in one line.

Thin is not the same as unneeded. A one-source page that three live pages link
to is doing its job. The test is whether anything would notice it gone.

If the checkpoint cannot be made (no git, nested repository, no identity), do
not move pages: propose only and say why.
