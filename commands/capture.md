---
description: Save a Gmail thread, Granola meeting or Notion page into raw/
argument-hint: "[what to capture]"
disable-model-invocation: true
---

Capture $ARGUMENTS from your connected services into `raw/` as new files with source frontmatter: Gmail threads to `raw/workspace/email/`, Granola meetings (notes and transcript) to `raw/meetings/`, Notion pages to `raw/workspace/docs/`. Read-only on the service: nothing is sent, labelled, changed or deleted. Email and meetings default to `private`, and the file asks you before it takes in other people's personal data. It stops at `raw/`; run `/ingest` to turn the files into pages.

Follow the `second-brain-capture` skill.
