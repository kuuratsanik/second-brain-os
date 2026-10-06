# Skills and slash commands

Two mechanisms that look similar and do different jobs.

**A skill** teaches repeatable behaviour. It loads when relevant and shapes how
the agent does something, whether you invoked it explicitly or just described the
task.

**A command** is a shortcut for a task you run often. It points at a skill and
saves you typing the instructions.

The behaviour belongs in the skill. That way ingestion works the same whether it
was triggered by `/ingest`, by a scheduled task, or by you saying "add this to my
vault".

## What this repo ships

Twenty-nine skills in [`skills/`](../../skills/README.md), one per workflow in this
guide. Seventy-eight commands in [`commands/`](../../commands/README.md). Most are a
few lines pointing at a skill and setting its scope; a few (`/audit`,
`/dry-run`, `/index` and `/scope`) are self-contained and name no skill. The
scheduling command is `/maintenance-schedule`, which points at
`second-brain-schedule`. It is not called `/schedule` because that name would
shadow Claude Code's built-in `/schedule`, which creates, updates, lists and runs
[routines](https://code.claude.com/docs/en/routines) that execute in the cloud
([commands reference](https://code.claude.com/docs/en/commands)).

The ratio is deliberate. Behaviour belongs in a small number of well-written
skills; commands are cheap, so there is no reason to make you remember how to
phrase a request you make every week.

Install them inside the vault at `.claude/skills/` and `.claude/commands/` so
they are versioned alongside your notes and travel with the vault. Claude Code
has merged custom commands into skills: a file at `.claude/commands/x.md` and a
skill at `.claude/skills/x/SKILL.md` both create `/x`, and existing command files
keep working ([skills docs](https://code.claude.com/docs/en/skills)).

## Writing your own

A skill worth writing has three properties: you do it repeatedly, you have
opinions about how, and the opinions are not obvious enough for the model to
guess.

The `description` is what Claude matches your request against, and the skills
docs say the listing truncates it at 1,536 characters, so put the key use case
first. Anthropic's own
[skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
recommends "pushy" descriptions because Claude tends to undertrigger skills.

Structure that works:

```markdown
---
name: skill-name
description: >-
  What it does. When to use it, written pushy, because Claude tends to
  under-trigger skills. Do NOT use for the tempting near-misses.
---

# Name

[Why this skill exists: what failure it prevents. This paragraph is the rubric
for every case the rules below do not cover.]

## Core rule
## Workflow
## Output format
## Calibration
## Example
```

The opening paragraph does more work than the rules. Rules cover the cases you
thought of; the reason covers the rest.

## Explain the why

"Never overwrite a contradiction" gets applied literally and fails on the edge
cases. "Never overwrite a contradiction, because the history of what you believed
is the thing this vault has that a search engine does not" generalises to
situations you never described.

All-caps NEVER without a reason is usually a missing explanation.

## Versioning

Skills live in the vault, so git tracks them. When output quality changes, the
skill diff is the first place to look.

Test a skill on three or four real cases before letting a scheduled task use it.
A flaw in a skill that runs nightly is a flaw in three hundred pages by the end
of the year.

## Next

[Guardrails](safety-and-guardrails.md)
