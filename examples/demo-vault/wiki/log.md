---
title: Log
type: log
---

# Log

> Fictional. This page belongs to the demo vault; the people, organisations and articles in it are invented.

One line per operation, newest at the bottom. This is the change log for the
whole vault: every ingest, merge, archive and rename goes here. Format:

```
DATE OPERATION target -> result
```

Destructive operations also name the checkpoint commit and the reason, so the
owner can undo them:

```
DATE archive wiki/concepts/x.md -> archive/wiki/concepts/x.md (reason; checkpoint a1b2c3d)
```

Operations: ingest, pull, link, merge, archive, rename, split, retype, lint,
review, rollback, skip. `skip` records an item sent to
[[needs-owner]].

The commit ids below are invented; this demo vault is not a git repository.

2026-08-13 link wiki/hubs, wiki/systems -> six hubs and four systems pages created from the vault template at setup
2026-08-13 ingest raw/clippings/2026-08-12-fifteen-minute-weekly-review.md -> wiki/sources/2026-08-12-fifteen-minute-weekly-review.md, wiki/concepts/weekly-review.md, wiki/concepts/time-boxing.md
2026-09-04 ingest raw/clippings/2026-09-03-retrieval-practice-at-work.md -> wiki/sources/2026-09-03-retrieval-practice-at-work.md, wiki/concepts/spaced-repetition.md, wiki/concepts/retrieval-practice.md
2026-09-06 link journal/2026-09-06.md -> idea captured at wiki/self-improvement/ideas/fifteen-minute-friday-review.md, status new
2026-09-11 skip calendar block for the Friday review -> hard stop (a); owner created it by hand; logged in wiki/systems/needs-owner.md
2026-09-11 review wiki/self-improvement/ideas/fifteen-minute-friday-review.md -> promoted to experiment wiki/self-improvement/experiments/friday-review-trial.md by the owner
2026-09-15 ingest raw/clippings/2026-09-14-oppimise-plaan.md -> wiki/sources/2026-09-14-oppimise-plaan.md (lang et, slug ASCII, title and original form in aliases)
2026-09-15 merge wiki/concepts/spaced-repetition.md -> wiki/concepts/retrieval-practice.md (same idea under two names; aliases moved to the survivor; checkpoint 4e91c07)
2026-09-15 archive wiki/concepts/spaced-repetition.md -> archive/wiki/concepts/spaced-repetition.md (merged into retrieval-practice; checkpoint 4e91c07)
2026-09-16 link wiki/self-improvement/ideas/morning-flashcards.md -> idea captured from the Estonian source, status new
2026-09-23 pull Granola -> raw/meetings/2026-09-22-q4-planning-sync.md (standing rule in wiki/systems/vault-operating-notes.md)
2026-09-23 ingest raw/meetings/2026-09-22-q4-planning-sync.md -> wiki/sources/2026-09-22-q4-planning-sync.md, wiki/entities/anu-kask.md, wiki/entities/mihkel-sepp.md, wiki/entities/kuusk-analytics.md
2026-09-26 skip raw/inbox/2026-09-25-vendor-call-notes.md -> hard stop (d), token found; not ingested, not staged; queued in wiki/systems/needs-owner.md
2026-09-30 ingest raw/youtube/2026-09-29-notes-that-link-back.md -> wiki/sources/2026-09-29-notes-that-link-back.md, wiki/concepts/note-linking.md, wiki/entities/margin.md
2026-09-30 review wiki/self-improvement/ideas/morning-flashcards.md -> status dropped by the owner; kept linked
2026-09-30 link wiki/synthesis/review-cadence.md -> created from three sources that disagree on spacing
2026-10-03 review wiki/self-improvement/experiments/friday-review-trial.md -> review written at wiki/self-improvement/reviews/friday-review-trial-review.md
2026-10-04 link wiki/hubs/hub-personal.md -> idea fifteen-minute-friday-review listed (journal-derived, domain personal added)
2026-10-04 link wiki/systems/friday-review.md -> system created from the adopted experiment
2026-10-04 lint wiki -> 0 broken links, 0 orphans, 0 stubs; Q4 priorities page listed under Gaps in index.md
2026-10-04 skip raw/inbox/2026-09-25-vendor-call-notes.md -> hard stop (d), token still present; entry in wiki/systems/needs-owner.md re-dated
2026-10-04 skip tag rename habit to routine (seven pages) -> checkpoint failed (git index.lock exists); queued in wiki/systems/needs-owner.md
