#!/usr/bin/env python3
"""Validate the agent kit that ships to users' vaults. Standard library only.

Usage:
    python3 tools/check_kit.py [--root DIR]
    python3 tools/check_kit.py --selftest

Checks, as `path:line: message`, exit status 1 on any problem:

* every skill, command and agent file has parseable frontmatter with its
  required fields and no unknown keys;
* skill names match their folder and name and description stay in limits;
* commands, skills and agents name only `second-brain-*` skills and
  `scripts/*.py` files that exist;
* a command has `argument-hint` if and only if its body uses `$ARGUMENTS`;
* `.claude-plugin/marketplace.json` and each `plugin.json` are valid and the
  plugin sources resolve;
* the schedulable-command list in `commands/README.md` is exactly the set of
  commands without `disable-model-invocation: true`.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Allowed frontmatter keys, from the Claude Code docs (checked 2026-10-05):
#   https://code.claude.com/docs/en/skills        (skill and command fields)
#   https://code.claude.com/docs/en/slash-commands (commands: all skill fields
#       except `name` and `paths`)
#   https://code.claude.com/docs/en/sub-agents    (subagent fields)
SKILL_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
COMMAND_KEYS = SKILL_KEYS - {"name", "paths"}
AGENT_KEYS = {
    "name", "description", "tools", "disallowedTools", "model",
    "permissionMode", "maxTurns", "skills", "mcpServers", "hooks", "memory",
    "background", "omitClaudeMd", "effort", "isolation", "color",
    "initialPrompt", "experimental",
}
# The sub-agents docs say plugin agents ignore these, so shipping them is a bug.
PLUGIN_AGENT_IGNORED = {"hooks", "mcpServers", "permissionMode"}
DESC_LIMIT = 1536  # description + when_to_use, per the skills docs

KEY_LINE = re.compile(r"^([A-Za-z][\w-]*)\s*:(?:\s+(.*)|\s*)$")
SKILL_REF = re.compile(r"(?<![\w/.-])second-brain-[a-z0-9]+(?:-[a-z0-9]+)*(?![\w/.-])")
NOT_SKILLS = {"second-brain-os"}  # the repository name
SCRIPT_REF = re.compile(r"(?<![\w./${}-])scripts/([\w.-]+\.py)")
TRUE = {"true", "yes", "on", "1"}


def parse_frontmatter(text):
    """Return (fields, body_start_line, errors). fields maps key -> (value, line)."""
    lines = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 1, [(1, "missing opening '---' frontmatter fence")]
    fields, errors, cur = {}, [], None
    for i, raw in enumerate(lines[1:], start=2):
        if raw.strip() == "---":
            return fields, i + 1, errors
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t" or raw.startswith("- "):
            if cur is None:
                errors.append((i, "indented line with no key above it"))
            else:
                v, ln = fields[cur]
                fields[cur] = ((v + " " + raw.strip()).strip(), ln)
            continue
        m = KEY_LINE.match(raw)
        if not m:
            errors.append((i, f"not a 'key: value' line: {raw[:40]!r}"))
            cur = None
            continue
        cur = m.group(1)
        if cur in fields:
            errors.append((i, f"duplicate key '{cur}'"))
        val = (m.group(2) or "").strip()
        if val in (">", ">-", ">+", "|", "|-", "|+"):
            val = ""
        if val and val[0] in "\"'" and val[-1:] == val[0] and len(val) > 1:
            val = val[1:-1]
        elif val and val[0] in "\"'":
            errors.append((i, f"unterminated quote in '{cur}'"))
        fields[cur] = (val, i)
    errors.append((len(lines), "frontmatter is never closed with '---'"))
    return fields, len(lines), errors


class Checker:
    def __init__(self, root):
        self.root = Path(root)
        self.problems = []

    def rel(self, path):
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def err(self, path, line, msg):
        self.problems.append(f"{self.rel(path)}:{line}: {msg}")

    def read(self, path):
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as e:
            self.err(path, 1, f"cannot read: {e}")
            return None

    def load(self, path, allowed, required):
        text = self.read(path)
        if text is None:
            return None, ""
        fields, body_start, errors = parse_frontmatter(text)
        for line, msg in errors:
            self.err(path, line, msg)
        if fields is None:
            return None, text
        for key, (_, line) in fields.items():
            if key not in allowed:
                self.err(path, line, f"unknown frontmatter key '{key}'")
        for key in required:
            if not fields.get(key, ("", 0))[0]:
                self.err(path, 1, f"missing required field '{key}'")
        body = "\n".join(text.replace("\r\n", "\n").split("\n")[body_start - 1:])
        return fields, body

    # ---- file kinds -------------------------------------------------------

    def check_skill(self, path):
        fields, body = self.load(path, SKILL_KEYS, ("name", "description"))
        if fields is None:
            return
        name = fields.get("name", ("", 0))[0]
        if name and name != path.parent.name:
            self.err(path, fields["name"][1],
                     f"name '{name}' does not match folder '{path.parent.name}'")
        n = len(fields.get("description", ("", 0))[0]) + len(fields.get("when_to_use", ("", 0))[0])
        if n > DESC_LIMIT:
            self.err(path, fields["description"][1],
                     f"description is {n} characters, limit {DESC_LIMIT}")
        return body

    def check_command(self, path):
        fields, body = self.load(path, COMMAND_KEYS, ("description",))
        if fields is None:
            return None, None
        uses = "$ARGUMENTS" in body
        has = "argument-hint" in fields
        if uses and not has:
            self.err(path, 1, "body uses $ARGUMENTS but there is no argument-hint")
        if has and not uses:
            self.err(path, fields["argument-hint"][1],
                     "argument-hint is set but the body never uses $ARGUMENTS")
        return fields, body

    def check_agent(self, path, plugin):
        fields, body = self.load(path, AGENT_KEYS, ("name", "description"))
        if fields is None:
            return None
        if plugin:
            for key in PLUGIN_AGENT_IGNORED & set(fields):
                self.err(path, fields[key][1], f"plugin agents ignore '{key}'")
        name = fields.get("name", ("", 0))[0]
        if name and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            self.err(path, fields["name"][1], f"agent name '{name}' is not lowercase-hyphenated")
        return body

    # ---- references -------------------------------------------------------

    def check_refs(self, path, body, skills, line_offset=0):
        if body is None:
            return
        for lineno, line in enumerate(body.split("\n"), start=1):
            for ref in SKILL_REF.findall(line):
                if ref not in skills and ref not in NOT_SKILLS:
                    self.err(path, lineno, f"references skill '{ref}', which does not exist")
            for ref in SCRIPT_REF.findall(line):
                if not (self.root / "scripts" / ref).is_file():
                    self.err(path, lineno, f"references scripts/{ref}, which does not exist")

    # ---- plugins ----------------------------------------------------------

    def load_json(self, path):
        text = self.read(path)
        if text is None:
            return None
        try:
            data = json.loads(text)
        except ValueError as e:
            self.err(path, getattr(e, "lineno", 1), f"invalid JSON: {e}")
            return None
        if not isinstance(data, dict):
            self.err(path, 1, "top level must be an object")
            return None
        return data

    def check_marketplace(self):
        path = self.root / ".claude-plugin" / "marketplace.json"
        if not path.is_file():
            if (self.root / "plugins").is_dir():
                self.err(path, 1, "missing, but plugins/ exists")
            return
        data = self.load_json(path)
        if data is None:
            return
        if not isinstance(data.get("name"), str) or not data.get("name"):
            self.err(path, 1, "missing required field 'name'")
        owner = data.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            self.err(path, 1, "missing required field 'owner.name'")
        plugins = data.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            self.err(path, 1, "'plugins' must be a non-empty list")
            return
        listed = set()
        for i, p in enumerate(plugins):
            where = f"plugins[{i}]"
            if not isinstance(p, dict):
                self.err(path, 1, f"{where} must be an object")
                continue
            name, source = p.get("name"), p.get("source")
            if not name:
                self.err(path, 1, f"{where} missing 'name'")
            if not source:
                self.err(path, 1, f"{where} missing 'source'")
                continue
            if isinstance(name, str):
                if name in listed:
                    self.err(path, 1, f"duplicate plugin name '{name}'")
                listed.add(name)
            if not isinstance(source, str):
                continue  # github/git sources are resolved by Claude Code, not here
            if not source.startswith("./"):
                self.err(path, 1, f"{where} source '{source}' must start with './'")
                continue
            target = (self.root / source).resolve()
            if self.root.resolve() not in target.parents and target != self.root.resolve():
                self.err(path, 1, f"{where} source '{source}' leaves the repository")
            elif not target.is_dir():
                self.err(path, 1, f"{where} source '{source}' is not a directory")
            else:
                manifest = target / ".claude-plugin" / "plugin.json"
                if not manifest.is_file():
                    self.err(manifest, 1, "missing plugin.json")
                else:
                    pj = self.load_json(manifest)
                    if pj is not None and pj.get("name") != name:
                        self.err(manifest, 1,
                                 f"name '{pj.get('name')}' differs from marketplace entry '{name}'")
        # every plugin directory should be listed
        pdir = self.root / "plugins"
        if pdir.is_dir():
            for d in sorted(x for x in pdir.iterdir() if x.is_dir()):
                if not any(isinstance(p, dict) and isinstance(p.get("source"), str)
                           and (self.root / p["source"]).resolve() == d.resolve()
                           for p in plugins):
                    self.err(path, 1, f"plugins/{d.name} is not listed in the marketplace")

    def check_plugin_manifests(self):
        for manifest in sorted(self.root.glob("plugins/*/.claude-plugin/plugin.json")):
            data = self.load_json(manifest)
            if data is None:
                continue
            if not isinstance(data.get("name"), str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["name"]):
                self.err(manifest, 1, "'name' is required and must be lowercase-hyphenated")
            ver = data.get("version")
            if ver is not None and not (isinstance(ver, str) and re.fullmatch(r"\d+\.\d+\.\d+\S*", ver)):
                self.err(manifest, 1, f"version {ver!r} is not semver")
            for key in ("description", "license", "homepage", "repository"):
                if key in data and not isinstance(data[key], str):
                    self.err(manifest, 1, f"'{key}' must be a string")
            if "keywords" in data and not (isinstance(data["keywords"], list)
                                           and all(isinstance(k, str) for k in data["keywords"])):
                self.err(manifest, 1, "'keywords' must be a list of strings")

    # ---- schedulable list -------------------------------------------------

    def check_schedulable(self, commands):
        readme = self.root / "commands" / "README.md"
        text = self.read(readme) if readme.is_file() else None
        if text is None:
            self.err(readme, 1, "missing commands/README.md")
            return
        flat = re.sub(r"\s+", " ", text.replace("\r\n", "\n"))
        m = re.search(r"can be scheduled(.*?)A scheduled task can fire only", flat)
        if not m:
            self.err(readme, 1, "cannot find the schedulable list "
                     "('can be scheduled ... A scheduled task can fire only')")
            return
        listed = set(re.findall(r"`/([\w-]+)`", m.group(1)))
        actual = {n for n, f in commands.items()
                  if f.get("disable-model-invocation", ("", 0))[0].lower() not in TRUE}
        line = next((i for i, l in enumerate(text.splitlines(), 1) if "can be scheduled" in l), 1)
        for n in sorted(listed - actual):
            self.err(readme, line, f"/{n} is listed as schedulable but "
                     + ("does not exist" if n not in commands else "sets disable-model-invocation: true"))
        for n in sorted(actual - listed):
            self.err(readme, line, f"/{n} has no disable-model-invocation: true but is not in the list")

    # ---- driver -----------------------------------------------------------

    def run(self):
        r = self.root
        skill_files = sorted(r.glob("skills/*/SKILL.md")) + sorted(r.glob("plugins/*/skills/*/SKILL.md"))
        skills = {p.parent.name for p in r.glob("skills/*/SKILL.md")}
        for p in skill_files:
            self.check_refs(p, self.check_skill(p), skills)
        commands = {}
        for p in sorted(r.glob("commands/*.md")):
            if p.name == "README.md":
                continue
            fields, body = self.check_command(p)
            if fields is not None:
                commands[p.stem] = fields
            self.check_refs(p, body, skills)
        for p in sorted(r.glob("agents/*.md")):
            if p.name != "README.md":
                self.check_refs(p, self.check_agent(p, False), skills)
        for p in sorted(r.glob("plugins/*/agents/*.md")):
            if p.name != "README.md":
                self.check_agent(p, True)
        self.check_marketplace()
        self.check_plugin_manifests()
        self.check_schedulable(commands)
        return self.problems


def check_kit(root):
    return Checker(root).run()


# ---- selftest -------------------------------------------------------------

GOOD = {
    "skills/second-brain-a/SKILL.md": "---\nname: second-brain-a\ndescription: >-\n  Does a.\n  More.\n---\n\nBody scripts/tool.py\n",
    "plugins/p/skills/s/SKILL.md": "---\nname: s\ndescription: S.\n---\nBody\n",
    "commands/one.md": "---\r\ndescription: One\r\nargument-hint: \"[x]\"\r\ndisable-model-invocation: true\r\n---\r\n\r\nDo $ARGUMENTS. Follow `second-brain-a`.\r\n",
    "commands/two.md": "---\ndescription: Two\n---\nNo args.\n",
    "commands/README.md": "# c\n\nThe maintenance set can be scheduled and run: `/two`. A scheduled task can fire only these.\n",
    "agents/ag.md": "---\nname: ag\ndescription: Agent.\ntools: Read\n---\nBody\n",
    "agents/README.md": "# agents\n",
    "plugins/p/agents/pa.md": "---\nname: pa\ndescription: Plugin agent.\n---\nBody\n",
    "plugins/p/.claude-plugin/plugin.json": '{"name": "p", "version": "1.0.0"}',
    ".claude-plugin/marketplace.json": '{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "p", "source": "./plugins/p"}]}',
    "scripts/tool.py": "",
}


def selftest():
    failures = []

    def make(tmp, overrides):
        files = dict(GOOD)
        files.update(overrides)
        for rel, content in files.items():
            if content is None:
                continue
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode("utf-8"))

    def case(label, overrides, expect):
        tmp = Path(tempfile.mkdtemp())
        try:
            make(tmp, overrides)
            out = check_kit(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        hit = any(expect in line for line in out) if expect else not out
        if not hit:
            failures.append(f"{label}: expected {expect or 'no problems'!r}, got {out}")

    case("good kit passes (CRLF command included)", {}, None)
    case("no frontmatter", {"commands/two.md": "Body\n"}, "missing opening")
    case("unclosed frontmatter", {"commands/two.md": "---\ndescription: x\nBody\n"}, "never closed")
    case("bad line", {"commands/two.md": "---\ndescription: x\njunk line\n---\n"}, "not a 'key: value'")
    case("unknown key", {"commands/two.md": "---\ndescription: x\nbogus: 1\n---\n"}, "unknown frontmatter key 'bogus'")
    case("name not allowed in commands", {"commands/two.md": "---\nname: two\ndescription: x\n---\n"}, "unknown frontmatter key 'name'")
    case("missing description", {"commands/two.md": "---\nmodel: x\n---\n"}, "missing required field 'description'")
    case("skill name mismatch", {"skills/second-brain-a/SKILL.md": "---\nname: other\ndescription: d\n---\n"}, "does not match folder")
    case("skill missing name", {"skills/second-brain-a/SKILL.md": "---\ndescription: d\n---\n"}, "missing required field 'name'")
    case("description too long", {"skills/second-brain-a/SKILL.md": "---\nname: second-brain-a\ndescription: " + "x" * 1537 + "\n---\n"}, "limit 1536")
    case("description at limit", {"skills/second-brain-a/SKILL.md": "---\nname: second-brain-a\ndescription: " + "x" * 1536 + "\n---\n"}, None)
    case("agent missing name", {"agents/ag.md": "---\ndescription: d\n---\n"}, "missing required field 'name'")
    case("agent unknown key", {"agents/ag.md": "---\nname: ag\ndescription: d\nallowed-tools: x\n---\n"}, "unknown frontmatter key")
    case("plugin agent ignored key", {"plugins/p/agents/pa.md": "---\nname: pa\ndescription: d\npermissionMode: plan\n---\n"}, "plugin agents ignore")
    case("missing skill ref", {"commands/two.md": "---\ndescription: x\n---\nFollow `second-brain-zzz`.\n"}, "skill 'second-brain-zzz'")
    case("missing script ref", {"commands/two.md": "---\ndescription: x\n---\nRun scripts/nope.py\n"}, "scripts/nope.py")
    case("$ARGUMENTS without hint", {"commands/two.md": "---\ndescription: x\n---\n$ARGUMENTS\n"}, "no argument-hint")
    case("hint without $ARGUMENTS", {"commands/two.md": "---\ndescription: x\nargument-hint: y\n---\nbody\n"}, "never uses $ARGUMENTS")
    case("bad marketplace JSON", {".claude-plugin/marketplace.json": "{"}, "invalid JSON")
    case("marketplace missing owner", {".claude-plugin/marketplace.json": '{"name":"m","plugins":[{"name":"p","source":"./plugins/p"}]}'}, "owner.name")
    case("marketplace source missing", {".claude-plugin/marketplace.json": '{"name":"m","owner":{"name":"o"},"plugins":[{"name":"p","source":"./plugins/zz"}]}'}, "not a directory")
    case("marketplace source escapes", {".claude-plugin/marketplace.json": '{"name":"m","owner":{"name":"o"},"plugins":[{"name":"p","source":"./../x"}]}'}, "leaves the repository")
    case("plugin.json missing name", {"plugins/p/.claude-plugin/plugin.json": "{}"}, "'name' is required")
    case("schedulable list extra", {"commands/README.md": "can be scheduled `/two`, `/one`. A scheduled task can fire only"}, "/one is listed as schedulable but sets")
    case("schedulable list missing", {"commands/README.md": "can be scheduled none. A scheduled task can fire only"}, "/two has no disable")
    for f in failures:
        print("FAIL", f)
    print("selftest:", "FAILED" if failures else "ok")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    problems = check_kit(args.root)
    for p in problems:
        print(p)
    print(f"check_kit: {len(problems)} problem(s)" if problems else "check_kit: ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
