# KV-Cache Tiers on a Local SSD

If a local model sits behind your second-brain agent, every session starts by making the model read the same long preamble again: the system prompt, the tool schemas, the vault index. That work is prefill, and its result is the KV cache. Several inference servers can now keep that cache on a local NVMe drive, so a restart or a new session loads it instead of recomputing it. This page covers what the cache is, which tools do this, the flags each documents, and when it is worth the trouble.

It is the self-hosted counterpart of hosted prompt caching, covered in [How models read context](../course-1-context/how-models-read.md#prompt-caching-pays-for-stillness). The rule from [context engineering](context-engineering.md) applies to both: keep the front of the prompt stable, because only an identical prefix can be reused.

Everything below was read from the projects' own repositories on 6 October 2026. The tools change quickly, and several of the features named here are marked experimental or deprecated by their own docs. Check the docs for the version you run. The last section lists what could not be fetched.

## What the KV cache is

For each token already in the context, each attention layer keeps a key vector and a value vector, so the model does not recompute them for every new token. That stored state is the KV cache. Its size per token is:

```
bytes per token = 2 x layers x KV heads x head dim x bytes per element
```

The 2 is key plus value. Multiply by the number of tokens in context and the cache grows linearly with context, on top of the model weights.

Worked example, Llama 3.1 8B. Meta's [llama-models repository](https://github.com/meta-llama/llama-models/blob/main/models/sku_list.py) lists its architecture arguments as `dim` 4096, `n_layers` 32, `n_heads` 32 and `n_kv_heads` 8 (grouped-query attention, which the [model card](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/MODEL_CARD.md) confirms and gives a context length of 128k). The reference [model code](https://github.com/meta-llama/llama-models/blob/main/models/llama3/model.py) sets `head_dim = args.dim // args.n_heads`, which is 128. At 2 bytes per element (a 16-bit cache; this is an assumption about your server's setting, and Ollama's `OLLAMA_KV_CACHE_TYPE` [documents](https://github.com/ollama/ollama/blob/main/docs/faq.mdx) a default of `f16`):

| Quantity | Calculation | Result |
|---|---|---|
| Per token | 2 x 32 x 8 x 128 x 2 bytes | 131,072 bytes (128 KiB) |
| A 20,000-token stable prefix | 20,000 x 131,072 | 2.62 GB (2.44 GiB) |
| A full 131,072-token context | 131,072 x 131,072 | 16 GiB |

The figures for layers, KV heads and hidden size come from Meta's repository, not from the Hugging Face `config.json`, which could not be fetched; see the last section. They describe the same architecture, but confirm them against the `config.json` of the exact checkpoint you run, since fine-tunes and other models differ. Models that compress the cache differently, such as those using multi-head latent attention, do not follow this formula.

## The tiers

| Tier | Holds | Notes |
|---|---|---|
| GPU memory (HBM or VRAM) | The cache for sequences being served | The only tier attention reads directly |
| CPU RAM | Recently used blocks, pinned for fast copies | vLLM and LMCache both use it as the first offload tier |
| Local NVMe SSD | Larger, slower, survives restarts | The subject of this page |
| Remote (object store, shared filesystem, another node) | Shared across machines | Not needed for one person's vault |

The tiers are a chain, not a menu. vLLM's [KV offloading guide](https://github.com/vllm-project/vllm/blob/main/docs/features/kv_offloading_usage.md) states that only the CPU tier has direct GPU access and that all transfers between GPU and a secondary tier are staged through it. SGLang's [HiCache design](https://github.com/sgl-project/sglang/blob/main/docs/docs/advanced_features/hicache_design.mdx) uses the same layering and calls the tiers L1 (GPU), L2 (host memory) and L3 (storage).

### Where an SSD helps

Prefill is compute-bound work that scales with prompt length. If the same 20,000 tokens open every session, an SSD that holds their KV blocks turns that prefill into a read. LMCache's README describes this as moving KV caches into a tiered hierarchy "enabling reuse across requests, sessions, and engine instances to reduce repeated prefill computation and improve TTFT". The cases that pay off:

- A long prefix that is identical across sessions: the system prompt, tool definitions and a vault index that changes rarely.
- Restarts. GPU and CPU copies are gone after the server restarts; a disk copy is not. vLLM's guide says runs with the same model, block size, parallelism layout and dtype share files under the same directory, and LMCache's README says its standalone server keeps the cache if the engine crashes.
- Many sessions that cannot all stay in RAM.

Whether it wins on your machine depends on one comparison: the time to read the bytes from disk against the time to recompute them. For the 2.62 GB prefix above, the read time is 2.62 GB divided by your drive's measured read throughput. The recompute time is your model's measured prefill time for 20,000 tokens. Measure both (recipe below) rather than assuming.

### Where it does not help

- Decode. Generating each token needs the sequence's KV in GPU memory. Disk is a place to park and reload blocks, not to serve attention from. The vLLM guide describes hits in the offload tiers as "promoted back to GPU on demand".
- Short or constantly changing prompts. If the prefix differs every time, nothing matches. Anything that edits an early token, such as a timestamp in the system prompt, defeats reuse in the same way it defeats API prompt caching.
- A slow drive. If reading a prefix from disk takes longer than recomputing it, the cache is a loss. Check the drive's sequential read speed against your prefill speed. Whether a given SATA or QLC drive is fast enough is a measurement, not a rule; their datasheet figures could not be fetched here.
- A small prefix. Below a few thousand tokens, prefill is usually quick enough that the disk round trip is not worth the wear.

## Tools

### LMCache

[LMCache](https://github.com/LMCache/LMCache) is a KV cache layer for inference engines. Its README lists local disk (SSD) among its storage backends, next to CPU RAM, Redis/Valkey, Mooncake, S3-compatible storage, NIXL and GDS. It documents two modes with vLLM. Its [quickstart](https://github.com/LMCache/LMCache/blob/dev/docs/source/getting_started/quickstart.rst) recommends the multiprocess (MP) mode, and its [local storage page](https://github.com/LMCache/LMCache/blob/dev/docs/source/kv_cache/storage_backends/local_storage.rst) says the older in-process disk mode is deprecated.

MP mode runs `lmcache server` as a separate process with a CPU-memory L1 tier and an optional persistent L2 tier. Quickstart commands, with the filesystem L2 adapter from the [adapter docs](https://github.com/LMCache/LMCache/blob/dev/docs/source/mp/l2_storage/fs.rst) added:

```bash
lmcache server --host localhost --port 5555 \
  --l1-size-gb 20 --eviction-policy LRU \
  --l2-adapter '{"type": "fs", "base_path": "/data/lmcache/l2", "use_odirect": true}'

vllm serve Qwen/Qwen3-8B --port 8000 --kv-transfer-config \
  '{"kv_connector":"LMCacheMPConnector", "kv_role":"kv_both", "kv_connector_extra_config": {"lmcache.mp.host": "localhost", "lmcache.mp.port": 5555}}'
```

`--l1-size-gb` is required. The quickstart uses `--chunk-size 16` as a demo value and says to use the default (256) in production. The fs adapter takes `base_path` (required), `relative_tmp_dir`, `read_ahead_size` and `use_odirect` (default `false`, bypasses the page cache). The quickstart notes that which `LMCacheMPConnector` runs depends on the vLLM version (before 0.20.0 it is vLLM's built-in one), so read it for your version.

The deprecated in-process mode is configured with `LMCACHE_LOCAL_DISK` (a `file://` path), `LMCACHE_MAX_LOCAL_DISK_SIZE` (in GB), `LMCACHE_CHUNK_SIZE` and `LMCACHE_EXTRA_CONFIG` (`use_odirect`, `disk_io_threads`). It creates one file per KV chunk and evicts when full (LRU, currently). It is listed here because older tutorials still use it.

### vLLM's own offloading

vLLM's [`OffloadingConnector`](https://github.com/vllm-project/vllm/blob/main/docs/features/disagg_prefill.md) is built in. Single-tier, CPU only:

```bash
vllm serve <model> --kv-transfer-config '{"kv_connector":"OffloadingConnector","kv_role":"kv_both","kv_connector_extra_config":{"block_size":64,"cpu_bytes_to_use":1000000000}}'
```

For a disk tier, the [usage guide](https://github.com/vllm-project/vllm/blob/main/docs/features/kv_offloading_usage.md) sets `spec_name` to `TieringOffloadingSpec` and adds a `secondary_tiers` entry of `"type": "fs"`:

```bash
vllm serve <model> --kv-transfer-config '{
  "kv_connector": "OffloadingConnector", "kv_role": "kv_both",
  "kv_connector_extra_config": {
    "spec_name": "TieringOffloadingSpec",
    "cpu_bytes_to_use": 10737418240,
    "block_size": 16,
    "eviction_policy": "lru",
    "secondary_tiers": [{"type": "fs", "root_dir": "/mnt/kv_cache",
                         "n_read_threads": 32, "n_write_threads": 16}]
  }}'
```

Documented keys: `cpu_bytes_to_use` is required and is the total across workers; `offload_prompt_only` defaults to `true`, so decode blocks are not offloaded; the fs tier's `n_read_threads` and `n_write_threads` default to 16 each. Per request, `kv_transfer_params` accepts `max_offload_tokens` (cap how many leading tokens are stored; `0` disables offload for that request) and `max_load_tokens` (cap how many are loaded). Both are marked experimental. The guide's tuning tip for the CPU tier is to size it above the aggregate GPU KV cache, because a smaller one only mirrors the GPU. The connector supports CUDA, ROCm and XPU only, so it does not apply to Apple silicon or CPU-only machines.

### SGLang HiCache

SGLang's [best-practices page](https://github.com/sgl-project/sglang/blob/main/docs/docs/advanced_features/hicache_best_practices.mdx) lists the flags `--enable-hierarchical-cache`, `--hicache-ratio`, `--hicache-size` (GB of host memory, overrides the ratio), `--hicache-write-policy` and `--hicache-storage-backend`. The [design page](https://github.com/sgl-project/sglang/blob/main/docs/docs/advanced_features/hicache_design.mdx) lists the backends `file`, `mooncake`, `hf3fs`, `nixl`, `aibrix` and `dynamic`. The `file` backend is the local-disk option. It writes to `/tmp/hicache` unless `SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR` is set, and the page describes it as "a simple file-based storage backend for demonstration purposes". Treat it as a starting point, not a hardened cache. The other backends are aimed at clusters.

```bash
python3 -m sglang.launch_server --model-path <model> \
  --enable-hierarchical-cache --hicache-size 32 \
  --hicache-storage-backend file
```

That command combines flags the docs list individually; it is not a copy of a documented example, and I did not run it.

### llama.cpp

`llama-server` has a RAM prompt cache and explicit save and restore of a slot's cache to disk. From the [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md):

- `--cache-prompt` (default enabled) and `-cram, --cache-ram N` (cache size in MiB, default 8192, `0` disables).
- `--cache-reuse N`: minimum chunk size to reuse via KV shifting (default 0).
- `--slot-save-path PATH`: directory for saved slot caches (default disabled).
- `POST /slots/{id_slot}?action=save`, `action=restore` and `action=erase`. Save and restore take a JSON body with `filename`, relative to `--slot-save-path`.

```bash
llama-server -m model.gguf --slot-save-path /data/slots

curl -X POST 'http://localhost:8080/slots/0?action=save' \
  -H 'Content-Type: application/json' -d '{"filename":"vault-prefix.bin"}'
curl -X POST 'http://localhost:8080/slots/0?action=restore' \
  -H 'Content-Type: application/json' -d '{"filename":"vault-prefix.bin"}'
```

The README's example response shows a save of 1,745 tokens writing 14,309,796 bytes in 49.865 ms, and a restore taking 42.937 ms. It does not name the model or the disk, so use it only as a shape of response. The command-line tools have a separate `--prompt-cache FNAME` (with `--prompt-cache-all` and `--prompt-cache-ro`), documented in the [completion README](https://github.com/ggml-org/llama.cpp/blob/master/tools/completion/README.md); it says a restored cache does not restore the exact session state, so a fixed seed does not guarantee the same output. This route is manual: you save a slot after loading the stable prefix and restore it after a restart. It works on any hardware llama.cpp supports.

### Ollama

Ollama's [FAQ](https://github.com/ollama/ollama/blob/main/docs/faq.mdx) documents `keep_alive` and `OLLAMA_KEEP_ALIVE` (how long a model stays in memory) and `OLLAMA_KV_CACHE_TYPE` (K/V cache quantization, default `f16`, needs Flash Attention). It documents no disk tier for the KV cache. I did not search its source for undocumented behaviour. A smaller cache type reduces the bytes per token in the formula above but does not persist anything.

### NVIDIA Dynamo (KVBM)

The [Dynamo README](https://github.com/ai-dynamo/dynamo/blob/main/README.md) describes the KV Block Manager as one that "Offloads KV cache across GPU → CPU → SSD → remote storage", and its support table marks KVBM as supported for vLLM and TensorRT-LLM and in progress for SGLang. The configuration docs are on docs.nvidia.com, which could not be fetched, so no flags are given here. Dynamo is a multi-node serving system; for one vault it is probably more machinery than needed.

## Practical guidance

**When it pays.** A long prefix reused across many sessions or restarts. If your agent already keeps the prefix under a few thousand tokens, spend the effort on [trimming context](context-engineering.md) instead. If you run a single session and never restart, GPU and CPU tiers cover it.

**Put the stable part first, and only cache that.** Order the prompt as system prompt, tool schemas, vault index, then the per-session material. Cache keys are built from the token prefix, so one changed token early on invalidates everything after it. In vLLM, `max_offload_tokens` stores only the leading tokens of a request, which is the system-prompt use case its docs name.

**Endurance.** Every prompt block that is offloaded is a write. At 128 KiB per token for the 8B example, 1,000,000 newly prefilled tokens a day is 131 GB a day if all are stored. That arithmetic is yours to redo with your model's bytes per token and your real token volume. Compare it with your drive's rated total bytes written (TBW) or drive writes per day, which the drive's datasheet gives. I could not fetch any vendor datasheet, so no endurance figure is stated here. Reduce writes by capping offload to the stable prefix, by setting a disk size limit (`LMCACHE_MAX_LOCAL_DISK_SIZE`) and by not putting the cache on the drive that holds your only copy of the vault.

**NVMe versus SATA, QLC.** Throughput sets how fast a prefix loads. The interface limits for NVMe (PCIe generation and lane count) and SATA (6 Gbit/s link) are in the standards, which could not be fetched; read the datasheet and, better, measure with a tool such as `fio` using large sequential reads. Do not trust the datasheet peak for a QLC drive until you have tested sustained writes, since a long write burst is the case an offload tier produces. This is a testing instruction, not a measured claim.

**Filesystem placement.** Use a local filesystem on the SSD itself, not a network share, and not the volume that holds your vault or backups. vLLM's tier creates many files (sharded by hash prefix) and LMCache's in-process mode creates one per chunk, so a filesystem with generous inode limits helps. LMCache's `use_odirect` bypasses the page cache; its docs recommend it when most CPU memory is in use. Keep the cache directory out of any sync tool or backup. Directories are keyed by model, block size, parallelism and dtype (vLLM), so changing any of them leaves orphaned directories that you delete by hand.

**Privacy.** The cache is derived from your prompts. A KV cache can in principle be used to recover the text it was computed from, so treat the directory like the vault itself: same disk encryption, same permissions. This is a precaution, not a claim from the sources.

## Measure it

Time to first token (TTFT) for a long shared prefix, cold versus cached. The prefix must be real: use your actual system prompt and index.

1. Build a fixed prefix file from your agent's real preamble, and a short question that you change on every run, so only the prefix is shared.
2. Stream a chat request and record the time until the first content chunk arrives.
3. Run it in four states and write down each time:
   - cold: server just started, empty cache directory;
   - GPU-warm: the same request again immediately;
   - disk-warm: restart the engine (keep the cache directory, and for LMCache keep `lmcache server` running or its L2 directory), then send it again;
   - baseline: the same restart with the disk tier disabled.

Disk-warm should beat cold by roughly the prefill time minus the read time. If it does not, the drive or the connector is the bottleneck. After a restart the operating system may still hold the files in its page cache, which makes the disk-warm run look faster than a real cold read; use `use_odirect` where available, or drop caches as root on Linux before the run.

```python
import json, sys, time, urllib.request

prefix = open(sys.argv[1]).read()
question = sys.argv[2]
body = json.dumps({
    "model": sys.argv[3],
    "stream": True, "max_tokens": 1,
    "messages": [{"role": "system", "content": prefix},
                 {"role": "user", "content": question}],
}).encode()
req = urllib.request.Request("http://localhost:8000/v1/chat/completions",
                             body, {"Content-Type": "application/json"})
t0 = time.perf_counter()
with urllib.request.urlopen(req) as r:
    for line in r:
        if line.startswith(b"data: ") and b'"content"' in line:
            print(f"TTFT {time.perf_counter() - t0:.3f} s")
            break
```

This script is a plain timing harness written for this page, not taken from any project's docs; it assumes an OpenAI-compatible server on port 8000 that streams. `llama-server` reports the numbers itself: the `/completion` response has a `timings` object with `cache_n` (prompt tokens reused from cache), `prompt_n` (tokens processed) and `prompt_ms`, so a restore should show a large `cache_n` and a small `prompt_ms`. Run each state several times and keep the median; one run on a cold drive tells you little.

## What was and was not checked

Checked on 6 October 2026 against the primary files named above: the LMCache README and docs source (`quickstart.rst`, `mp/l2_storage/fs.rst`, `local_storage.rst`), vLLM's `disagg_prefill.md` and `kv_offloading_usage.md` on `main`, SGLang's HiCache docs on `main`, the llama.cpp server and completion READMEs on `master`, Ollama's `faq.mdx`, the Dynamo README, and Meta's llama-models repository. The docs describe the branch head, so flags may differ from the release you installed. I ran no server and no benchmark, so no speed result is claimed.

Not re-checked on 6 October 2026 because the page could not be fetched:

- The Hugging Face `config.json` for Llama 3.1 8B (`huggingface.co` was unreachable); the example uses Meta's repository instead.
- NVIDIA's Dynamo and KVBM documentation on docs.nvidia.com.
- Any SSD vendor datasheet, and the NVMe, PCIe and SATA specifications, so no endurance or interface throughput numbers are given.
- The upstream hosted docs sites for LMCache and SGLang; their source files in the repositories were read instead.
- SGLang's `file` backend source and its exact environment variable spelling beyond what the design page prints.
