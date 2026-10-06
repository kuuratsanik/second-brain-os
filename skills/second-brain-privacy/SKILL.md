---
name: second-brain-privacy
description: >-
  Audit the vault for material that should not be in it: credentials, other
  people's private information, confidential work, and anything the user would
  not want synced or backed up, and check that each page's `sensitivity:` label
  matches what it holds. Use this skill when the user asks about privacy,
  is about to share or sync the vault, has just imported chat history or meeting
  notes, or asks what is sensitive in their notes. Do NOT use to delete anything
  on your own, or as a substitute for the publishing check.
---

# Audit privacy

The vault is synced, committed, backed up and sometimes shared. Every copy is
another place the content exists.

## Core rule

Find and report. Delete nothing without an explicit instruction naming what to
remove.

## Workflow

1. **Scan for credentials:** API keys, tokens, passwords, connection strings.
   Check `.obsidian/plugins/` too, where plugin data lives.
2. **Find other people's information:** meeting transcripts, personal messages,
   anything told in confidence, health or financial detail about someone else.
3. **Find confidential work:** material under NDA or employer restriction.
4. **Check the git remote.** Private material in a public repo is the most
   expensive version of this problem.
5. **Check `sensitivity:` labels** (below): pages that hold sensitive material
   but are labelled `normal`, and labelled pages that are in the wrong place.
6. **Report by severity,** with the specific file and why.

## Sensitivity labels

Each page carries `sensitivity: normal | private | restricted` in its
frontmatter, as the vault `CLAUDE.md` defines it. A missing field means
`normal`. Treat the label as an instruction about what may leave the page:

| Value | Holds | What it blocks |
|---|---|---|
| `normal` | Ordinary notes and sources | Nothing beyond the general rails |
| `private` | Health, finance, relationships, journal-derived material, other people's information | Its content in any web search, API call or connected-service request. `publish: true` and `/publish`, `/export` and any output meant to be shared. Quoting it on a `normal` page |
| `restricted` | Anything that would hurt someone if it leaked | Everything `private` blocks, and more: no content in reports, review pages or scheduled-run summaries (name the page, not what it says), no copying into other pages beyond a link and a neutral one-line pointer, and no excerpts in a chat reply unless the owner asks for that page |

Rules for applying it:

- Raising a label is mechanical: do it, log it, report it. Lowering one is the
  owner's decision; never lower a label yourself. A page you cannot place gets
  the higher level.
- A page that quotes or summarises a `private` or `restricted` page takes at
  least that page's level. Check pages that link to one.
- A page with `maintained_by: human` keeps its wording; change only the
  frontmatter label, and report it.
- In a report, name the file and the label, never the content.
- Labels are advice to you and to the skills, not a lock. A label stops nothing
  the vault's guard hook does not already block, so a page that must never
  leave the machine also belongs out of any synced or backed-up folder.

## Output format

```
Critical: <credentials, must be removed and rotated>
High: <other people's private information>
Review: <material the user should decide about>
Labels: <n pages under-labelled, raised> | <n pages with a label problem left for the owner>
Repo visibility: <public | private> - <verdict>
```

## Calibration

Never quote the credential itself in the report. Name the file and the type.

Redaction after ingest is unreliable, because material has already propagated
into concept pages and links. When something should not be there, say what else
would need removing with it.
