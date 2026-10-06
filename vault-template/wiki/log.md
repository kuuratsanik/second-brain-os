---
title: Log
type: log
---

# Log

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
