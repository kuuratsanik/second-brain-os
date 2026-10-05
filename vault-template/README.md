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
  .obsidian .claude/settings.json .claude/hooks
git commit -m "Initial vault"
claude
```

If you copied the Quickstart's setup, also add `.claude/skills .claude/commands
.claude/agents scripts` to that first commit, because the agent setup is worth
versioning. Always include `.claude/settings.json` and `.claude/hooks`: they
hold the boundaries described below. `raw/workspace/` stays ignored by `.gitignore`.

`.obsidian/` holds a small Obsidian preset, applied when you open the folder as
a vault. Attachments go to `raw/assets`. New notes go to `raw/inbox`, so notes
you create in Obsidian land there as source material the agent reads but never
edits; for a page the agent maintains, link it with a folder path, such as
`[[wiki/concepts/goals]]`. Links are wikilinks that update on rename.
`archive/`, `scripts/` and `.claude/` are excluded from search and the graph;
`output/` is not, so you can find the agent's drafts. The Templates folder is
`templates/`, and Daily notes writes `YYYY-MM-DD` files to `journal/`. The
graph colours pages by `domain:`, highlights hubs, and hides `raw/`, `archive/`
and `templates/`. Obsidian writes this folder; the agent has no reason to write
here, and nothing blocks it. `.gitignore` keeps `workspace*` and `cache` out of
git, so the preset is versioned and your window layout is not. Obsidian also
rewrites the view state in `graph.json` when you open the graph: commit that
diff or ignore it, but keep the file tracked. Change any setting in Obsidian.

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
| Never push, send, add a remote, hard-reset or amend | deny rules and hook | Push routes the hook does not know |
| Never delete (`rm`, `rmdir`, `unlink`, `git rm`, `find -delete`, `git clean`) | deny rules and hook | Deleting from inside a script the agent runs |
| Moves and copies stay in the vault and never clobber protected paths | hook (`mv`, `cp`, `git mv`, `install`, `ln`, PowerShell equivalents) | |
| Writing to connected services (a) | deny rules on MCP tool names | Connectors whose tool names do not match, and MCP file tools (Obsidian REST and similar) whose names the patterns miss |
| Sending vault content out (b) | deny rules and hook for curl, wget and PowerShell web uploads; ask for WebFetch, WebSearch, curl, wget | What goes into a search query or a read, and other upload routes: `scp`, `rsync` to a host, `ssh`, `nc`, `gh api` and `gh gist`, and Python, Node or other one-liners that open a socket |
| `raw/` is append-only | hook (new files allowed, existing files and folders cannot be changed, moved or renamed) | |
| `journal/`, `scripts/`, `.claude/` and `.gitignore` are yours | deny rules and hook | |
| `CLAUDE.md` only changes in Profile (e) | hook; ask rule | Schedule prompts, which live outside the vault |
| `raw/workspace/` never staged | hook (also blocks `git add -A`, `.`, the vault root, `raw`, `-f`, `commit -a`) | |
| Checkpoint, log, report, queue, run commit | | All of it; the Stop hook only warns about uncommitted paths |
| Secrets (d), merging people (f) | | All of it |

The permission rules cannot express "existing files only", so the `raw/` and
`CLAUDE.md` checks live in the hook. Both layers run: a call must pass the hook
and the permission rules. Deny rules and explicit ask rules apply in every
permission mode, including `bypassPermissions`; that mode approves everything
the rules leave unmatched without a prompt and disables Claude Code's other
safety checks, so do not run the vault in it. A hook blocks only by exiting with code 2: a hook that crashes, cannot
start or times out does not block, and the deny rules are then the only layer.
`guard.py` itself fails closed on bad input.
Neither layer is a sandbox. They read the command text, so a script that
deletes files itself is not seen; for that, turn on Claude Code's sandbox.
PowerShell coverage is partial: the hook knows the common cmdlets
(`Remove-Item`, `Move-Item`, `Rename-Item`, `Set-Content`, `Out-File`,
`Invoke-WebRequest` and friends), `cmd /c` and `-EncodedCommand`, but not every
way to write a file. The shell parser is also conservative about things it cannot
resolve: a path with a glob, a brace list or a variable that could reach a
protected folder is refused (so `git mv wiki/{a,b}.md archive/` is blocked: name
each file), and after a `cd` it cannot follow (`cd -`, `cd $DIR`, `popd`),
relative paths are refused until the command uses absolute paths. After a
`cd` it can follow, a relative path is checked against both the folder you
started in and the one you moved to, and refused if either lands on a protected
path, so use paths from the vault root or absolute paths.
`git -c` only accepts a short allowlist of harmless settings, `git config` only
reads (`get`, `list`, `--get`, `--list`, or one setting name), and `git -C` must stay inside the vault. `scripts/` is owner-maintained so the agent cannot write a
script and then run it under the `python3 scripts/*.py` allow rule.

**Connector names.** The MCP deny rules match tool names by pattern
(`mcp__*__*send*`, `mcp__*__*create*`, `mcp__*__*append*`, `mcp__*__*patch*`,
`mcp__*__*put*` and so on), because tool names differ by connector and server.
These patterns are a starting point. Check them against
the tool names your connectors expose (the `/mcp` command lists them), then add
the exact names you want blocked or remove a pattern that catches a read-only
tool. Patterns can also block reads whose names contain the word, such as a
tool called `get_updates` or `get_output`.

**Allowed without asking.** `python3 scripts/*.py` (and `python`, `py` for
Windows), `git add`, `commit`, `status`, `log`, `diff`, `show`, `revert`,
`rev-parse`, `check-ignore`, `git mv` and `mkdir`, so scheduled archive and
commit steps run. Archive with `git mv`: plain `mv` is not allowed, and git
refuses to move files out of the vault or over an existing page. `git restore`
and `git checkout` ask first, so a scheduled run cannot use them; rollback is
live-only anyway. `git revert --abort` is denied; use `git revert --quit`.

**Scheduled runs.** A headless run (`claude -p`) has nobody to answer a prompt,
so anything that would ask is refused. In the default permission mode that
includes every page write. Start scheduled runs with
`--permission-mode acceptEdits` (or set `permissions.defaultMode` to
`acceptEdits` in `.claude/settings.json`), or add `Edit(/wiki/**)`,
`Edit(/output/**)` and `Edit(/archive/**)` allow rules. Write them as `Edit`
rules: Claude Code never consults a path rule written for `Write`. In
`acceptEdits` mode Claude Code also auto-approves `rm`, `rmdir`, `sed`, `touch`,
`mkdir`, `mv` and `cp` for paths inside the vault, which is why the deny rules
and the hook matter in that mode: the hook is what stops a `mv` out of the vault
or a `sed -i` on a `raw/` file. The ask rules
(CLAUDE.md edits, web access, `git checkout`, `git restore`) are refused in a
scheduled run, which is what you want. See the
[permission modes](https://code.claude.com/docs/en/permission-modes) page.

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
