#!/usr/bin/env python3
"""Claude Code SessionStart hook: warns when the vault's guard files were changed.

Compares the working copy of three files with the version in the last commit
(git show HEAD:path), by SHA-256:

  .claude/settings.json      permission rules and hook registration
  .claude/hooks/guard.py     the guard itself
  CLAUDE.md                  the vault's rules

It prints a warning to stdout when a file differs from HEAD, is not tracked, is
missing, or when git cannot answer. Per https://code.claude.com/docs/en/hooks
(read 2026-10-06), SessionStart is one of the events where "Claude Code adds
plain-text stdout as context that Claude can see and act on", and exit 0 is
success. SessionStart cannot block: exit 2 only shows stderr to the user. So this
script always exits 0, and prints nothing when all three files match HEAD.

Limits: it compares with the last commit, so a tampered file that was then
committed passes; it runs at session start, not on every call; and it cannot
report on itself or on a settings.json that no longer registers it. Line endings
are ignored (CRLF and LF compare equal). Stdlib only; Python 3.9 or newer.
"""
import hashlib
import json
import os
import subprocess
import sys

FILES = (".claude/settings.json", ".claude/hooks/guard.py", "CLAUDE.md")


def sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def git_show(root, path):
    """(bytes or None, problem). None with problem None means 'not in HEAD'."""
    try:
        p = subprocess.run(["git", "show", "HEAD:./" + path], cwd=root, capture_output=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git could not run ({type(e).__name__})"
    if p.returncode == 0:
        return p.stdout, None
    err = p.stderr.decode("utf-8", "replace").lower()
    if "not a git repository" in err:
        return None, "this folder is not a git repository"
    if "unknown revision" in err or "bad revision" in err or "does not have any commits" in err \
            or "ambiguous argument 'head" in err or "invalid object name 'head'" in err:
        return None, "the repository has no commit yet"
    return None, None  # the path is not in HEAD


def check(root):
    """List of problem lines; empty when all files match HEAD."""
    problems = []
    for rel in FILES:
        path = os.path.join(root, *rel.split("/"))
        committed, problem = git_show(root, rel)
        if problem:
            hint = (" Do the Quickstart's first-commit step (git init, git add of the template files "
                    "including .claude/hooks, git commit -m \"Initial vault\") so there is a committed "
                    "version to compare with." if "no commit" in problem or "not a git" in problem else "")
            return [f"Integrity check could not run: {problem}. The settings, guard and "
                    f"CLAUDE.md cannot be compared with a committed version.{hint}"]
        try:
            with open(path, "rb") as f:
                current = f.read()
        except OSError:
            current = None
        if current is None and committed is None:
            problems.append(f"{rel} is missing and was never committed")
        elif current is None:
            problems.append(f"{rel} is committed but missing from the working folder")
        elif committed is None:
            problems.append(f"{rel} is not tracked by git (no committed version to compare with)")
        elif sha(current) != sha(committed):
            problems.append(f"{rel} differs from the last commit")
    return problems


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or (
        data.get("cwd") if isinstance(data, dict) and isinstance(data.get("cwd"), str) else None
    ) or os.getcwd()
    try:
        problems = check(root)
    except Exception as e:  # never fail a session start, but say the check did not run
        problems = [f"Integrity check failed to run ({type(e).__name__}: {e})"]
    if problems:
        lines = ["WARNING: vault integrity check (.claude/hooks/integrity.py).",
                 *("- " + p for p in problems),
                 "These files hold the vault's safety rules. If you did not change them, "
                 "treat the session as untrusted: do not rely on the guard, tell the owner "
                 "before doing anything else, and do not edit or commit these files. The "
                 "owner can compare with `git diff HEAD -- <file>` and commit intended "
                 "changes (a Profile edit to CLAUDE.md shows up here until it is committed)."]
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
