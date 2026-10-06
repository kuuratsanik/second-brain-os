# Security policy

## Reporting a vulnerability

Report it privately through GitHub: open this repository's **Security** tab and
choose **Report a vulnerability**. Please do not open a public issue or pull
request for it. Include what you found, the file, how to reproduce it, and what
an attacker gains.

GitHub's documentation describes the feature as "privately reporting a security
vulnerability". Not re-checked on 6 October 2026 because the page on
docs.github.com could not be fetched, so check [GitHub's
documentation](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
for the current steps.

The button appears only if the repository owner has enabled private
vulnerability reporting in the repository settings. If you cannot see it, the
owner has not yet done so; open a public issue that says only "I have a
security report" with no details, and wait for contact. The setting is described
in GitHub's documentation on configuring private vulnerability reporting for a
repository (not re-checked on 6 October 2026 for the same reason).

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
