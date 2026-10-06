#!/usr/bin/env python3
"""Print one version's section of CHANGELOG.md, for a GitHub release body.

Usage:
    python3 tools/release_notes.py VERSION [--changelog PATH]
    python3 tools/release_notes.py --selftest

VERSION is `1.3.0` or `v1.3.0`. The section is the text under the heading
`## [VERSION] - date`, up to the next `## ` heading, without the heading itself
and without leading or trailing blank lines. Headings inside fenced code blocks
are ignored. Exit status 1 and a message on stderr if the version has no
heading or its section is empty. Standard library only.

.github/workflows/release.yml runs this on a `v*` tag; tools/check_kit.py
imports `find_section` to check that skills/VERSION has a heading.
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def normalize(version):
    v = version.strip()
    return v[1:] if v[:1] in ("v", "V") else v


def find_section(text, version):
    """Return the section body for `version`, or None if there is no heading for it."""
    version = normalize(version)
    heading = re.compile(r"^##\s+\[" + re.escape(version) + r"\](\s|$)")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    body, found, fenced = [], False, False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            if found:
                break
            if heading.match(line):
                found = True
                continue
        if found:
            body.append(line)
    if not found:
        return None
    return "\n".join(body).strip("\n").strip()


def main_cli(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("version", nargs="?")
    ap.add_argument("--changelog", default=str(Path(__file__).resolve().parent.parent / "CHANGELOG.md"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.version:
        ap.error("VERSION is required")
    version = normalize(args.version)
    if not SEMVER.match(version):
        print(f"release_notes: {args.version!r} is not X.Y.Z or vX.Y.Z", file=sys.stderr)
        return 1
    path = Path(args.changelog)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        print(f"release_notes: cannot read {path}: {e}", file=sys.stderr)
        return 1
    section = find_section(text, version)
    if section is None:
        print(f"release_notes: {path} has no heading '## [{version}]'", file=sys.stderr)
        return 1
    if not section:
        print(f"release_notes: the section for {version} in {path} is empty", file=sys.stderr)
        return 1
    sys.stdout.write(section + "\n")
    return 0


SAMPLE = """# Changelog

Intro.

## [Unreleased]

- Not released.

## [1.2.0] - 2026-02-01

### Added

- Thing one.

```
## [9.9.9] - not a heading
```

- Thing two.

## [1.1.0] - 2026-01-01

### Fixed

- Old fix.

## [1.0.0] - 2025-12-01
"""


def selftest():
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f"{label}: expected {want!r}, got {got!r}")

    check("middle section",
          find_section(SAMPLE, "1.2.0"),
          "### Added\n\n- Thing one.\n\n```\n## [9.9.9] - not a heading\n```\n\n- Thing two.")
    check("leading v", find_section(SAMPLE, "v1.1.0"), "### Fixed\n\n- Old fix.")
    check("empty last section", find_section(SAMPLE, "1.0.0"), "")
    check("unreleased", find_section(SAMPLE, "Unreleased"), "- Not released.")
    check("missing version", find_section(SAMPLE, "1.3.0"), None)
    check("fenced heading is not a heading", find_section(SAMPLE, "9.9.9"), None)
    check("prefix does not match", find_section(SAMPLE, "1.2"), None)
    check("crlf", find_section("## [2.0.0] - x\r\n\r\n- a\r\n\r\n## [1.0.0]\r\n", "2.0.0"), "- a")

    tmp = Path(tempfile.mkdtemp())
    try:
        cl = tmp / "CHANGELOG.md"
        cl.write_text(SAMPLE, encoding="utf-8")
        for argv, code in (
            (["1.1.0", "--changelog", str(cl)], 0),
            (["v1.2.0", "--changelog", str(cl)], 0),
            (["1.0.0", "--changelog", str(cl)], 1),   # empty section
            (["1.3.0", "--changelog", str(cl)], 1),   # no heading
            (["1.3", "--changelog", str(cl)], 1),     # not X.Y.Z
            (["1.1.0", "--changelog", str(tmp / "none.md")], 1),
        ):
            out, err = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = open(tmp / "out.txt", "w", encoding="utf-8")
            try:
                got = main_cli(argv)
            finally:
                sys.stdout.close()
                sys.stdout, sys.stderr = out, err
            check(f"exit status for {argv[0]}", got, code)
    finally:
        for p in tmp.iterdir():
            p.unlink()
        tmp.rmdir()

    for f in failures:
        print("FAIL", f)
    print("selftest:", "FAILED" if failures else "ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main_cli(sys.argv[1:]))
