#!/bin/bash
# Install the site build dependency in Claude Code cloud sessions, so
# scripts/build_all.py and the CI checks run as they do in CI.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

# Idempotent: pip skips the pinned version when it is already installed,
# and the container is cached after the hook completes.
python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore -r requirements.txt
