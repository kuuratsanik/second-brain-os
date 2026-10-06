## What changed

<One topic per PR. Say what and why in a few lines.>

## Sources

<Primary source for every factual claim (README, paper, release note). If a
source could not be fetched, say so and use "not re-checked on <date> because
the page could not be fetched". Write "none" if there are no factual claims.>

## Checklist

- [ ] `python3 tools/check_kit.py --selftest && python3 tools/check_kit.py`
- [ ] `python3 tools/doc_links.py --selftest && python3 tools/doc_links.py`
- [ ] `python3 tools/check_external_links.py --selftest` (no network)
- [ ] `python3 -m unittest discover -s tests -t .`
- [ ] `ruff check .` (ruff 0.16.10, rules in `ruff.toml`)
- [ ] `zizmor --offline --no-progress .github` (zizmor 1.30.1) and `actionlint`, if a workflow changed
- [ ] `python3 vault-template/.claude/hooks/test_guard.py`
- [ ] `python3 scripts/link_check.py vault-template`
- [ ] A new docs page updated its section `README.md` index (or the page order in `scripts/build_tracks.py`)
- [ ] Plain writing: no marketing language, no emoji

## Generated HTML

- [ ] Rebuilt with `pip install -r requirements.txt && python3 scripts/build_all.py` and the result is committed
- [ ] Not needed: nothing under `docs/`, `resources/`, `tools/`, `skills/`, `commands/`, `agents/`, `scripts/` or `plugins/` changed
