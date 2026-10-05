#!/usr/bin/env python3
"""Claude Code hook that enforces the vault's hard stops (stdlib only).

Registered in .claude/settings.json for two events:

  PreToolUse  Write|Edit|MultiEdit|NotebookEdit and Bash|PowerShell
              Exit 2 blocks the call and sends stderr to the agent.
              Exit 0 lets the normal permission flow decide.
  Stop        Warns (does not block) when the run ends with uncommitted
              changes, as a JSON systemMessage on stdout.

What it blocks:
  - changing an existing file under raw/ (new files are allowed)
  - any write under journal/ or .claude/ (settings, hooks, skills, commands, agents)
  - CLAUDE.md edits outside the "## Profile" block
  - shell commands that delete files, discard work, push, add remotes,
    rewrite history, upload data with curl or wget, or stage raw/workspace/
  - shell writes (redirects, tee, sed -i, mv, cp, truncate) to those places

It is a safety net, not a sandbox. It reads the command text, so a script that
deletes files from inside (for example `python3 x.py`) is not seen. For
OS-level enforcement use Claude Code's sandbox.

Hook protocol: https://code.claude.com/docs/en/hooks
Permission rule syntax: https://code.claude.com/docs/en/permissions
"""
import json
import os
import re
import subprocess
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

DELETE_CMDS = {"rm", "rmdir", "unlink", "shred", "del", "erase", "rd",
               "remove-item", "ri", "rimraf", "trash"}
WRAPPERS = {"sudo", "doas", "command", "builtin", "env", "nohup", "time",
            "exec", "xargs", "nice", "stdbuf", "timeout", "setsid", "ionice"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "pwsh", "powershell"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                       "--exec-path", "--super-prefix"}

BLOCK_MSG = "Blocked by vault guard (.claude/hooks/guard.py): "


class Block(Exception):
    pass


# --------------------------------------------------------------- paths

def norm(p):
    return os.path.normcase(os.path.realpath(p))


def rel_to_root(path, cwd, root):
    """Path relative to the vault root with '/' separators, or None if outside."""
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        p = os.path.join(cwd, p)
    real, base = norm(p), norm(root)
    try:
        if os.path.commonpath([real, base]) != base:
            return None
    except ValueError:  # different drives on Windows
        return None
    r = os.path.relpath(real, base).replace(os.sep, "/")
    return "" if r == "." else r


# ------------------------------------------------------- file tool rules

def profile_span(content):
    m = re.search(r"(?m)^## Profile\s*$", content)
    if not m:
        return None
    nxt = re.search(r"(?m)^## ", content[m.end():])
    end = m.end() + nxt.start() if nxt else len(content)
    return m.start(), end


def apply_edits(content, edits):
    for e in edits:
        old = e.get("old_string", e.get("old_str"))
        new = e.get("new_string", e.get("new_str"))
        if not isinstance(old, str) or not isinstance(new, str) or old not in content:
            raise Block("the edit does not match the current CLAUDE.md text")
        if e.get("replace_all"):
            content = content.replace(old, new)
        else:
            content = content.replace(old, new, 1)
    return content


def check_claude_md(tool, tool_input, real_path):
    if tool == "NotebookEdit":
        raise Block("CLAUDE.md is not a notebook")
    try:
        with open(real_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        raise Block("CLAUDE.md can only be edited inside its Profile block")
    span = profile_span(content)
    if span is None:
        raise Block("CLAUDE.md has no '## Profile' block, so no edit is allowed")
    if tool == "Write":
        new = tool_input.get("content", tool_input.get("file_text"))
        if not isinstance(new, str):
            raise Block("cannot read the new CLAUDE.md content")
    elif tool == "MultiEdit":
        new = apply_edits(content, tool_input.get("edits") or [])
    else:
        new = apply_edits(content, [tool_input])
    pre, post = content[:span[0]], content[span[1]:]
    middle_ok = (len(new) >= len(pre) + len(post) and new.startswith(pre)
                 and new.endswith(post))
    middle = new[len(pre):len(new) - len(post)]
    # the Profile heading itself must survive; no other heading may appear
    if (not middle_ok or not re.match(r"## Profile[ \t]*\n", middle)
            or re.search(r"(?m)^## ", middle[len("## Profile"):])):
        raise Block("CLAUDE.md may only change inside its Profile block "
                    "(hard stop e). Propose other changes in the run report.")


def check_path(tool, path, tool_input, cwd, root):
    """Raise Block if `tool` may not write `path`. tool 'Bash' means no
    content-level checks are possible, so CLAUDE.md is fully blocked."""
    r = rel_to_root(path, cwd, root)
    if r is None:
        return
    first = r.split("/")[0].lower()
    real = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    if first == ".claude":
        raise Block(f"'{r}' is agent configuration (settings, hooks, skills, "
                    "commands, agents). Only the owner changes it (hard stop e).")
    if first == "journal":
        raise Block(f"'{r}' is the owner's journal, read-only for the agent. "
                    "Put your writing on a wiki page.")
    if r.lower() == "claude.md":
        if tool == "Bash":
            raise Block("CLAUDE.md cannot be changed from a shell command "
                        "(hard stop e).")
        check_claude_md(tool, tool_input, real)
        return
    if first == "raw" and os.path.isfile(real):
        raise Block(f"'{r}' already exists in raw/, which is never edited, "
                    "renamed or overwritten. Write a new file beside it "
                    "(for example <name>-clean.md).")


# ----------------------------------------------------------- shell parsing

def split_commands(cmd):
    """Quote-aware split into command segments, each a list of tokens.
    Separators: ; & | newline ( ) { } and the openers of $( and backticks."""
    segs, toks, cur = [], [], []
    quote = None
    i, n = 0, len(cmd)

    def end_tok():
        if cur:
            toks.append("".join(cur))
            cur.clear()

    def end_seg():
        end_tok()
        if toks:
            segs.append(list(toks))
            toks.clear()

    while i < n:
        c = cmd[i]
        if quote:
            if c == quote:
                quote = None
            else:
                cur.append(c)
        elif c in "\"'":
            quote = c
            cur.append("")  # keep empty-string tokens alive
        elif c in " \t":
            end_tok()
        elif c in ";|\n(){}`":
            end_seg()
        elif c == "&":
            prev = cmd[i - 1] if i else ""
            nxt = cmd[i + 1] if i + 1 < n else ""
            if prev == ">" or nxt == ">":
                cur.append(c)  # 2>&1, &>
            else:
                end_seg()
        elif c == "$" and i + 1 < n and cmd[i + 1] == "(":
            end_seg()
            i += 1
        else:
            cur.append(c)
        i += 1
    end_seg()
    return segs


def inner_strings(cmd):
    """Text inside $( ), backticks and double quotes, so nested commands are checked."""
    found = re.findall(r"\$\(([^()]*)\)", cmd) + re.findall(r"`([^`]*)`", cmd)
    return found


def strip_prefix(tokens):
    """Drop VAR=value assignments and wrapper commands (sudo, env, xargs ...)."""
    t = list(tokens)
    while t:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t[0]):
            t.pop(0)
        elif os.path.basename(t[0]).lower().removesuffix(".exe") in WRAPPERS:
            w = os.path.basename(t[0]).lower()
            t.pop(0)
            while t and t[0].startswith("-"):
                t.pop(0)
            if w == "timeout" and t and re.match(r"^\d", t[0]):
                t.pop(0)
        else:
            break
    return t


def cmd_name(tokens):
    return os.path.basename(tokens[0]).lower().removesuffix(".exe")


def paths_in_segment(tokens):
    return [t for t in tokens[1:] if t and not t.startswith("-")]


# ------------------------------------------------------------ shell rules

def under_workspace(tok, cwd, root):
    """True if a git pathspec token names raw/workspace (or could glob into it)."""
    if tok.startswith(":"):
        return True  # pathspec magic: cannot be evaluated, refuse
    if re.search(r"[*?\[]", tok):
        lit = re.split(r"[*?\[]", tok, 1)[0].replace("\\", "/")
        r = rel_to_root(lit or ".", cwd, root)
        if r is None:
            return False
        prefix = (r.lower() + "/") if r else ""
        return "raw/workspace/".startswith(prefix) or prefix.startswith("raw/workspace/")
    r = rel_to_root(tok, cwd, root)
    if r is None:
        return False
    r = r.lower()
    return r == "raw/workspace" or r.startswith("raw/workspace/")


def check_git(args, cwd, root):
    a = list(args)
    while a and a[0].startswith("-"):
        opt = a.pop(0)
        if opt in GIT_OPTS_WITH_VALUE and a:
            a.pop(0)
    if not a:
        return
    sub, rest = a[0].lower(), a[1:]
    flags = [x for x in rest if x.startswith("-")]
    pos = [x for x in rest if not x.startswith("-")]
    if sub == "push":
        raise Block("git push (hard stop a). The vault is never pushed by the agent.")
    if sub == "remote" and pos and pos[0].lower() in {"add", "set-url"}:
        raise Block("adding or repointing a git remote (hard stop a).")
    if sub == "reset" and ("--hard" in flags or "--merge" in flags):
        raise Block("git reset --hard discards work (hard stop c). Use git revert.")
    if sub in {"clean", "rm", "rebase", "filter-branch", "filter-repo"}:
        raise Block(f"git {sub} deletes files or rewrites history (hard stop c).")
    if sub in {"checkout", "restore"} and (
            any(p in {".", "*", ":/"} for p in pos)
            or "-f" in flags or "--force" in flags):
        raise Block(f"git {sub} would discard working-tree changes (hard stop c).")
    if sub in {"add", "stage"}:
        bad = {"-A", "--all", "-f", "--force", "-u", "--update"}
        if any(f in bad for f in flags):
            raise Block("stage by explicit path only: no -A, -u or -f (rail 5).")
        if any(p in {".", "*", ":/", "raw", "raw/"} for p in pos):
            raise Block("stage by explicit path: not '.', '*' or the whole raw/ "
                        "folder (rail 5; raw/workspace/ is never staged).")
    if sub == "commit":
        if "--all" in flags or any(re.match(r"^-[A-Za-z]*a[A-Za-z]*$", f) and not f.startswith("--")
                                   for f in flags):
            raise Block("git commit -a stages every tracked change; stage the "
                        "run's own paths by name (rail 5).")
    if sub == "mv":
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    if sub in {"add", "stage", "commit", "mv", "update-index", "stash"}:
        if any(under_workspace(p, cwd, root) for p in pos):
            raise Block("raw/workspace/ holds other people's words and is never "
                        "staged or committed (hard stop b).")


def check_net(name, args):
    flags = [x for x in args if x.startswith("-")]
    low = [x.lower() for x in args]
    if name == "curl":
        for i, f in enumerate(args):
            if f.startswith("--"):
                key = f.split("=", 1)[0].lower()
                if key in {"--data", "--data-raw", "--data-binary", "--data-ascii",
                           "--data-urlencode", "--form", "--form-string",
                           "--upload-file", "--json"}:
                    raise Block("curl upload flag (hard stop b).")
                if key == "--request" and _method_bad(args, i, f):
                    raise Block("curl with a non-GET method (hard stop b).")
            elif f.startswith("-") and len(f) > 1 and f[1:2].isalpha():
                cluster = f[1:]
                if re.search(r"[dFT]", cluster.split("X")[0] if "X" in cluster else cluster):
                    raise Block("curl upload flag (hard stop b).")
                if "X" in cluster and _method_bad(args, i, f):
                    raise Block("curl with a non-GET method (hard stop b).")
    elif name == "wget":
        for f in low:
            key = f.split("=", 1)[0]
            if key in {"--post-data", "--post-file", "--body-data", "--body-file"}:
                raise Block("wget upload flag (hard stop b).")
            if key == "--method" and "=" in f and f.split("=", 1)[1] not in {"get", "head"}:
                raise Block("wget with a non-GET method (hard stop b).")
        for i, f in enumerate(low):
            if f == "--method" and i + 1 < len(low) and low[i + 1] not in {"get", "head"}:
                raise Block("wget with a non-GET method (hard stop b).")


def _method_bad(args, i, flag):
    if "=" in flag:
        val = flag.split("=", 1)[1]
    elif flag.endswith("X") or flag == "--request":
        val = args[i + 1] if i + 1 < len(args) else ""
    else:
        val = flag[flag.index("X") + 1:]
    return val.upper() not in {"GET", "HEAD"}


def redirect_targets(tokens):
    out = []
    for i, t in enumerate(tokens):
        m = re.match(r"^(?:\d*|&)>>?(.*)$", t)
        if not m:
            continue
        target = m.group(1) or (tokens[i + 1] if i + 1 < len(tokens) else "")
        if target and not target.startswith("&") and target != "/dev/null":
            out.append(target)
    return out


def check_segment(tokens, cwd, root, depth):
    for target in redirect_targets(tokens):
        check_path("Bash", target, {}, cwd, root)
    t = strip_prefix(tokens)
    if not t:
        return
    name = cmd_name(t)
    args = t[1:]
    pos = paths_in_segment(t)

    if name in DELETE_CMDS:
        raise Block(f"'{name}' deletes files (hard stop c). Archive instead: "
                    "move the page to archive/ keeping its path.")
    if name == "find" and ("-delete" in args or any(
            a in {"-exec", "-execdir", "-ok"} and i + 1 < len(args)
            and os.path.basename(args[i + 1]).lower() in DELETE_CMDS
            for i, a in enumerate(args))):
        raise Block("find -delete or -exec rm deletes files (hard stop c).")
    if name == "rsync" and any(a.startswith(("--delete", "--remove-source")) for a in args):
        raise Block("rsync --delete deletes files (hard stop c).")
    if name == "git":
        check_git(args, cwd, root)
    if name in {"curl", "wget"}:
        check_net(name, args)
    if name in SHELLS and depth < 3:
        for i, a in enumerate(args):
            if a.lower() in {"-c", "-command", "-encodedcommand"} and i + 1 < len(args):
                check_shell(args[i + 1], cwd, root, depth + 1)
    if name == "eval" and depth < 3:
        check_shell(" ".join(args), cwd, root, depth + 1)
    if name.startswith("python") and "-c" in args:
        code = " ".join(args[args.index("-c") + 1:])
        if re.search(r"\b(rmtree|os\.remove|os\.unlink|os\.rmdir|\.unlink\(|\.rmdir\()", code):
            raise Block("python one-liner that deletes files (hard stop c).")
    # writes to protected places
    if name == "tee":
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    elif name in {"sed", "perl", "ruby"} and any(
            a == "--in-place" or a.startswith("--in-place=") or re.match(r"^-[A-Za-z]*i", a)
            for a in args if a.startswith("-")):
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    elif name in {"mv", "move", "move-item", "mi", "ren", "rename"}:
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    elif name in {"cp", "copy", "copy-item", "cpi", "install", "ln"} and pos:
        check_path("Bash", pos[-1], {}, cwd, root)
    elif name in {"truncate", "dd"}:
        for p in pos:
            check_path("Bash", p.split("=", 1)[-1], {}, cwd, root)


def check_shell(cmd, cwd, root, depth=0):
    for inner in inner_strings(cmd):
        if depth < 3:
            check_shell(inner, cwd, root, depth + 1)
    for seg in split_commands(cmd):
        check_segment(seg, cwd, root, depth)


# ------------------------------------------------------------------- main

def pre_tool_use(data):
    tool = data.get("tool_name", "")
    tin = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    if tool in WRITE_TOOLS:
        if tool == "MultiEdit" and not tin.get("file_path"):
            paths = {e.get("file_path") for e in tin.get("edits") or []}
        else:
            paths = {tin.get("file_path") or tin.get("notebook_path")}
        paths.discard(None)
        if not paths:
            raise Block("no file path in the tool input")
        for p in paths:
            check_path(tool, p, tin, cwd, root)
    elif tool in SHELL_TOOLS:
        check_shell(tin.get("command") or "", cwd, root)


def stop(data):
    cwd = data.get("cwd") or os.getcwd()
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True,
                             text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError):
        return
    lines = [l for l in out.splitlines() if l.strip()]
    if lines:
        shown = ", ".join(l[3:] for l in lines[:8]) + (" ..." if len(lines) > 8 else "")
        msg = (f"{len(lines)} path(s) are not committed: {shown}. Rail 5: one run "
               "commit, staging only this run's paths by name. Anything you did "
               "not write yourself is the owner's edit; leave it out.")
        print(json.dumps({"systemMessage": msg}))


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.stderr.write(BLOCK_MSG + "could not read the hook input.\n")
        return 2
    try:
        if data.get("hook_event_name") == "Stop":
            stop(data)
        else:
            pre_tool_use(data)
    except Block as b:
        sys.stderr.write(BLOCK_MSG + str(b) + "\n")
        return 2
    except Exception as e:  # fail closed: a guard that crashes must not wave things through
        if data.get("hook_event_name") == "Stop":
            return 0  # the Stop hook only warns; never trap the agent in a loop
        sys.stderr.write(BLOCK_MSG + f"internal error ({e!r}); refusing.\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
