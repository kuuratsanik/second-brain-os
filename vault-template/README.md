# vault-template

An opinionated starter vault, tuned for an agent that works without asking
first, for several life and work domains (work, learning, personal, creative,
self-improvement, systems), and for notes in more than one language. Anyone can
use it: it ships with no personal facts, and the interview fills in the
profile. Copy this folder somewhere on your machine, open it in Obsidian as a
vault, and start Claude Code inside it.

```bash
cp -r vault-template ~/brain
cd ~/brain
git init
git add .gitignore CLAUDE.md README.md templates wiki projects output journal archive raw \
  .claude/settings.json .claude/hooks
git commit -m "Initial vault"
claude
```

If you copied the Quickstart's setup, also add `.claude/skills .claude/commands
.claude/agents scripts` to that first commit, because the agent setup is worth
versioning. Always include `.claude/settings.json` and `.claude/hooks`: they
hold the boundaries described below. `raw/workspace/` stays ignored by `.gitignore`.

Do the git step once. The agent's safety rails (a checkpoint commit before any
destructive step, one commit per run) need the vault folder to be its own git
repository. If the vault sits inside another repository, the agent will not
create one and will queue the problem for you instead.

`CLAUDE.md` is the instruction sheet the agent reads every session. Read it
before your first run. Its Profile block is empty on purpose: fill it with the
interview from [the CLAUDE.md guide](https://github.com/kuuratsanik/second-brain-os/blob/main/docs/02-setup/claude-md.md), in a live
session, before you rely on the agent. The rules are strict about linking and
about never overwriting a contradiction, because those two are what separate a
vault that compounds from a folder of summaries.

Read the Autonomy section before you schedule anything. It lets the agent
ingest, merge and archive on its own, and limits that with rails: a checkpoint
before destructive steps, archive instead of delete, a change log in
`wiki/log.md`, and hard stops for writing to connected services, sending
personal data out, secrets and irreversible steps.

## What is enforced and what is not

Rules in `CLAUDE.md` are instructions the agent usually follows. They are not a
boundary. Claude Code's own documentation says a `CLAUDE.md` entry "shapes what
Claude tries but doesn't enforce a boundary". Two files add real ones, and both
are copied with the template into `.claude/`:

- `.claude/settings.json`: permission rules (deny, ask, allow) and hook
  registration.
- `.claude/hooks/guard.py`: a PreToolUse hook (Python standard library only)
  that reads each file edit and shell command before it runs and exits 2 to
  block it. `test_guard.py` beside it feeds the hook sample calls; run
  `python3 .claude/hooks/test_guard.py` after you change either file.

| Hard stop or rail | Enforced by | Still prompt-only |
|---|---|---|
| Never push, add a remote, or hard-reset | deny rules and hook | |
| Never delete (`rm`, `rmdir`, `unlink`, `git rm`, `find -delete`, `git clean`) | deny rules and hook | Deleting from inside a script the agent runs |
| Writing to connected services (a) | deny rules on MCP tool names | Connectors whose tool names do not match; non-MCP routes |
| Sending vault content out (b) | deny rules and hook for curl/wget uploads; ask for WebFetch, WebSearch, curl, wget | What goes into a search query or a read |
| `raw/` is append-only | hook (new files allowed, existing files blocked) | |
| `journal/` is yours | deny rule and hook | |
| `CLAUDE.md` only changes in Profile (e) | hook; ask rule | Schedule prompts, which live outside the vault |
| `raw/workspace/` never staged | hook (also blocks `git add -A`, `.`, `-f`, `commit -a`) | |
| Checkpoint, log, report, queue, run commit | | All of it; the Stop hook only warns about uncommitted paths |
| Secrets (d), merging people (f) | | All of it |

The permission rules cannot express "existing files only", so the `raw/` and
`CLAUDE.md` checks live in the hook. Both layers run: a command must pass the
hook and the permission rules. Do not run the vault in `bypassPermissions` mode,
which skips the permission prompts, including the ask rules.
Neither layer is a sandbox. They read the command text, so a script that
deletes files itself is not seen; for that, turn on Claude Code's sandbox.

**Connector names.** The MCP deny rules match tool names by pattern
(`mcp__*__*send*`, `mcp__*__*create*` and so on), because tool names differ by
connector and server. These patterns are a starting point. Check them against
the tool names your connectors expose (the `/mcp` command lists them), then add
the exact names you want blocked or remove a pattern that catches a read-only
tool. Patterns can also block reads whose names contain the word, such as a
tool called `get_updates`.

**Adjusting.** Edit `.claude/settings.json` yourself. A deny rule beats an ask
rule, and an ask rule beats an allow rule, at every settings level, so to let
the agent do something denied, delete the deny entry; adding an allow entry
elsewhere does not override it. Use `.claude/settings.local.json` for
changes that should stay on your machine. If the hook blocks something you
want, edit `guard.py`; the agent cannot, because writes under `.claude/` are
blocked. Run `test_guard.py` afterwards.

**Windows.** The hook command is `python3`. If that name opens the Microsoft
Store stub on your machine, change `python3` to `python` or `py` in the three
hook entries of `settings.json`. A hook that fails to start does not block
anything, so check once that a blocked call, such as `rm x`, is refused.

**Sources.** Field names and rule syntax were checked against the current
Claude Code documentation: [permissions](https://code.claude.com/docs/en/permissions),
[hooks](https://code.claude.com/docs/en/hooks) and
[settings](https://code.claude.com/docs/en/settings). The exit-2 and
`systemMessage` behaviour is from the hooks page; rule evaluation order, the
`Edit(path)` syntax and `mcp__server__tool` patterns are from the permissions
page.

`.gitignore` keeps `raw/workspace/` (email, chat, docs, calendar) and editor
state out of git. Your journal and meeting transcripts are versioned unless you
uncomment their lines. Never push this vault to a remote without checking what
is in it.

```
raw/        what arrives, by source: clippings, youtube, meetings, workspace, ai-chats, inbox
wiki/       the agent's pages: sources, entities, concepts, synthesis, hubs,
            self-improvement (ideas, experiments, reviews), systems
journal/    your own entries, read-only for the agent
projects/   one folder per project, each with its own CLAUDE.md
output/     generated drafts and reports
archive/    retired pages, never deleted
templates/  page templates
```

Delete the domains you do not need, and edit `wiki/systems/routing.md` if your
sources differ.
