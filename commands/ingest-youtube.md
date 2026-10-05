---
description: Ingest a video or podcast transcript
argument-hint: "[video URL]"
disable-model-invocation: true
---

Pull the transcript for $ARGUMENTS into `raw/`, clean it with `second-brain-transcript`, then ingest. Split by topic first if the recording covers more than one.

Follow the `second-brain-transcript` skill.
