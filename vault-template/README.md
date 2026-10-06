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
versioning. If you install the kit as the `second-brain` plugin instead, there is nothing of
it to add here: it lives outside the vault (see
[plugins](https://github.com/kuuratsanik/second-brain-os/blob/main/plugins/README.md#second-brain)).
Always include `.claude/settings.json` and `.claude/hooks`: they
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
and `templates/`. Obsidian writes this folder; the hook blocks the agent from writing
here; `git add .obsidian/graph.json` and committing it still work. `.gitignore` keeps `workspace*` and `cache` out of
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
- `.claude/hooks/guard.py`: a PreToolUse hook (Python 3.9 or newer, standard library only)
  that reads each file edit and shell command before it runs and exits 2 to
  block it. It also checks `sensitivity: restricted` pages (below), writes the
  audit log, and has a Stop mode that warns about uncommitted paths.
  `test_guard.py` beside it feeds the hook sample calls and the regression
  corpus `guard_corpus.json`; run `python3 .claude/hooks/test_guard.py` after
  you change either file.
- `.claude/hooks/integrity.py`: a SessionStart hook (Python 3.9 or newer) that warns
  when `settings.json`, `guard.py` or `CLAUDE.md` differ from the last commit.

| Hard stop or rail | Enforced by | Still prompt-only |
|---|---|---|
| Never push, send, add a remote, hard-reset or amend | deny rules and hook | Push routes the hook does not know |
| Never delete (`rm`, `rmdir`, `unlink`, `shred`, `trash-put`, `gio trash`, `git rm`, `find -delete` and `-exec`, `git clean`, `zip -m`, `tar --remove-files`, .NET `File.Delete`) | deny rules and hook; the hook also pattern-matches one-liners (`python3 -c`, `node -e`, `perl -e`, `ruby -e`, `php -r`, `deno eval`) that call a delete function, and sees through `busybox`, `coreutils`, `Start-Process`, backslashes (`r\m`), `$'...'` quoting and five levels of `sh -c` | Deleting from inside a script file the agent runs, one-liners the patterns miss, and names built at run time (`eval "$x"`, base64) |
| Work stays recoverable (c): no history rewrites or silent discards | hook: `git stash` (except `list` and `show`), `branch -d/-D/-m/-M/-f`, `tag -d/-f`, `reset` to another commit or with `--keep/--soft/--mixed` and a target, `switch -f`, `checkout -- <path>` and `restore <path>` without a named commit (`restore --staged` alone is allowed), `update-index --remove`, `worktree remove/prune`, `reflog expire/delete`, `update-ref -d`, `gc --prune`, `prune`, `notes remove`, `submodule deinit`, `replace`, `--exec-path` | `git apply` and `git am` (they change files from a diff), `git add -i`, restoring from a named commit (the rollback route) |
| Moves and copies stay in the vault and never clobber protected paths | hook (`mv`, `cp`, `git mv`, `install`, `ln`, PowerShell equivalents). `env -C`, `env --chdir`, `sudo -D`, `patch -d` and `Start-Process -WorkingDirectory` are refused outright, because they change what every later path means | |
| Writing to connected services (a) | deny rules on MCP tool names | Connectors whose tool names do not match, and MCP file tools (Obsidian REST and similar) whose names the patterns miss |
| Sending vault content out (a, b) | deny rules and hook for curl, wget and PowerShell web uploads; ask for WebFetch, WebSearch, curl, wget. The hook also refuses `nc`, `ncat`, `netcat` and `socat` outright, `scp`, `sftp` and `rsync` with a remote spec (`host:path`, `user@host:`, `scp://`, `rsync://`), and `ssh` with a file or a pipe as input | What goes into a search query or a read, and other upload routes: `gh api` and `gh gist`, `aws`, `rclone`, `ssh host 'command'` with the data inside the command, and Python, Node or other one-liners that open a socket |
| `raw/` is append-only | hook (new files allowed, existing files and folders cannot be changed, moved or renamed) | |
| `journal/`, `scripts/`, `.claude/`, `.obsidian/` (Obsidian's settings) and `.gitignore` are yours | deny rules and hook: file tools, redirects, `tee`, `sed -i`, `cp`, `mv`, `truncate`, `dd`, `patch`, `sort -o`, `gawk -i inplace`, `vim`/`ed`, `chmod`/`chown`/`chattr`/`setfacl`/`attrib`/`icacls`, `touch`, `mkdir`, and one-liners in python, node, perl, ruby and php (including `truncate`) | Anything a script file the agent runs does |
| `CLAUDE.md` only changes in Profile (e) | hook; ask rule | Schedule prompts, which live outside the vault |
| `raw/workspace/` never staged | hook (also blocks `git add -A`, `.`, the vault root, `raw`, `-f`, `commit -a`) | |
| Checkpoint before archive (rail 1) | hook: `git mv`, `mv` and `Move-Item` into `archive/` are blocked while the source has uncommitted changes, and when git cannot say (no repository, no commit, git missing) | Checkpoints before other operations (merge, rename, split) |
| Log, report, queue, run commit | | All of it; the Stop hook only warns about uncommitted paths |
| Secrets (d) | hook: Write, Edit and MultiEdit content, and shell commands that write (redirects, heredocs, `tee`, `git commit -m`, `sed -i`, `perl -i`, `python3 -c`, `node -e`, `ruby -e`, `php -r`), are blocked when they contain a GitHub, AWS, Anthropic, OpenAI-style, Slack or Stripe live key or a private key block; the message names the kind, not the value | Other credential formats, passwords, account numbers, secrets that arrive through a script or a connector, and anything already in a file |
| `sensitivity: restricted` pages stay in the vault | hook: a verbatim run of 200 or more characters from a restricted page is blocked in text headed for `output/`, a path outside the vault, WebFetch, WebSearch or an MCP tool; so is a shell command that names a restricted page (or a glob or folder holding one) and writes to `output/` or outside the vault, or runs a sending tool. The exact list is under "Restricted pages" | `private` pages; unlabelled pages; paraphrase, translation, homoglyphs, base64 and other encodings; short or split quotes; copying into another wiki page; paths built at run time; scripts the agent runs |
| The agent cannot edit its own audit log | hook (any write, move or delete of `.claude/guard.log`, `guard.log.1` or the cache); deny rules `Edit(/.claude/**)`, `Edit(/.claude/guard.log*)`, `rm` and friends | A script file that opens the log itself; you, in your own terminal |
| Tampering with the guard is noticed | `integrity.py` at session start: warns when `settings.json`, `guard.py` or `CLAUDE.md` differ from, or are missing from, the last commit | A tamper that was committed; changes mid-session; a `settings.json` edited to drop the hook |
| Merging people (f) | | All of it |

The permission rules cannot express "existing files only", so the `raw/` and
`CLAUDE.md` checks live in the hook. Both layers run: a call must pass the hook
and the permission rules. Deny rules and explicit ask rules apply in every
permission mode, including `bypassPermissions`; that mode approves everything
the rules leave unmatched without a prompt and disables Claude Code's other
safety checks, so do not run the vault in it. A hook blocks only by exiting with code 2: a hook that crashes, cannot
start or times out does not block, and the deny rules are then the only layer.
`guard.py` itself fails closed on bad input.

**Secret patterns.** The check looks for known key shapes with realistic lengths: `ghp_`, `gho_`, `ghu_`, `ghs_` and `ghr_` tokens, `github_pat_`, `AKIA` and `ASIA` key ids, `sk-ant-`, `sk-` followed by 20 or more letters or digits (and `sk-proj-` style keys), PEM private key blocks, `xox[baprs]-` tokens, Slack webhook URLs and Stripe live keys. A page that only mentions a prefix ("`ghp_` tokens") or holds a short value passes, and so does a match that holds a placeholder word (`fake`, `demo`, `example`, `placeholder`, `redacted`, `dummy`, `sample`, `your`) set off by `-`, `_` or the ends of the string, the all-caps `EXAMPLE`, `REDACTED` or `PLACEHOLDER` anywhere in it (so `AKIAIOSFODNN7EXAMPLE` is fine), or a run of four `x`, four `0`, three `*` or three `.`. To add a format, change a length or switch the check off, edit `SECRET_PATTERNS`, `SECRET_PLACEHOLDER` or `SECRET_CHECK` near the top of `.claude/hooks/guard.py`, then run `test_guard.py`.

**Restricted pages.** The privacy skill says a `sensitivity: restricted` page never leaves the vault or lands in a report. The hook enforces the part it can see:

- *Text.* A Write, Edit, MultiEdit or NotebookEdit whose target is under `output/` or outside the vault is blocked when its new text shares a run of 200 or more characters with a restricted page (the pieces of one MultiEdit are also tried joined). The same test runs on the input of WebFetch, WebSearch and every MCP tool, and on the text of a shell command that writes to `output/` or outside the vault or runs a sending tool. Before comparing, both sides get Unicode NFKC (so full-width letters fold to plain ones), lose zero-width characters and soft hyphens, are lower-cased, and every run of spaces and punctuation becomes one space, so bold, quotes, line wraps, bullets and invisible characters do not hide a copy. Web inputs are also tried with percent-encoding undone.
- *Paths.* A shell command is blocked when it names a restricted page and also writes to `output/` or outside the vault, or runs a sending tool. What counts, exactly:
  - *A restricted page is named* by its path (relative to the folder the command is in, absolute, or its vault-relative text anywhere in the command, including inside `bash -c`, a variable assignment or a heredoc), by a glob that matches one (`*`, `?`, `[...]`, `{a,b}`, and `$VAR` read as `*`), or, for `cp`, `mv`, `rsync`, `tar`, `zip`, `rar`, `7z`, `cpio`, `pax`, `Compress-Archive`, `grep`, `rg`, `ag` and `ack`, by a folder that holds one. `git archive` and `git bundle` with an export destination or a sending tool count as naming every restricted page.
  - *A write to `output/` or outside the vault* is a redirect (`>`, `>>`, `2>`), `tee`, `cp`, `copy`, `install`, `ln`, `rsync`, `mv`, `git mv`, `Move-Item`, `Rename-Item`, `dd of=`, PowerShell `Set-Content`, `Add-Content`, `Out-File` and `New-Item` (and their aliases), `zip`, `rar a`, `7z a`, `tar` creating or appending (`-f`, old-style `czf`, `--file`), `Compress-Archive -DestinationPath`, `pandoc -o`, `git archive -o`, `git archive` with a redirect, or `git bundle create`.
  - *A sending tool* is `curl`, `wget`, `scp`, `sftp`, `ssh`, `rsync`, `nc`, `ncat`, `netcat`, `socat`, `gh`, `aws`, `gsutil`, `gcloud`, `rclone`, `mail`, `mailx`, `mutt`, `sendmail`, `Send-MailMessage` or a PowerShell web cmdlet.
  - *Not blocked:* reading a restricted page, `git add` and `git commit` of one, copies inside `wiki/`, and listing a folder into `output/` (`ls`, `find` print names, not content).
- *Cost.* The hook keeps `.claude/guard-cache.json` (page path, mtime, size and sampled hashes, never text) and re-reads only pages that changed. On a 3,000-page vault with 30 restricted pages, a call that needs the check costs about 12 ms more than one that does not (a 20 KB text about 25 ms, a 100 KB text about 75 ms, the first call after a fresh checkout about 65 ms). Calls that never write to an export path pay nothing beyond Python start-up, but note that start-up now happens on every WebFetch, WebSearch and MCP tool call too, about 45 ms on the machine measured. `python3 .claude/hooks/test_guard.py --bench` measures it on yours.
- *Limits.* Only the label `restricted` counts: `private` pages, unlabelled pages and a label the agent forgot to set are not checked. Any 200-character run from a restricted page counts, including public text quoted on it, so quoting that paragraph in `output/` is blocked too. A 199-character quote, a paraphrase, a translation, homoglyphs (look-alike letters from another script), base64, rot13 and other encodings pass, and each call is judged alone, so a page copied in short pieces over several calls passes. Copying a restricted page into another `wiki/` page, reading it into the conversation, and anything a script the agent runs does are still prompt-only. A path built at run time, or reached through `xargs`, is not seen. Keep a page that must never leave the machine out of any synced or backed-up folder.

**Audit log.** Every blocked call appends one line to `.claude/guard.log`: `{"ts": "2026-10-06T08:15:00Z", "tool": "Write", "rule": "raw-append-only", "target": "raw/clippings/a.md"}`. `rule` is a short name (`delete`, `secret`, `restricted-excerpt`, `audit-log` and so on), and `target` is the vault-relative path for a file tool, the restricted page for a restricted-page block, otherwise the tool name. The log never holds a command, a secret value or an excerpt. At about 1 MB it moves to `guard.log.1`, replacing the older one. The file is git-ignored. **Read it in your weekly review**: `tail -n 50 .claude/guard.log`, or search it for `restricted-` and `secret` first. A rule that fires often is either a habit to fix in a skill or a rule to change. The guard refuses writes, moves and deletes of the log, its rotation and the cache, and `settings.json` denies `Edit` on them, so the agent cannot erase its own trail; you can, in your own terminal. A script file the agent runs could still open the log itself (the same limit as every script), and a hook that fails to start writes nothing.

**Tamper check.** `.claude/hooks/integrity.py` runs when a session starts, resumes, clears, compacts or forks (a `SessionStart` hook with no matcher). It compares the SHA-256 of `.claude/settings.json`, `.claude/hooks/guard.py` and `CLAUDE.md` with the versions in the last commit (`git show HEAD:path`, line endings ignored) and prints a warning when one differs, is missing, or is not tracked, or when git cannot answer (no repository, no commit, git missing). Per the [hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-10-06), a `SessionStart` hook's plain-text stdout is added to Claude's context, exit 0 is success, and the event cannot block, so the script always exits 0 and prints nothing when all three files match. It is a warning, not a lock: a tamper that was then committed passes, so commit your own changes to these files deliberately; a Profile edit to `CLAUDE.md` shows up until it is committed; the check does not run mid-session; and a `settings.json` edited to drop the hook, or a changed `integrity.py`, cannot report itself. If you see the warning and did not make the change, run `git diff HEAD -- <file>`.

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
`mcp__*__*put*` and so on; the verbs `label`, `unlabel`, `apply`, `modify`, `archive`, `mark` and `star` are
matched only at the start of a tool name, so `list_labels` and `get_draft` stay readable), because tool names differ by connector and server.
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
Store stub on your machine, change `python3` to `python` or `py` in every hook
entry of `settings.json` (five: SessionStart, three PreToolUse, Stop). A hook that
fails to start does not block anything, so check once that a blocked call, such
as `rm x`, is refused, and that `.claude/guard.log` gained a line.

**Sources.** Field names and rule syntax were checked against the current
Claude Code documentation: [permissions](https://code.claude.com/docs/en/permissions),
[hooks](https://code.claude.com/docs/en/hooks) and
[settings](https://code.claude.com/docs/en/settings). The exit-2 and
`systemMessage` behaviour, and the SessionStart event (stdout as context, exit codes, no
blocking), are from the hooks page, read 2026-10-06; rule evaluation order, the
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
