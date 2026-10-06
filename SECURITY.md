# Security policy

## Reporting a vulnerability

Report it privately through GitHub's private vulnerability reporting. Open this
repository, choose the **Security** tab, click **Report a vulnerability**, and
fill in the form. Please do not report it in a public issue or pull request.
By default the form asks for a summary, details, a proof of concept and the
impact: say what you found, in which file, how to reproduce it, and what an
attacker gains.

This is GitHub's feature "Privately reporting a security vulnerability"; the
steps above are from its [documentation](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately),
read in the github/docs source on 6 October 2026. It works only where the
repository owner has enabled it: under Settings, Code security and analysis,
Advanced Security, Private vulnerability reporting, **Enable**
([Configuring private vulnerability reporting for a
repository](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository),
read the same way on the same date).

## What is in scope

This repository ships code and settings that run on a reader's machine, next to
their notes and credentials. In scope:

- The vault template's guard hook,
  [`vault-template/.claude/hooks/guard.py`](vault-template/.claude/hooks/guard.py),
  and the permission rules in
  [`vault-template/.claude/settings.json`](vault-template/.claude/settings.json):
  a way to make a blocked command, edit or secret get through, or a way for the
  hook to fail open where the README says it fails closed.
- The scripts that ship into a vault: `scripts/link_check.py`,
  `scripts/vault_stats.py`, `scripts/graph_export.py` and
  `scripts/chat_export_to_md.py` (path handling, unsafe parsing, writes outside
  the vault).
- The plugins: the `second-brain` plugin (`.claude-plugin/`, `skills/`,
  `commands/`, `agents/`) and `plugins/agents-course/`, including anything that
  makes an agent run commands or send data the page does not say it does.

Out of scope: the static site generators in `tools/` and the `build_*.py`
scripts (they only run in this repository), the correctness of guide content
(open an ordinary issue), and vulnerabilities in Claude Code, Obsidian or the
other tools the kit works with, which belong to those projects.

## The guard is a guardrail, not a sandbox

The guard hook and the deny rules reduce what an agent can do by mistake. They
are not a security boundary. The hook reads command text and file paths before
they run; it cannot see what a script file does when the agent runs it, and some
routes (other upload tools, one-liners its patterns miss, connectors whose tool
names do not match) are not covered. The vault template's README lists, rule by
rule, what is enforced and what stays prompt-only: see
[What is enforced and what is not](vault-template/README.md#what-is-enforced-and-what-is-not).
A report that a route listed there as unblocked is unblocked is a known
limitation, not a vulnerability; a bypass of something listed as enforced is.

If you need a hard boundary, run the agent in a container or a separate account
with no credentials, and keep the vault in a repository that has no remote.
