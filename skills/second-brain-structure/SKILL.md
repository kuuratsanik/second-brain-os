---
name: second-brain-structure
description: >-
  Adjust how existing pages in a second-brain vault are connected and
  classified: add missing links in both directions, split an overloaded page,
  fix a page's type, consolidate tags, add missing aliases, and add typed
  relations only where a source states them. Use this skill whenever the user
  asks to link pages, split a page, retype or refile one, audit tags or
  aliases, or add relation types such as supports or contradicts. Do NOT use to
  ingest new sources, to merge two pages, which is second-brain-merge, to
  rename a page, which is second-brain-rename, or to find orphans and broken
  links, which is second-brain-lint.
---

# Restructure existing pages

Links and types are how the vault is navigated. Adding a link is cheap and
rarely wrong; changing what a page is, or how it is cut, changes what other
pages mean.

## Core rule

Additive and mechanical changes (links, a missing alias) are made and logged.
Changes that alter what a page is or how it is cut (split, retype, a tag
consolidation, relation types) are proposed with the exact edit, and made only
after the owner agrees, or when the vault's `CLAUDE.md` grants that autonomy.
Never change the wording of a page marked `maintained_by: human`: links and
frontmatter only.

## Workflow

Pick the operation the request names.

1. **Link.** Read the named pages, or the pages added since the last review if
   none are named. Add links in both directions only where the relationship is
   real: one page uses, depends on, contradicts or explains the other, not merely
   shares a word. Link the first mention in running text, or add it to a
   Related list. Create no pages and rewrite no content; a missing target goes
   under Gaps in `index.md`.
2. **Aliases.** Find acronyms, alternate spellings, other-language names and
   common short names in the text that are not in a page's `aliases`. Propose
   each addition; missing aliases are the main reason a vault grows two pages
   for one thing.
3. **Tags.** List every tag with its count. Flag tags used once, near-synonyms,
   and tags outside the vocabulary in `CLAUDE.md`. Propose one consolidation
   map, old tag to new.
4. **Retype.** Check the page against its type's contract in `CLAUDE.md`. A
   source page that explains an idea is a concept page in the wrong folder.
   Propose the new type, folder and the sections to rewrite; keep every claim
   and its source. Move the file with `git mv`, naming both paths exactly, after
   `mkdir -p` on the destination folder.
5. **Split.** If a page holds more than one idea (unrelated section headings,
   claims that cannot be explained together), propose the split points and the
   titles of the resulting pages. On approval, create the new pages with their
   claims and sources, keep the original as the page for its core idea, link it
   to the new pages and back, and repoint an inbound link only where it clearly
   meant one of the parts.
6. **Typed links.** Add a relation type (supports, contradicts, extends,
   part-of, applies) only where the page or its source states the relationship.
   Never infer one. Use the notation the vault already uses; if it has none,
   propose one and ask before applying it anywhere.
7. **Checkpoint first** for retype, split and any tag or alias change across more
   than a few pages: commit the paths you will change, by path, as
   `checkpoint: <op> <run id>`. Without a repository, propose only.
8. **Log** each operation in `log.md`.
9. **Commit the run** by path, following `second-brain-commit`, with the subject
   `run-YYYY-MM-DD-<link|structure>`. Nothing changed means no commit.
10. **Report.**

## Output format

```
Operation: <link | aliases | tags | retype | split | typed-links>
Pages read: <n>
Changed: <n> pages - <list>
Proposed, not applied: <n> - <each with the exact edit>
Gaps: <targets that do not exist yet>
```

## Calibration

Linking too eagerly is the usual failure: every page ends up linked to every
page and the graph stops saying anything. If you would have to argue for the
link, leave it out.

Do not split a page just because it is long. Split when it holds two ideas that
other pages link to separately.

A tag used once is not automatically wrong; it may be new. Propose, do not
assume.
