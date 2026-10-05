# raw/

Source material, grouped by where it came from. The grouping tells the agent
how to ingest each item; see the routing table in `CLAUDE.md`.

| Folder | What goes in it |
|---|---|
| `clippings/` | Web articles from Obsidian Web Clipper |
| `youtube/` | Video clips and transcripts |
| `meetings/` | Granola transcripts and notes |
| `workspace/email/` | Gmail threads |
| `workspace/chat/` | Slack threads |
| `workspace/docs/` | Notion pages and Google Drive files |
| `workspace/calendar/` | A dated snapshot of the week's events, written by the weekly review |
| `ai-chats/` | Exported AI chat history |
| `inbox/` | Anything else: PDFs, voice notes, loose files |
| `assets/` | Images and attachments referenced by raw files |

Nothing in this folder is edited after it lands. The agent reads from here and
writes to `wiki/`. It may add new files when it pulls something from a
connected service, but never changes or deletes an existing one. If a file is
wrong, add the corrected one next to it and re-ingest, so the source stays a
faithful record of what you saved.

Name files `YYYY-MM-DD-slug.md`, with the slug in lowercase ASCII. The slug
rules for Estonian and other letters are in `CLAUDE.md`. The page's real title
goes in its frontmatter, not the file name.

`workspace/` is git-ignored by default (see `.gitignore`). Cleaned transcripts
are written beside the original as `<name>-clean.md`; the original is never
overwritten.

Email, chat and meeting files contain other people's words. Keep them out of
any repository you push or share.
