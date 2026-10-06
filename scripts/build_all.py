#!/usr/bin/env python3
"""Rebuild the whole site, in the one correct order.

    pip install -r requirements.txt
    python3 scripts/build_all.py

Steps (each reads the output of the one before):
  1. tools/extract_site.py   docs/ + resources/   -> site_data.json
  2. tools/build_site.py     site_data.json       -> index.html, resources.html
  3. scripts/build_tracks.py course + handbooks   -> index.html (marker blocks)
  4. scripts/build_tree.py   repo + index.html    -> tree.html
  5. scripts/build_static.py site constants       -> sitemap.xml, robots.txt, 404.html
  6. scripts/build_llms.py   index.html + docs/   -> llms.txt, llms-full.txt
  7. scripts/build_feed.py   CHANGELOG.md         -> feed.xml
  8. scripts/build_og.py     site palette         -> og.png

The output is deterministic: running this twice gives identical bytes.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = ["tools/extract_site.py", "tools/build_site.py",
         "scripts/build_tracks.py", "scripts/build_tree.py",
         "scripts/build_static.py", "scripts/build_llms.py",
         "scripts/build_feed.py", "scripts/build_og.py"]

for step in STEPS:
    print(f"== {step}", flush=True)
    subprocess.run([sys.executable, os.path.join(ROOT, step)], cwd=ROOT, check=True)
