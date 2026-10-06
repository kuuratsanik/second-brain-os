# plugins

Claude Code plugins from this repo. It is a plugin marketplace: add it once,
install what you need.

```bash
claude plugin marketplace add kuuratsanik/second-brain-os
claude plugin install second-brain@second-brain-os     # the vault kit
claude plugin install agents-course@second-brain-os    # the course tools
```

| Plugin | What it is | Source |
|---|---|---|
| [`second-brain`](#second-brain) | The vault kit: 24 skills, 72 slash commands, 6 agents and the vault scripts | The repo root: [`skills/`](../skills/README.md), [`commands/`](../commands/README.md), [`agents/`](../agents/README.md), [`scripts/`](../scripts/README.md) |
| [`agents-course`](#agents-course) | One tool per course module, in your own repo | `plugins/agents-course/` |

## second-brain

The same skills, commands and agents the Quickstart copies into a vault, as a
plugin. There is one copy of each file in this repo: the plugin manifest
[`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) sits at the
repository root next to `marketplace.json`, and the marketplace entry's source
is `./`. Claude Code accepts a plugin at the marketplace root
([marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources):
a relative source resolves from the marketplace root, and `"."` on its own
means the root).

What the plugin does not carry: the vault template (`CLAUDE.md`, the permission
rules and the guard hook). Plugin agents cannot ship hooks or permission modes,
and those files belong to the vault, so you still copy `vault-template/` as the
[Quickstart](../README.md#quickstart) says. The plugin replaces only the
copies of `skills/`, `commands/` and `agents/`.

### Names

Claude Code puts every plugin component under the plugin's name
([plugins reference](https://code.claude.com/docs/en/plugins-reference): an agent `reviewer` in plugin `deploy-tools` appears as `deploy-tools:reviewer`; plugin skills are `/plugin-name:skill-name` on the [skills page](https://code.claude.com/docs/en/skills)).
I checked this by installing the plugin from a local copy of this repo with Claude Code 2.1.290 and reading the component names in the session's init event, with no model call:

| Component | Copied into `.claude/` | As the plugin |
|---|---|---|
| Command | `/ingest` | `/second-brain:ingest` |
| Skill | `second-brain-ingest` | `/second-brain:second-brain-ingest` |
| Agent | `curator` | `second-brain:curator` |

Skills still trigger from their descriptions, so you rarely type the long
name. Commands are the part you type, and they now carry the prefix. A command
with `disable-model-invocation: true` keeps it: the field is part of the file,
not of the name. The sixteen commands that a scheduled task can fire should be
the same sixteen, as `/second-brain:ingest`, `/second-brain:lint` and so on.
That is inferred from the skills documentation, not stated in the scheduled-tasks
documentation, so check the first run of a task before relying on it. The
vault template's autonomy override names commands, skills and agents by their
short names, and its text says the `second-brain:` prefix is covered too. A
file under `.claude/commands/` in your vault would still run as `/ingest`; a
plugin command never does.

`claude plugin details second-brain@second-brain-os` lists the 24 skills but shows
0 agents and no commands. It reads only the default directories, and the manifest
lists files, so it undercounts. The components still load, because the manifest
accepts file paths for `commands` and `agents`
([manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference#path-rules)).

### Scripts

Skills and commands run `scripts/vault_stats.py`, `link_check.py`,
`graph_export.py` and `chat_export_to_md.py` from the vault root. A plugin
install does not create `scripts/` in the vault, so those skills say to use
`${CLAUDE_PLUGIN_ROOT}/scripts/` when the vault has none. Claude Code fills in
that variable in skill, command and agent text for plugin components
([manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference#where-each-variable-resolves)).
In a vault that has the folder, the vault's own copy is used.

Copy the four scripts into the vault anyway if you want `/second-brain:metrics`,
`/second-brain:health` or `/second-brain:graph` to run without a prompt, or
from a scheduled task:

```bash
mkdir -p ~/brain/scripts
cp second-brain-os/scripts/{chat_export_to_md,graph_export,link_check,vault_stats}.py ~/brain/scripts/
```

The template's allow rules are `python3 scripts/*.py` and its variants. A call
to the plugin's copy is a different path, which no allow rule matches, so Claude
Code asks first, and a scheduled run has nobody to ask.

### Which install to use

| | Copy into the vault (Quickstart) | Plugin |
|---|---|---|
| Install | `cp -r` of `skills/`, `commands/`, `agents/`, plus the four vault scripts from `scripts/` | `claude plugin install second-brain@second-brain-os`, plus the template copy |
| Names | `/ingest`, `curator` | `/second-brain:ingest`, `second-brain:curator` |
| Where the files live | In the vault, versioned with your notes | In `~/.claude/plugins/`, outside the vault |
| Edit a skill for this vault | Edit the file | Not durable: an update replaces the plugin's copy. Copy the skill into `.claude/skills/` under another name, or use the Quickstart |
| Update | `/install` compares versions and lists the copy commands, which the owner runs because the guard hook blocks the agent from writing `.claude/` | `claude plugin update second-brain@second-brain-os`, then `/reload-plugins` or a new session |
| Scripts | In the vault | Copy them in (above), or accept a prompt per run |
| Several vaults | One copy each | One install, shared by every vault |

Use the copy install if you edit the kit, want a vault to be self-contained, or
run scheduled jobs. Use the plugin if you keep several vaults, want updates
without copy commands, or do not want the kit files in the vault's git history.

Do not use both in one vault. Both load, because plugin skills are namespaced
and so never replace a skill of the same name
([skills page](https://code.claude.com/docs/en/skills)): each skill, command and
agent appears twice, once under each name. That doubles the skill descriptions
in every session's context and leaves Claude two near-identical skills to pick
from.
The two copies also update on different schedules. To switch, delete the other
install first (`.claude/skills/second-brain-*`, `.claude/commands/`,
`.claude/agents/`, or `claude plugin uninstall second-brain@second-brain-os`),
then install the one you want. The `second-brain-doctor` skill warns when it
finds both.

The guard hook and permission rules live in the vault's `.claude/settings.json`
and apply whichever way the kit arrived. They fire on every tool call from any
skill, command or agent, plugin or not. The plugin carries no hooks of its own,
so there is nothing to conflict with the template's. Installing the kit as a
plugin does not bypass the guard. In a test, the guard allowed a call to the
plugin's copy of `vault_stats.py`, which is a read.

### Versions

`plugin.json` carries the version from [`skills/VERSION`](../skills/VERSION),
which is the kit version, so the plugin and the kit always carry the same number. Claude Code takes a
manifest `version` over the commit SHA
([loading reference](https://code.claude.com/docs/en/plugins/loading#how-claude-code-computes-the-version)),
so `claude plugin update` finds nothing new until the version is bumped. Bump
`skills/VERSION` and `plugin.json` together; `tools/check_kit.py` fails when
they differ.

### What the install copies

For a marketplace added from GitHub, Claude Code copies the whole plugin
directory into its cache, and here that is the entire repository (about 4 MB:
the guide, the site and the tests as well). Only `skills/`, `commands/` and
`agents/` are loaded from it. `plugin.json` lists every command and agent file
because a plugin loads every `.md` file in a listed folder, and `commands/README.md`
and `agents/README.md` would otherwise load as a `/second-brain:README` command
and an agent. `tools/check_kit.py` keeps the lists in step with the folders.
`claude plugin validate .` passes with a warning that `CLAUDE.md` at the plugin
root is not loaded, and it also reports the two folder READMEs, though the
manifest lists keep them from loading.

## agents-course

Each tool does the practice page of one course module, in your own repo.

| Tool | Invoke as | Module |
|---|---|---|
| Context audit | `/agents-course:context-audit` | [1 · Context](../docs/course-1-context/context-practice.md) — measure the four places, find cache killers and window bloat |
| Goal test | `/agents-course:goal-test` | [2 · Loop](../docs/course-2-loop/loop-practice.md) — turn a task into a testable done, generate the script and the bounded loop |
| Gate check | `/agents-course:gate-check` | [3 · The gate](../docs/course-3-gate/gate-practice.md) — find the decisions that do not need the big model, propose fail-closed gates |
| Harness audit | `/agents-course:harness-audit` | [4 · Harness](../docs/course-4-harness/harness-practice.md) — walk the four rings, state the blast radius, rank the hardening list |
| Evals bootstrap | `/agents-course:evals-bootstrap` | [5 · Evals](../docs/course-5-evals/evals-practice.md) — mine real failures into cases, generate the trace checker |
| Loop critic | agent `agents-course:loop-critic` | [2 · Loop](../docs/course-2-loop/the-four-parts.md) — a checker outside the model: reviews loop results in a clean context |

The skills are plain `SKILL.md` files, so they also work copied into
`~/.claude/skills/` or with any harness that reads the Agent Skills format.

## Running the evals

The plugin ships an eval suite in `agents-course/evals/`, in the format of
Claude Code's built-in plugin evals ([format and options](https://code.claude.com/docs/en/plugin-evals);
needs Claude Code v2.1.269 or later and the same login your sessions use, so
runs count against your plan or API bill). From this repo:

```bash
cd plugins/agents-course
claude plugin eval . --allow-tools Write Edit --threshold 0.8
```

Pass `--allow-tools Write Edit`. Without it those tools are removed from every
run, the `evals-bootstrap` and `goal-test` cases cannot create their files, and
the read-only guard on the audit skills passes trivially. The suite never
grants `Bash`, so no sandbox backend is needed.

Each case runs three times with the plugin and three times without it. One run
of the whole suite with `--runs 1`, both arms, 12 cases, cost $1.72 at list
prices when this suite was written. The default three runs per case should
cost about three times that, roughly $5, plus run-to-run variation. For a
cheap check while editing a skill, run one arm once:

```bash
claude plugin eval . --case 'context-audit-*' --runs 1 --ablation none
```

The twelve cases:

| Case | Checks |
|---|---|
| `context-audit-fires` | The skill fires on a cache and context-layout question; it never calls `Edit` or `Write`; the reply names the dynamic values and the tool count |
| `harness-audit-fires` | The skill fires on an unattended-run safety question; it never edits; the reply states the blast radius and the containment ring |
| `gate-check-fires` | The skill fires on a model-cost question; a judge model checks that only the bounded decisions get a cheaper gate |
| `goal-test-fires` | The skill fires on a vague loop goal and writes `goal-test.*` |
| `evals-bootstrap-fires` | The skill fires on a request for evals; `cases.yaml` and `check_traces.py` exist, the cases use the `trace has` rule language, and the runner calls no model |
| `loop-critic-dispatched` | Claude dispatches the `loop-critic` agent when asked for an independent review, and its output has the `VERDICT` / `defects` shape |
| `*-ignores-unrelated` (four skills) | An unrelated question does not fire the skill |
| `gate-check-ignores-evals-request` | A request for a regression suite does not fire `gate-check` |
| `loop-critic-not-dispatched-for-unrelated` | An unrelated question does not dispatch the critic |

The cases paste their inputs into the prompt instead of using fixture projects,
because fixtures need `--scaffold`, which runs a script as you. Each run starts
in an empty workspace, so the audit skills read the pasted text.

The `no-edit` and `no-write` graders test the plugin's wiring, not the model:
they mean something only while `Edit` and `Write` are granted, and the prompts do not ask
for a change, so they catch a skill that loses its `disallowed-tools` line.

A `Δ` of `0.00` on a case means the plugin did not change the score on that
case. In a first run on 2026-10-05 the content checks of `context-audit-fires`
and `gate-check-fires` also passed without the plugin (those cases have since
gained checks on each skill's own output format, not yet run); the trigger graders
(`tool_used: Skill`) are excluded from the score in a two-arm run, so only the
content checks count there. Read those two as regression guards, not as proof
of lift. Results go to `evals/results/`, which is git-ignored.
