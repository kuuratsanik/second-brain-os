---
description: Ingest someone else's video or podcast from a URL
argument-hint: "[video URL]"
disable-model-invocation: true
---

Pull the transcript for $ARGUMENTS into `raw/`, clean it with `second-brain-transcript`, then ingest it as a source page attributable to its speaker ("this source says"). Split by topic first if the recording covers more than one. For your own recordings and voice notes use `/ingest-voice`.

Follow the `second-brain-transcript` skill.
