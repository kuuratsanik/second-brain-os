# Claude Code in the vault

Claude Code is the half that reads and writes. Two ways to run it, and the
choice only affects where you type, not what happens.

## Option A: the desktop app

Download Claude Desktop from [claude.com/download](https://claude.com/download)
and sign in. The app has a **Code** tab, which is Claude Code without a
terminal. If you have never used a command line, start here.

## Option B: the terminal

Install Claude Code and run `claude` from inside the vault folder:

```bash
cd ~/brain
claude
```

Started this way, the agent reads and writes the vault directly through the
filesystem, with no plugin and no MCP server involved. This is the simplest
possible setup and it is enough for everything in the ingestion, structuring
and retrieval sections of this guide.

Installation instructions for each platform are in the [official setup
docs](https://code.claude.com/docs/en/setup).

## Option C: inside Obsidian

Community plugins now embed the agent in the editor, and they are heavily used.
[Claudian](https://github.com/yishentu/claudian) and
[Copilot](https://github.com/logancyang/obsidian-copilot) each have more than two
million installs in Obsidian's
[community-plugin-stats.json](https://github.com/obsidianmd/obsidian-releases/blob/master/community-plugin-stats.json)
(about 2.3 million each in October 2026). Both can run Claude Code and Codex in a
pane next to your notes. The README of each lists the other agents it supports.

Worth knowing about because it removes the window switching entirely. Worth
being careful with for the same reason this guide keeps ingestion on a
schedule: an agent in the editor invites ad-hoc edits that never make it into
`log.md`, and an unlogged vault is one you cannot audit.

A reasonable split is the plugin for conversation and drafting, the terminal or
a scheduled task for anything that writes wiki pages.

## Python 3 for the guard hook

The vault template's safety rails include a hook, `.claude/hooks/guard.py`,
that Claude Code starts with `python3`. A hook that cannot start blocks
nothing, so Python 3 is a prerequisite, not an option. Check that
`python3 --version` prints a version. On a Mac, `/usr/bin/python3` is one of Apple's developer-tool shims
([TN2339](https://developer.apple.com/library/archive/technotes/tn2339/_index.html)); if `python3 --version` asks to install the Command Line Tools instead of printing a version, accept, or install Python from [python.org](https://www.python.org/downloads/). After copying the
template into the vault (see the [Quickstart](../../README.md#quickstart)), run:

```bash
cd ~/brain
python3 .claude/hooks/test_guard.py
```

It should end with "N/N passed". Do not rely on the rails until it does.

## Windows

The Quickstart commands are bash. Run them in Git Bash, which comes with [Git
for Windows](https://git-scm.com/download/win), and they work unchanged. In
PowerShell, `mkdir -p`, `cp -r`, the `rm` glob and `\` line continuations fail;
the [Quickstart](../../README.md#windows) has PowerShell equivalents. On Windows
`python3` is often the Microsoft Store stub: use `python` or `py` for the check
above, and change `python3` to `python` or `py` in the three hook entries of
`.claude/settings.json`, as the [template README](../../vault-template/README.md#what-is-enforced-and-what-is-not)
describes.

## Plan requirement

Claude Code needs a paid account: Pro, Max, Team, Enterprise, or a Console
account billed per token. The free Claude.ai plan does not include Claude Code
access, per Anthropic's own setup documentation. If the Code tab prompts you to
upgrade, that is why.

## Filesystem or MCP

Both work. The difference is narrow and worth knowing before you pick:

| | Filesystem | MCP |
|---|---|---|
| Setup | none, just `cd` into the vault | plugin plus a config command |
| Obsidian open | not required | required, the plugin serves the API |
| Scope | whatever folder you started in | the whole vault, from anywhere |
| Failure mode | none to speak of | plugin off, app closed, wrong port |

Start on the filesystem. Move to [MCP](mcp-obsidian.md) when you want the agent
to reach the vault from sessions that are not running inside it, which mostly
matters once you add scheduled tasks.

## First run

Point it at the structure before asking for anything else:

```
Read CLAUDE.md and wiki/index.md, then tell me what this vault currently
contains and what is missing.
```

The answer tells you immediately whether the agent understood its instructions.
If it starts inventing a structure you did not ask for, your `CLAUDE.md` is too
vague. See [writing your CLAUDE.md](claude-md.md).

## Permissions

The agent will ask before editing files. Grant it write access to the vault and
nothing else. Do not grant blanket shell access on a folder that holds anything
you cannot lose, and read [guardrails](../06-agents/safety-and-guardrails.md)
before you automate anything on a schedule.

## Next

[MCP for Obsidian](mcp-obsidian.md)
