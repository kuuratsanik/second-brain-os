# The Four Rings

Build the harness from the outside in: containment, guides, sensors, permissions. The order matters because each ring must hold when every ring inside it fails. A guide can be ignored, a sensor can miss, an approval can be misclicked; a wall does not care. So the outermost ring goes up before the first prompt is written.


![Nested boxes around the model, from outside in: containment (what it cannot reach at all), guides (AGENTS.md, tool descriptions), sensors (tests, linters, review) and permissions (approval for the irreversible).](fig-four-rings.svg)

## Ring one: containment

Containment is what the agent physically cannot reach, and it is the only ring that works with zero model cooperation. The standard kit: a container or VM rather than your laptop's shell; a throwaway branch or git worktree rather than main; a read-only database user rather than the application's credentials; a network allowlist rather than the open internet. None of this involves prompting. If you set it up before the agent's first run, the worst possible session is a discarded branch and a wasted API bill.

## Ring two: guides

Guides are everything the agent reads before acting: AGENTS.md files, tool descriptions, examples. They are cheap, and they carry most of the day-to-day quality. A useful AGENTS.md is four lines, not four pages:

```markdown
- Monorepo: services live in services/, shared code in packages/. Run everything from the repo root.
- `make test` must pass before you call any task done.
- Never hand-edit files in migrations/ — generate them with `make migration`.
- Your database user is read-only. Ask before proposing any schema change.
```

Tool design is the other half of this ring. Google's Kaggle whitepaper [Agent Tools & Interoperability with MCP](https://www.kaggle.com/whitepaper-agent-tools-and-interoperability-with-mcp) sorts tools into function tools, built-in tools and agent tools, and its best practices are all guide-writing: document each tool well enough that the model can choose it by description alone, design tools around tasks rather than API surfaces, return concise output, and make errors teach the fix. Prefer a typed tool over raw access — `search_orders(customer_id)` beats handing over a SQL connection, because the schema is itself containment. The whitepaper's case for MCP is interoperability: one open protocol (JSON-RPC 2.0 over stdio or streamable HTTP) so N clients and M tool servers need one integration each, not N×M. The full treatment is in [tools and MCP](../track-harness/tools-and-mcp.md).

## Ring three: sensors

Sensors tell you, deterministically, whether the work is sound. Run the cheap ones on everything: linter, type checker, test suite after every change — they cost seconds and never get tired. Spend the expensive ones — a second model reviewing the diff, a human reading it — only on what matters: auth code, migrations, anything that moves money. A harness where `make test` runs automatically catches more than one where a reviewer is meant to remember.

## Ring four: permissions

Anthropic reports that [Claude Code users approve 93% of permission prompts](https://www.anthropic.com/engineering/claude-code-auto-mode) (March 2026). A gate that opens 93 times in 100 trains people to stop reading it. The real protection is ring one — actions that are not available at all — so spend approval prompts only on the truly irreversible: pushing to a shared branch, sending anything, deleting anything. Three prompts a day get read; thirty get clicked.

## Hooks: guides with teeth

A guide the model might skim becomes a rule the harness enforces. In Claude Code, a [PreToolUse hook](https://code.claude.com/docs/en/hooks) runs before a matching tool call and can block it; this one enforces "never push to main":

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.command' | grep -qE 'git push.*\\bmain\\b' && { echo 'Blocked: never push to main' >&2; exit 2; } || exit 0"
          }
        ]
      }
    ]
  }
}
```

Exit code 2 blocks the call and shows the hook's stderr to the model as the reason, so the agent corrects course instead of failing silently. The hooks guide positions hooks as the way to enforce project rules rather than relying on the model to follow them.

## The bets expire

Every ring component is a bet that the model cannot do something. Anthropic added context resets to a harness because Claude Sonnet 4.5 wrapped up work prematurely near its context limit — then [dropped them entirely](https://www.anthropic.com/engineering/harness-design-long-running-apps) when Opus 4.5 largely removed that behaviour. Your bets will expire the same way. [Harness practice](harness-practice.md) turns that into a quarterly ritual.
