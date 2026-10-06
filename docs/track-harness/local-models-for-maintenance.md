# Local Models for Cheap Maintenance

Some vault maintenance is routine enough that a small model on your own CPU might do it: suggest tags, write a one-paragraph summary of one source, sort lint findings into "mechanical" and "needs a human". This page covers what such a model can and cannot do in a second-brain vault, how to run it with `llama-server` from llama.cpp, how to turn the vault's `CLAUDE.md` into a saved prompt-cache slot so each run does not re-read it, and how to point `vault_search.py --embed-url` at a local embedding server.

It does not claim a local model matches Claude. No model was run for this page, and no quality or speed figure is given. Where a statement is a judgement rather than something a source says, it says so.

Everything attributed to llama.cpp below was read from its [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) on `master` on 6 October 2026, through a fetch tool that returns extracts, not the whole file. The flags change between releases; run `llama-server --help` on the build you have. The last section lists what was not checked.

## What a small local model can and cannot do here

This is judgement, not measurement. The test that matters is whether you can check the output cheaply. A small model is a reasonable fit where you can, and a poor one where you cannot.

| Job | Fit | Why |
|---|---|---|
| Tag a page from a fixed vocabulary | Plausible | A closed choice. Your script can reject any tag not in the vocabulary |
| Summarise one source page in a paragraph | Plausible, with a check | The source is in the prompt, so you can compare. Small models are more likely to drop or invent detail than a large one; sample and read |
| Triage `link_check` output (broken link, stub, stale) into mechanical or needs-human | Plausible | A short classification of lines the script already found |
| Draft aliases or the other-language title | Weak | Needs knowledge of what the owner actually calls things; an alias must be a real name, not an invented one |
| Ingest a source into several linked pages | Do not | Needs the whole vault in view and judgement about what already exists |
| Find contradictions, merge duplicates, decide what to archive | Do not | The vault `CLAUDE.md` makes uncertain identity a hard stop (f), and a wrong merge is expensive |
| Read email, meetings or web pages unattended | Do not | The [graduation page](build-graduate.md) gives "reads untrusted content" and "runs unattended" as reasons to use a harness with a real permission system; a script you wrote has neither |

Three facts shape the design.

**Claude Code is not the harness for this.** The Claude Code gateway documentation says Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway" ([LLM gateways](https://code.claude.com/docs/en/llm-gateway), read 6 October 2026). llama-server does offer an Anthropic-compatible `/v1/messages` endpoint, per its README, but that does not make the pairing supported. So a local job is a small script of your own that sends a prompt to llama-server and reads the reply, in the shape of [the loop you built](build-the-loop.md).

**Your script has none of the vault's guardrails.** The vault's `.claude/settings.json` and guard hook protect Claude Code sessions. They do not see your script. Give the script one place to write, a proposals file such as `output/local-proposals-YYYY-MM-DD.md`, and have it validate before writing (is every tag in the vocabulary, does the summary quote text that is in the source). Then a Claude session or you apply what is worth applying. That keeps the local model on proposals and the vault rails on writes.

**Local does keep content on the machine.** The README gives `--host` a default of `127.0.0.1`, so a server started without that flag listens only on the local machine. That matters for `private` pages, whose content the vault `CLAUDE.md` bars from any request to another service. If you set `--host` to expose the server, set `--api-key` as well; the README lists both.

## Run llama-server on a CPU

```bash
llama-server -m ./models/your-chat-model.gguf \
  -c 8192 -t 8 -np 1 -ngl 0 \
  --host 127.0.0.1 --port 8080 \
  --slot-save-path ./slots
```

What the README says about each flag:

| Flag | README description (quoted) |
|---|---|
| `-m, --model FNAME` | model path to load |
| `-c, --ctx-size N` | "size of the prompt context (default: 0, 0 = loaded from model)" |
| `-t, --threads N` | "number of CPU threads to use during generation (default: -1)" |
| `-np, --parallel N` | "number of server slots (default: -1, -1 = auto)" |
| `-ngl, --gpu-layers N` | "max. number of layers to store in VRAM, either an exact number, 'auto', or 'all' (default: auto)" |
| `--host HOST` | "IP addresses to listen on ... (default: 127.0.0.1)" |
| `--slot-save-path PATH` | "path to save slot kv cache (default: disabled)" |

`-ngl 0` is this page's reading of the `-ngl` description: if it is the maximum number of layers kept in VRAM, zero keeps none there. On a machine with no GPU the default `auto` should already do that; the flag is only a way to say so. `-np 1` gives one slot, so there is one cache to save and restore; the README documents `--kv-unified` and `--kv-unified-per-slot`, and how the context is divided between slots depends on those flags, which this page did not study, so read them before raising it. Set `-t` to your physical core count as a starting point, which is a convention, not a README recommendation, and measure.

Calling it from a script uses the OpenAI-compatible chat endpoint, which the README describes as "POST `/v1/chat/completions`: OpenAI-compatible Chat Completions API" that takes `messages`. For output your script must parse, the README documents schema-constrained JSON (`{"type": "json_object", "schema": {...}}`) and grammar-based sampling. Use one of them for tags and triage so the model cannot return free text where your code expects a list. Constraining the shape does not make the content right; you still validate it.

## Make CLAUDE.md a saved slot

llama-server does not read `CLAUDE.md`. That file is Claude Code's. What you can do is put the same text at the start of every prompt your script sends, and have the server keep the processed result.

The [KV-cache page](kv-cache-ssd-tier.md) explains why: the model has to read the stable front of the prompt before it can read your page, and that work (prefill) is the slow part on a CPU. The vault `CLAUDE.md` in this repo is about 12,000 characters (1,800 words); the token count depends on the model's tokenizer, so measure it rather than guess. If every maintenance call starts with that text, only the page at the end is new.

Per the README, `--cache-prompt` is on by default, and the `cache_prompt` request option reads "Re-use KV cache from a previous request if possible. This way the common prefix does not have to be re-processed, only the suffix that differs between the requests." So within one server run, a stable prefix is reused for free. Saving a slot makes it survive a restart:

1. Build the prefix once: your instruction block, the vault `CLAUDE.md`, the tag vocabulary. Keep it byte-identical from run to run. Put the page being processed after it, never before; one changed early character defeats the reuse.
2. Send a first request with that prefix (and a trivial question), pinned to a slot with `id_slot` (README: "Assign the completion task to an specific slot. If is -1 the task will be assigned to a Idle slot.").
3. Save the slot. The README documents `POST /slots/{id_slot}?action=save` with a required `filename`, relative to `--slot-save-path`:

   ```bash
   curl -X POST 'http://127.0.0.1:8080/slots/0?action=save' \
     -H 'Content-Type: application/json' -d '{"filename":"vault-claude-md.bin"}'
   ```

4. At the start of each scheduled run, after starting the server, restore it with `action=restore` and the same `filename`.
5. Check it worked. The `/completion` response's `timings` object includes `cache_n` ("number of prompt tokens reused from cache") and `prompt_n` ("number of prompt tokens being processed"). After a restore, `cache_n` should be large and `prompt_n` small.

When `CLAUDE.md` changes, or you change the model, the saved file no longer matches: save a new one. The README does not say what a restore does with a file from a different model, so do not rely on it; keep one file per model and per `CLAUDE.md` version in the name. The kv-cache page covers the other cache routes, and its measurement recipe works here too.

## Point vault_search at a local embedding server

`scripts/vault_search.py` ranks with BM25 on its own. With `--embed-url` it adds semantic ranking, using an embedding endpoint, and caches vectors on disk with `--embed-cache`. The README's description of `--embedding` is: "restrict to only support embedding use case; use only with dedicated embedding models (default: disabled)". So an embedding server is a second llama-server process with an embedding model, not the chat server you started above.

```bash
llama-server -m ./models/your-embedding-model.gguf --embedding \
  --host 127.0.0.1 --port 8081

python3 scripts/vault_search.py . "hoidmine" --embed-url http://127.0.0.1:8081 \
  --embed-cache .cache/embeddings.json
```

Notes from the README: `--pooling {none,mean,cls,last,rank}` is the "pooling type for embeddings, use model default if unspecified", so usually leave it. The `/v1/embeddings` endpoint is OpenAI-compatible and "requires pooling different from `none`"; the separate `/embedding` endpoint also supports `none`. Which of the two paths the script calls, and whether `--embed-url` wants the base address or the full path, is in `python3 scripts/vault_search.py --help`; check it on the version you have rather than copying the line above.

The cache file holds vectors computed from your pages. Treat it like the pages: keep `.cache/` out of git (the vault template's `.gitignore` lists it) and out of any shared folder. Use an address on this machine only. The `/ask` skill follows the same rule, because page text goes to the server.

## Run it on a schedule

A scheduled job that uses a local model is a plain script run by `cron`, Task Scheduler or a Desktop scheduled task, not a Claude Code session; see [scheduled maintenance](../06-agents/scheduled-maintenance.md) for where each runs. The job starts llama-server, restores the slot, loops over the pages, writes proposals and stops the server. CPU inference is slow, so cap the pages per run, as the vault rails cap ingest at 20.

## Quality limits against Claude

State these plainly before relying on any of this.

- No comparison was run for this page. Do not assume the small model's tags, summaries or triage are as good as Claude's; assume they are worse until a sample says otherwise.
- Expect more format slips, more invented detail in summaries and weaker handling of the vault's rules. The schema constraint and your validation catch the first; reading a sample catches the others.
- Before you switch a job on, run the local model and Claude on the same 20 pages and read both. Count tags outside the vocabulary and summaries with a claim not in the source. If you would not accept the local output unreviewed, do not schedule it unreviewed.
- Keep a Claude pass on top: a weekly run that reads the proposals file and applies, edits or discards each item. That is the cheap part of the saving, and the part that keeps the wiki's quality where it was.
- Anything that needs the whole vault in view, or that is a hard stop in `CLAUDE.md`, stays with Claude and the owner.

## What was and was not checked

Checked on 6 October 2026: the llama.cpp server README on `master` (flags `-m`, `-c`, `-t`, `-np`, `-ngl`, `--host`, `--api-key`, `--embedding`, `--pooling`, `--slot-save-path`, `--cache-prompt`; the `/v1/embeddings`, `/embedding`, `/v1/chat/completions`, `/v1/messages` and `/slots` endpoints; `cache_prompt`, `id_slot`, `cache_n` and `prompt_n`; JSON-schema and grammar options), and the Claude Code gateway documentation.

Not re-checked on that date:

- The last part of the server README (about 16,000 of its 116,000 characters) was not returned by the fetch tool.
- The fetch tool returned extracts, so quoted descriptions are as it returned them; confirm any flag against `llama-server --help` for your build.
- What `--slot-save-path` restore does across different models, and how `--kv-unified` and `--kv-unified-per-slot` change the division of context between slots when `-np` is above 1.
- The exact path and base-address handling of `--embed-url` in `vault_search.py`, which belongs to the script, not to llama.cpp.
- Model choice, model file formats and their licences, CPU speed, and token counts. No model was downloaded or run.
