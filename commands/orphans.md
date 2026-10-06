---
description: Find unreachable pages
---

List pages with no inbound links, of any age. For each, either propose where it should be linked from, or flag it as an archive candidate if there is nowhere; the move itself, with `git mv` after `mkdir -p`, is `/archive`. Link-adding is mechanical; archiving follows `/archive`. Use `/prune` for old pages with one source, and `/stale` for pages nobody has updated.

Follow the `second-brain-lint` skill.
