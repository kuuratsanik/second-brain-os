---
type: regex
pattern: 'anthropic|openai|messages\.create'
flags: i
target: { source: file, path: check_traces.py }
match: not_contains
---
