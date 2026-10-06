#!/usr/bin/env python3
"""Claude Code hook that enforces the vault's hard stops (stdlib only).

Registered in .claude/settings.json for two events:

  PreToolUse  Write|Edit|MultiEdit|NotebookEdit, Bash|PowerShell, and
              WebFetch|WebSearch|mcp__.*
              Exit 2 blocks the call and sends stderr to the agent.
              Exit 0 lets the normal permission flow decide.
  Stop        Warns (does not block) when the run ends with uncommitted
              changes, as a JSON systemMessage on stdout.

What it blocks:
  - changing an existing file under raw/ (new files are allowed)
  - any write under journal/, scripts/, .obsidian/ or .claude/ (settings, hooks,
    skills, commands, agents, the audit log), all owner-maintained
  - writing a credential (GitHub, AWS, Anthropic, OpenAI-style, Slack, Stripe
    keys, private key blocks) into a file or a shell redirect (hard stop d)
  - git mv into archive/ of a page with uncommitted changes (rail 1)
  - CLAUDE.md edits outside the "## Profile" block
  - shell commands that delete files, discard work, push, add remotes,
    rewrite history, upload data with curl or wget, or stage raw/workspace/
  - shell writes (redirects, tee, sed -i, mv, cp, git mv, truncate, PowerShell
    Set-Content and friends) to those places, and moves or copies that leave the
    vault or clobber protected pages
  - pages marked `sensitivity: restricted` leaving the vault: a verbatim excerpt
    of 200 or more characters headed for output/, a path outside the vault, a
    web request or an MCP tool; and shell commands that copy, pipe or send such a
    page (see the "sensitivity: restricted" section below for exact limits)

Every block appends one JSON line {ts, tool, rule, target} to .claude/guard.log
(rotated at about 1 MB to guard.log.1). It holds a rule name and a path or the
tool name, never a command, a secret or an excerpt. The guard also refuses any
write to the log, its rotation and its cache, so the agent cannot edit it.

It is a safety net, not a sandbox. It reads the command text, so a script that
deletes files from inside (for example `python3 x.py`) is not seen; one-liners
(`python3 -c`, `node -e`, `perl -e`, `ruby -e`, `php -r`, `deno eval`) are
matched by pattern only. For OS-level enforcement use Claude Code's sandbox.

Hook protocol: https://code.claude.com/docs/en/hooks
Permission rule syntax: https://code.claude.com/docs/en/permissions
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
import zlib

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

DELETE_CMDS = {"rm", "rmdir", "unlink", "shred", "del", "erase", "rd",
               "remove-item", "ri", "rimraf", "trash"}
WRAPPERS = {"sudo", "doas", "command", "builtin", "env", "nohup", "time",
            "exec", "xargs", "nice", "stdbuf", "timeout", "setsid", "ionice"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "pwsh", "powershell"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                       "--exec-path", "--super-prefix", "--config-env"}
# Owner-maintained: the agent may not write here at all.
# .obsidian is Obsidian's own settings folder.
OWNER_DIRS = frozenset({".claude", "journal", "scripts", ".obsidian"})
# Never moved away or archived (rail 2), and never overwritten once they exist.
KEEP_PAGES = ["wiki/systems", "wiki/hubs", "wiki/index.md", "wiki/log.md"]
# A source of a move may not be (or contain) any of these.
MOVE_SOURCE_BLOCKED = ["raw", "archive", "journal", ".claude", "scripts", ".obsidian",
                       "claude.md", ".gitignore"] + KEEP_PAGES
MOVE_CMDS = {"mv", "move", "move-item", "mi", "rename-item", "rni", "ren", "rename"}
RENAME_CMDS = {"rename-item", "rni", "ren", "rename"}
COPY_CMDS = {"cp", "copy", "copy-item", "cpi", "copy-item", "install", "ln"}
PS_WRITE_CMDS = {"set-content", "sc", "out-file", "add-content", "ac", "clear-content",
                 "clc", "new-item", "ni", "mkdir", "md"}
WEB_CMDS = {"invoke-webrequest", "iwr", "invoke-restmethod", "irm", "curl", "wget"}
PS_WEB_FLAGS = {"headers", "header", "uri", "outfile", "method", "useb", "usebasicparsing",
                "contenttype", "timeoutsec", "credential", "proxy", "useragent",
                "maximumredirection", "skipcertificatecheck", "body", "infile", "form"}

# Hard stop (d): credentials never go into a file. To adjust, edit
# SECRET_PATTERNS (each is (kind, regex)); to turn the check off, set
# SECRET_CHECK = False. The message names the kind, never the value.
SECRET_CHECK = True
SECRET_PATTERNS = [
    ("a GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    ("a GitHub token", r"\bgithub_pat_[A-Za-z0-9_]{40,}"),
    ("an AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("an Anthropic API key", r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    ("an API key (sk-)", r"\bsk-[A-Za-z0-9]{20,}"),
    ("an API key (sk-)", r"\bsk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]{20,}"),
    ("a private key", r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----\s+(?:[A-Za-z0-9+/]{40,}|Proc-Type)"),
    ("a Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
    ("a Slack webhook URL", r"hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{20,}"),
    ("a Stripe live key", r"\b[spr]k_live_[A-Za-z0-9]{20,}"),
]
# A match containing one of these is a documented placeholder, not a credential.
# Words count only when set off by -, _ or the ends; ALL-CAPS markers count anywhere.
SECRET_PLACEHOLDER = re.compile(
    r"(?i:(?<![A-Za-z0-9])(fake|demo|example|placeholder|redacted|dummy|sample|your)(?![A-Za-z0-9]))|"
    r"EXAMPLE|REDACTED|PLACEHOLDER|(?i:x{4,})|0{4,}|\*{3,}|\.{3,}")

BLOCK_MSG = "Blocked by vault guard (.claude/hooks/guard.py): "


class Block(Exception):
    """A refusal. `rule` names the rule for the audit log; when it is None the
    message is classified (RULE_PATTERNS). `target` is the path that triggered it."""

    def __init__(self, msg, rule=None, target=None):
        super().__init__(msg)
        self.rule, self.target = rule, target


# Rule names for the audit log (.claude/guard.log), matched against the message.
# The log records the rule name and a path or tool name, never the message text.
RULE_PATTERNS = [
    (r"audit log", "audit-log"),
    (r"not a git repository|uncommitted changes|could not run git status", "archive-checkpoint"),
    (r"^'?CLAUDE\.md|CLAUDE\.md (may|can|has|is|cannot)|the edit does not match", "claude-md"),
    (r"\.gitignore", "gitignore"),
    (r"owner-maintained configuration", "owner-config"),
    (r"owner's journal", "journal"),
    (r"already exists in raw/", "raw-append-only"),
    (r"glob, brace or variable|cannot tell where|cannot be checked|cannot check", "unresolvable-path"),
    (r"git -c |git config|GIT_CONFIG", "git-config"),
    (r"sends the vault out|git remote|adding or repointing", "push-or-remote"),
    (r"uploads data|upload flag|non-GET", "upload"),
    (r"outside the vault", "outside-vault"),
    (r"protected path|system, hub, index or log", "protected-move"),
    (r"pathspec|never staged|stage by explicit|stages every tracked", "staging"),
    (r"deletes files|one-liner that deletes|find -delete", "delete"),
    (r"git (reset|revert|checkout|restore|clean|rm|rebase|commit|mv)|amending|--no-verify|rewrites history", "git-destructive"),
    (r"PowerShell -EncodedCommand|no file path|internal error", "unreadable-input"),
]
LOG_MAX = 1_000_000


def classify(msg):
    for pat, name in RULE_PATTERNS:
        if re.search(pat, msg):
            return name
    return "other"


# --------------------------------------------------------------- paths

def jp(cwd, p):
    """Join for a path that rel_to_root has already accepted: when the working
    directory is unknown (None) the path is absolute, so the join is the path."""
    return os.path.join(cwd or "", p)


def norm(p):
    return os.path.normcase(os.path.realpath(p))


def rel_to_root(path, cwd, root):
    """Path relative to the vault root with '/' separators, or None if outside."""
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        if cwd is None:
            raise Block(f"cannot tell where '{path}' points: an earlier cd could not be "
                        "followed. Use a path from the vault root, or an absolute one.")
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
        old = e.get("old_string", e.get("old_str", e.get("original_text")))
        new = e.get("new_string", e.get("new_str", e.get("new_text")))
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


def find_secret(text):
    """Kind of the first credential-looking string in text, or None."""
    if not SECRET_CHECK or not isinstance(text, str):
        return None
    for kind, pat in SECRET_PATTERNS:
        for m in re.finditer(pat, text):
            if not SECRET_PLACEHOLDER.search(m.group(0)):
                return kind
    return None


def check_secrets(texts):
    for t in texts:
        kind = find_secret(t)
        if kind:
            raise Block(f"the content contains {kind} (hard stop d). Never write "
                        "credentials into a file: leave it out and report the file "
                        "and kind to the owner.", rule="secret")


def written_texts(tool, tin):
    """Every piece of new text a file tool would write."""
    out = [tin.get("content"), tin.get("file_text"), tin.get("new_string"),
           tin.get("new_str"), tin.get("new_text"), tin.get("new_source")]
    for e in tin.get("edits") or []:
        if isinstance(e, dict):
            out += [e.get("new_string"), e.get("new_str"), e.get("new_text")]
    return [x for x in out if isinstance(x, str)]


def check_path(tool, path, tool_input, cwd, root):
    """Raise Block if `tool` may not write `path`. tool 'Bash' means no
    content-level checks are possible, so CLAUDE.md is fully blocked."""
    if tool == "Bash" and FUZZY.search(path):
        full, _ = lit_rel(path, cwd, root)
        if full is not None and any(
                overlaps(full, p) for p in OWNER_DIRS | {"raw", "claude.md", ".gitignore"}):
            raise Block(f"'{path}' uses a glob, brace or variable and may write to a "
                        "protected path (raw/, journal/, scripts/, .claude/, CLAUDE.md); "
                        "name the file exactly.")
        return
    r = rel_to_root(path, cwd, root)
    if r is None:
        return
    first = r.split("/")[0].lower()
    real = os.path.realpath(jp(cwd, os.path.expanduser(path)))
    if r.lower() == ".gitignore":
        raise Block(".gitignore is owner-maintained (it decides what is versioned).")
    if r.lower().startswith(".claude/guard"):
        # guard.log, guard.log.1 and the restricted-page cache: written by the hook only
        raise Block(f"'{r}' is the guard's audit log or cache. Only the hook writes it; "
                    "the agent never edits, moves or deletes it.", rule="audit-log")
    if first in {".claude", "scripts", ".obsidian"}:
        raise Block(f"'{r}' is owner-maintained configuration or tooling (settings, "
                    "hooks, skills, commands, agents, scripts, Obsidian settings). "
                    "Only the owner changes it (hard stop e).")
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
        elif c == "|" and i and cmd[i - 1] == ">":
            cur.append(c)  # the >| redirect
        elif c in "{}" and not cur and (
                i + 1 >= n or cmd[i + 1] in " \t;\n)"):
            end_seg()  # a standalone { or } group token, not a brace expansion
        elif c in "{}":
            cur.append(c)  # inside a token: wiki/{a,b}.md, ${VAR}
        elif c in ";|\n()`":
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
    cmd = mask_single_quoted(cmd)
    found = re.findall(r"\$\(([^()]*)\)", cmd) + re.findall(r"`([^`]*)`", cmd)
    return found


def mask_single_quoted(cmd):
    """Blank out text inside single quotes: the shell expands nothing there, so a
    backtick or $( in it is plain text. Double quotes and backslashes are tracked."""
    out, quote, i = [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if quote == "'":
            if c == "'":
                quote = None
                out.append(c)
            else:
                out.append(" ")
        elif c == "\\" and i + 1 < len(cmd):
            out.append(c + cmd[i + 1])
            i += 1
        elif quote == '"':
            if c == '"':
                quote = None
            out.append(c)
        else:
            if c in "\"'":
                quote = c
            out.append(c)
        i += 1
    return "".join(out)


SHELL_KEYWORDS = {"do", "then", "else", "elif", "if", "while", "until", "!", "coproc"}
WRAPPER_VALUE_FLAGS = {
    "nice": {"-n", "--adjustment"}, "sudo": {"-u", "-g", "-h", "-p", "-C", "-r", "-t", "-U"},
    "doas": {"-u", "-C"}, "env": {"-u", "-C", "-S"},
    "xargs": {"-n", "-I", "-L", "-P", "-d", "-E", "-s", "-a"},
    "timeout": {"-s", "-k"}, "stdbuf": {"-i", "-o", "-e"}, "ionice": {"-c", "-n", "-p"},
}


def strip_prefix_ex(tokens):
    """Drop VAR=value assignments, shell keywords and wrapper commands (sudo, env,
    xargs, nice ...). Returns (remaining tokens, assignments seen)."""
    t, assigns = list(tokens), []
    while t:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t[0]):
            assigns.append(t.pop(0))
        elif t[0] in SHELL_KEYWORDS:
            t.pop(0)
        elif os.path.basename(t[0]).lower().removesuffix(".exe") in WRAPPERS:
            w = os.path.basename(t[0]).lower().removesuffix(".exe")
            t.pop(0)
            while t and t[0].startswith("-"):
                f = t.pop(0)
                if f in WRAPPER_VALUE_FLAGS.get(w, ()) and t:
                    t.pop(0)
            while t and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t[0]):
                assigns.append(t.pop(0))  # env VAR=x cmd
            if w == "timeout" and t and re.match(r"^\d", t[0]):
                t.pop(0)
        else:
            break
    return t, assigns


def strip_prefix(tokens):
    return strip_prefix_ex(tokens)[0]


def cmd_name(tokens):
    return os.path.basename(tokens[0]).lower().removesuffix(".exe")


def paths_in_segment(tokens):
    return [t for t in tokens[1:] if t and not t.startswith("-")]


# ------------------------------------------------------------ shell rules

FUZZY = re.compile(r"[*?\[${]")


def lit_rel(tok, cwd, root):
    """(lowercase vault-relative path, fuzzy). For a token with a glob or a
    variable, the path is the literal prefix, so callers test prefix overlap.
    None when the path is outside the vault."""
    t = tok.replace("\\", "/") if os.sep == "\\" else tok
    m = FUZZY.search(t)
    if not m:
        r = rel_to_root(t, cwd, root)
        return (None if r is None else r.lower()), False
    lit = t[:m.start()]
    d, sep, part = lit.rpartition("/")
    base = (d + "/") if sep else "."
    r = rel_to_root(base, cwd, root)
    if r is None:
        return None, True
    return ((r + "/" if r else "") + part).lower(), True


def overlaps(full, prot):
    """True if a (possibly partial) path could be, sit inside or contain `prot`."""
    return full == prot or full.startswith(prot + "/") or prot.startswith(full)


def pathspec_blocked(tok, cwd, root):
    """git pathspecs that would stage the vault root, all of raw/, or raw/workspace/."""
    if tok.startswith(":"):
        return True  # pathspec magic cannot be evaluated: refuse
    full, fuzzy = lit_rel(tok, cwd, root)
    if full is None:
        return False
    if fuzzy:
        return overlaps(full, "raw/workspace")
    return (full in {"", "raw"} or full == "raw/workspace"
            or full.startswith("raw/workspace/"))


VALUE_FLAGS = {"-m", "-F", "-C", "-c", "--message", "--file", "--author", "--date",
               "--reuse-message", "--reedit-message", "--template", "--cleanup",
               "--trailer", "--fixup", "--squash", "--chmod", "--pathspec-from-file"}


def git_positionals(rest):
    pos, i, only_pos = [], 0, False
    while i < len(rest):
        t = rest[i]
        if only_pos:
            pos.append(t)
        elif t == "--":
            only_pos = True
        elif t.startswith("-") and len(t) > 1:
            cluster = re.fullmatch(r"-[A-Za-z]+", t)
            if t in VALUE_FLAGS or (cluster and t.endswith("m") and len(t) > 2):
                i += 1  # skip the flag's value (-m "msg", -am "msg")
        else:
            pos.append(t)
        i += 1
    return pos


def flag_letters(flags):
    letters = set()
    for f in flags:
        if re.fullmatch(r"-[A-Za-z]+", f):
            letters.update(f[1:])
    return letters


SAFE_GIT_C = re.compile(r"^(user\.|core\.quotepath$|color\.|log\.|diff\.renames$|commit\.gpgsign$)")
GIT_ENV_BLOCKED = re.compile(r"^(HOME=|XDG_CONFIG_HOME=|PATH=|GIT_CONFIG|GIT_DIR=|GIT_WORK_TREE=|GIT_SSH|GIT_EXEC_PATH=|"
                             r"GIT_INDEX_FILE=|GIT_COMMON_DIR=|GIT_PAGER=|GIT_EDITOR=)", re.I)
GIT_READ_CONFIG = {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l",
                   "--show-origin", "--show-scope", "--get-color", "--get-colorbool"}


def check_git(args, cwd, root):
    a = list(args)
    while a and a[0].startswith("-"):
        opt = a.pop(0)
        value = None
        if opt in GIT_OPTS_WITH_VALUE and a:
            value = a.pop(0)
        elif opt.startswith("-c") and len(opt) > 2:
            value = opt[2:]
        elif opt.startswith("--config-env=") or opt.startswith("--git-dir=") \
                or opt.startswith("--work-tree="):
            value = opt.split("=", 1)[1]
        if opt == "-C" and value is not None:
            if FUZZY.search(value):
                raise Block("git -C with a glob or variable cannot be checked.")
            if rel_to_root(value, cwd, root) is None:
                raise Block(f"git -C '{value}' points outside the vault.")
            cwd = jp(cwd, os.path.expanduser(value))
        elif opt.startswith(("--git-dir", "--work-tree")) and value is not None:
            if rel_to_root(value, cwd, root) is None:
                raise Block(f"git {opt.split('=')[0]} points outside the vault.")
        elif opt == "-c" or opt.startswith("-c") or opt.startswith("--config-env"):
            key = (value or "").split("=", 1)[0]
            if not SAFE_GIT_C.match(key.lower()):
                raise Block(f"git -c {key or '...'} is not on the short allowlist (user.*, "
                            "core.quotepath, color.*, log.*, diff.renames, commit.gpgsign); "
                            "other settings can run commands (hard stop c).")
    if not a:
        return
    sub, rest = a[0].lower(), a[1:]
    flags = [x for x in rest if x.startswith("-")]
    letters = flag_letters(flags)
    pos = git_positionals(rest)
    if sub in {"push", "send-pack", "imap-send", "send-email"} or (
            sub == "svn" and "dcommit" in rest):
        raise Block(f"git {sub} sends the vault out (hard stop a). The agent never "
                    "pushes or sends.")
    if sub == "config" and not (
            set(x.lower() for x in rest) & GIT_READ_CONFIG
            or any(x.lower().startswith("--get") for x in rest)
            or (pos and pos[0].lower() in {"get", "list"})
            or (len(pos) == 1 and set(flags) <= {"--global", "--local", "--system",
                                                  "--worktree"})):
        raise Block("git config may only read (get, list, --get, --list, --show-origin, "
                    "or one setting name); set, unset and edit can define aliases or "
                    "hooks (hard stop c).")
    if sub == "remote" and pos and pos[0].lower() in {"add", "set-url"}:
        raise Block("adding or repointing a git remote (hard stop a).")
    if sub == "reset" and ("--hard" in flags or "--merge" in flags):
        raise Block("git reset --hard discards work (hard stop c). Use git revert.")
    if sub == "revert" and "--abort" in flags:
        raise Block("git revert --abort discards later changes; use "
                    "git revert --quit (second-brain-rollback).")
    if sub in {"clean", "rm", "rebase", "filter-branch", "filter-repo"}:
        raise Block(f"git {sub} deletes files or rewrites history (hard stop c).")
    if sub in {"checkout", "restore"} and (
            any(p in {".", "*", ":/"} for p in pos)
            or "-f" in flags or "--force" in flags or "f" in letters):
        raise Block(f"git {sub} would discard working-tree changes (hard stop c).")
    if sub in {"add", "stage"}:
        if letters & {"A", "f", "u"} or any(
                f.split("=")[0] in {"--all", "--force", "--update"} for f in flags):
            raise Block("stage by explicit path only: no -A, -u or -f (rail 5).")
        if any(f.startswith("--pathspec-") for f in flags):
            raise Block("--pathspec-from-file hides the paths being staged (rail 5).")
    if sub == "commit":
        if "n" in letters or "--no-verify" in flags:
            raise Block("git commit --no-verify skips hooks (hard stop c).")
        if "a" in letters or "--all" in flags:
            raise Block("git commit -a stages every tracked change; stage the "
                        "run's own paths by name (rail 5).")
        if any(f == "--amend" or f.startswith(("--fixup", "--squash")) for f in flags):
            raise Block("amending or fixing up commits rewrites history (hard stop c); "
                        "make a new commit.")
        if any(f.startswith("--pathspec-") for f in flags):
            raise Block("--pathspec-from-file hides the paths being committed (rail 5).")
    if sub in {"add", "stage", "commit"}:
        for p in pos if sub != "commit" else [x for x in pos if x]:
            if pathspec_blocked(p, cwd, root):
                raise Block(f"pathspec '{p}' covers the vault root, all of raw/ or "
                            "raw/workspace/. Stage by explicit path; raw/workspace/ "
                            "is never staged (rail 5, hard stop b).")
    if sub in {"update-index", "stash"}:
        if any(pathspec_blocked(p, cwd, root) for p in pos):
            raise Block("raw/workspace/ is never staged (hard stop b).")
    if sub == "mv":
        if "-f" in flags or "--force" in flags or "f" in letters:
            raise Block("git mv --force can overwrite pages (hard stop c).")
        check_move("git mv", pos, [], cwd, root, is_move=True)


def check_archive_checkpoint(sources, dest, cwd, root):
    """Rail 1: a page moved into archive/ must be committed first. Fails closed
    when git cannot answer. The timeout stays under the hook's own 10 seconds."""
    dfull, _ = lit_rel(dest, cwd, root)
    if dfull is None or dfull.split("/")[0] != "archive":
        return
    for s in sources:
        spec = s if FUZZY.search(s) else ":(literal)" + os.path.join(cwd or "", os.path.expanduser(s))
        try:
            p = subprocess.run(["git", "status", "--porcelain", "--", spec], cwd=root,
                               capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):  # includes TimeoutExpired
            raise Block("could not run git status to check for uncommitted changes "
                        "before archiving; commit the checkpoint first (rail 1).")
        if p.returncode != 0:
            raise Block("this vault is not a git repository, or has no commit. Archive "
                        "nothing; queue it in wiki/systems/needs-owner.md (rail 1).")
        if p.stdout.strip():
            raise Block(f"'{s}' has uncommitted changes: commit the checkpoint "
                        "first (rail 1), then move it into archive/.")


PS_PARAMS = ("method", "body", "infile")


def ps_param(f):
    """Canonical PowerShell web parameter for a flag, allowing unambiguous prefixes
    (-Me, -Bod); None for anything else."""
    key = f.lower().split(":", 1)[0]
    if not key.startswith("-") or key.startswith("--") or len(key) < 3:
        return None
    key = key[1:]
    for p in PS_PARAMS:
        if p.startswith(key):
            return p
    return "form" if key == "form" else None


def check_net(name, args):
    low = [x.lower() for x in args]
    if name in WEB_CMDS:  # PowerShell Invoke-WebRequest / Invoke-RestMethod and aliases
        for i, f in enumerate(args):
            p = ps_param(f)
            if p in {"body", "infile", "form"}:
                raise Block(f"{name} -{p} uploads data (hard stop b).")
            if p == "method":
                val = f.split(":", 1)[1].lower() if ":" in f else (
                    low[i + 1] if i + 1 < len(low) else "")
                if val not in {"get", "head"}:
                    raise Block(f"{name} with a non-GET method (hard stop b).")
    if name == "curl":
        for i, f in enumerate(args):
            # PowerShell-style single-dash words (-Headers, -OutFile) are not curl clusters
            if (f.startswith("-") and not f.startswith("--")
                    and f[1:].lower() in PS_WEB_FLAGS and len(f) > 3):
                continue
            if f.startswith("--"):
                key = f.split("=", 1)[0].lower()
                if key in {"--data", "--data-raw", "--data-binary", "--data-ascii",
                           "--data-urlencode", "--form", "--form-string",
                           "--upload-file", "--json"}:
                    raise Block("curl upload flag (hard stop b).")
                if key == "--request" and _method_bad(args, i, f):
                    raise Block("curl with a non-GET method (hard stop b).")
            elif re.fullmatch(r"-[A-Za-z0-9]{1,8}[^\s]*", f) and f[1:2].isalpha():
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
        m = re.match(r"^(?:\d*|&)(?:>>|>\||>)(.*)$", t)
        if not m:
            continue
        target = m.group(1) or (tokens[i + 1] if i + 1 < len(tokens) else "")
        if target and not target.startswith("&") and target != "/dev/null":
            out.append(target)
    return out


def positionals(args, value_flags=()):
    pos, i = [], 0
    while i < len(args):
        t = args[i]
        if t == "--":
            pos.extend(args[i + 1:])
            break
        if t.startswith("-") and len(t) > 1:
            if t in value_flags:
                i += 1
        else:
            pos.append(t)
        i += 1
    return pos


def target_dir_option(args):
    for i, a in enumerate(args):
        if a in {"-t", "--target-directory"} and i + 1 < len(args):
            return args[i + 1]
        if a.startswith("--target-directory="):
            return a.split("=", 1)[1]
    return None


def check_move(name, pos, args, cwd, root, is_move):
    """mv, cp, git mv, install, ln, Move-Item, Copy-Item, Rename-Item.
    Every destination must be inside the vault. For a move, every source must be
    inside the vault and none may be (or contain) raw/, archive/, journal/,
    .claude/, scripts/, CLAUDE.md or the system, hub, index and log pages."""
    topt = target_dir_option(args)
    if name.split()[-1] in RENAME_CMDS and len(pos) == 2 and not re.search(r"[\\/]", pos[1]):
        pos = [pos[0], os.path.join(os.path.dirname(pos[0]), pos[1])]
    if topt is not None:
        dest, sources = topt, pos
    elif len(pos) >= 2:
        dest, sources = pos[-1], pos[:-1]
    else:
        return
    if is_move:
        for s in sources:
            full, fuzzy = lit_rel(s, cwd, root)
            if full is None:
                raise Block(f"'{s}' is outside the vault; moves must stay inside it. "
                            "Archive by moving into archive/ (use git mv).")
            for prot in MOVE_SOURCE_BLOCKED:
                if overlaps(full, prot) or (not fuzzy and prot.startswith(full + "/")):
                    raise Block(f"'{s}' is, or contains, a protected path ({prot}); "
                                "it is never moved or renamed (rail 2, hard stop c).")
    dfull, dfuzzy = lit_rel(dest, cwd, root)
    if dfull is None:
        raise Block(f"destination '{dest}' is outside the vault.")
    top = dfull.split("/")[0]
    if dfuzzy:
        if top in OWNER_DIRS or top == "raw" or dfull == "claude.md" or any(
                overlaps(dfull, k) for k in KEEP_PAGES):
            raise Block(f"destination '{dest}' cannot be checked and may overwrite "
                        "a protected path; name it exactly.")
        return
    if is_move:
        check_archive_checkpoint(sources, dest, cwd, root)
    dest_abs = os.path.realpath(jp(cwd, os.path.expanduser(dest)))
    is_dir = os.path.isdir(dest_abs) or dest.endswith(("/", "\\")) or topt is not None
    targets = []
    if is_dir:
        for s in sources:
            targets.append(os.path.join(dest, os.path.basename(s.rstrip("/\\")) or s))
    else:
        targets.append(dest)
    for t in targets:
        check_path("Bash", t, {}, cwd, root)
        tfull, _ = lit_rel(t, cwd, root)
        treal = os.path.realpath(jp(cwd, os.path.expanduser(t)))
        if tfull is not None and os.path.exists(treal) and any(
                overlaps(tfull, k) for k in KEEP_PAGES):
            raise Block(f"'{t}' is a system, hub, index or log page; it is never "
                        "overwritten by a move or copy.")


def decode_ps(b64):
    import base64
    try:
        return base64.b64decode(b64, validate=True).decode("utf-16-le")
    except (ValueError, UnicodeDecodeError):
        raise Block("could not decode a PowerShell -EncodedCommand; refusing.")


def nested_script(name, args):
    """The script text a shell invocation runs, or None."""
    low = [a.lower() for a in args]
    if name == "cmd":
        for i, a in enumerate(low):
            if a in {"/c", "/k", "/r"}:
                return " ".join(args[i + 1:])
        return None
    if name in {"pwsh", "powershell"}:
        for i, a in enumerate(low):
            if a in {"-e", "-ec", "-enc", "-encodedcommand"} and i + 1 < len(args):
                return decode_ps(args[i + 1])
            if a in {"-c", "-command"} and i + 1 < len(args):
                return " ".join(args[i + 1:])
        return None
    for i, a in enumerate(args):
        if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a):
            rest = [x for x in args[i + 1:] if x != "--"]
            if rest:
                return rest[0]
    return None


SCRIPT_INTERP = re.compile(r"^(node|nodejs|deno|bun|perl|ruby|php)[0-9.\-]*$")
SCRIPT_DELETE = re.compile(
    r"\b(rmSync|unlinkSync|rmdirSync|rmtree|remove_tree|rmdir|unlink|"
    r"File\.(delete|unlink)|FileUtils\.(rm|rm_r|rm_rf|rm_f|remove\w*)|Dir\.(rmdir|delete|unlink)|"
    r"fs\.(promises\.)?rm|fsPromises\.rm|promises\.rm|Deno\.remove(Sync)?)\b|"
    r"\.rm\s*\(|(?<![A-Za-z0-9_.])rm\s*\(", re.I)
# A one-liner that runs a shell command: blocked only if the text also deletes.
SCRIPT_SHELL = re.compile(r"\b(execSync|exec|execFile|spawnSync|spawn|system|popen|"
                          r"child_process)\b|%x[(\[{]|`", re.I)
SHELL_DELETE = re.compile(r"(?<![A-Za-z0-9_])(rm|rmdir|unlink|shred|del|erase|rimraf|trash|clean|mv|reset)"
                          r"(?![A-Za-z0-9_])|-delete\b", re.I)
SCRIPT_WRITE = re.compile(
    r"\b(writeFile(Sync)?|appendFile(Sync)?|createWriteStream|copyFile(Sync)?|"
    r"rename(Sync)?|file_put_contents|File\.(write|open|rename)|IO\.write|"
    r"Deno\.write\w*|open)\b", re.I)
PY_WRITE = re.compile(r"open\s*\([^)]*,\s*['\"][^'\"]*[wax+]|write_text|write_bytes|"
                     r"shutil\.(copy|move)|os\.(rename|replace|truncate)|\.touch\s*\(|\bwrite\s*\(")
PROTECTED_WORD = re.compile(r"raw|journal|scripts|\.claude|guard\.log|\.obsidian|claude\.md|\.gitignore|"
                            r"wiki[/\\](systems|hubs|index|log)", re.I)


def script_oneliner(name, args):
    """Code text of a node/deno/bun/perl/ruby/php one-liner, or None. Fuzzy on
    purpose: the whole argument list after the interpreter is searched."""
    if not SCRIPT_INTERP.match(name):
        return None
    base = re.sub(r"[0-9.\-]+$", "", name)
    if base == "deno":
        hit = "eval" in args
    elif base == "php":
        hit = any(a == "-r" or re.fullmatch(r"-[A-Za-z]*r", a) for a in args)
    elif base in {"perl", "ruby"}:
        hit = any(re.fullmatch(r"-[A-Za-z0-9]*[eE]", a) for a in args)
    else:  # node, bun
        hit = any(a in {"-e", "--eval", "-p", "--print"} or a.startswith(("--eval=", "--print="))
                  for a in args)
    return " ".join(args) if hit else None


def check_segment(tokens, cwd, root, depth):
    for target in redirect_targets(tokens):
        check_path("Bash", target, {}, cwd, root)
    for i, tok in enumerate(tokens):  # env -S "cmd args" runs a command line
        if os.path.basename(tok).lower().removesuffix(".exe") == "env":
            for j in range(i + 1, len(tokens)):
                f = tokens[j]
                script = None
                if f in {"-S", "--split-string"} and j + 1 < len(tokens):
                    script = tokens[j + 1]
                elif f.startswith("--split-string="):
                    script = f.split("=", 1)[1]
                elif f.startswith("-S") and len(f) > 2:
                    script = f[2:]
                if script and depth < 3:
                    check_shell(script, cwd, root, depth + 1)
            break
    t, assigns = strip_prefix_ex(tokens)
    if not t:
        return
    name = cmd_name(t)
    args = t[1:]
    pos = paths_in_segment(t)
    if _CTX:
        note_segment(tokens, name, args, pos, cwd, root)
    if (name == "git" or name.startswith("git-")) and any(
            GIT_ENV_BLOCKED.match(x) for x in assigns):
        raise Block("GIT_CONFIG*, GIT_DIR, GIT_WORK_TREE, GIT_SSH* and GIT_EXEC_PATH "
                    "change what git runs or where; not allowed (hard stop c).")

    if name.startswith("git-") and name[4:] in {"push", "send-pack", "imap-send",
                                                "send-email", "clean", "rm", "rebase"}:
        check_git([name[4:]] + args, cwd, root)
    if name in DELETE_CMDS:
        raise Block(f"'{name}' deletes files (hard stop c). Archive instead: "
                    "git mv the page into archive/ keeping its path.")
    if name == "find" and ("-delete" in args or any(
            a in {"-exec", "-execdir", "-ok"} and i + 1 < len(args)
            and os.path.basename(args[i + 1]).lower() in DELETE_CMDS
            for i, a in enumerate(args))):
        raise Block("find -delete or -exec rm deletes files (hard stop c).")
    if name == "rsync" and any(a.startswith(("--delete", "--remove-source")) for a in args):
        raise Block("rsync --delete deletes files (hard stop c).")
    if name == "git":
        check_git(args, cwd, root)
    if name in {"curl", "wget"} | WEB_CMDS:
        check_net(name, args)
    if (name in SHELLS or name == "cmd") and depth < 3:
        script = nested_script(name, args)
        if script:
            check_shell(script, cwd, root, depth + 1)
    if name == "eval" and depth < 3:
        check_shell(" ".join(args), cwd, root, depth + 1)
    if name.startswith("python") and "-c" in args:
        code = " ".join(args[args.index("-c") + 1:])
        if re.search(r"(?<![A-Za-z0-9_])(rmtree|os\.remove|os\.unlink|os\.rmdir)|\.unlink\s*\(|\.rmdir\s*\(", code):
            raise Block("python one-liner that deletes files (hard stop c).")
        if PY_WRITE.search(code) and PROTECTED_WORD.search(code):
            raise Block("python one-liner that writes to a protected path (raw/, journal/, "
                        "scripts/, .claude/ and the audit log, .obsidian/, CLAUDE.md).")
    code = script_oneliner(name, args)
    if code is not None:
        if SCRIPT_DELETE.search(code) or (SCRIPT_SHELL.search(code) and SHELL_DELETE.search(code)):
            raise Block(f"{name} one-liner that deletes files (hard stop c).")
        if SCRIPT_WRITE.search(code) and PROTECTED_WORD.search(code):
            raise Block(f"{name} one-liner that writes to a protected path "
                        "(raw/, journal/, scripts/, .claude/, .obsidian/, CLAUDE.md).")
    # writes to protected places
    if name == "tee" or name in PS_WRITE_CMDS:
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    elif name in {"sed", "perl", "ruby"} and any(
            a == "--in-place" or a.startswith("--in-place=") or re.match(r"^-[A-Za-z]*i", a)
            for a in args if a.startswith("-")):
        for p in pos:
            check_path("Bash", p, {}, cwd, root)
    elif name in MOVE_CMDS:
        check_move(name, positionals(args, {"-t", "--target-directory", "-S", "--suffix"}),
                   args, cwd, root, is_move=True)
    elif name == "install" and "-d" in args:
        for p in positionals(args, {"-m", "-o", "-g", "-t", "-S"}):
            check_path("Bash", p, {}, cwd, root)
    elif name in COPY_CMDS:
        check_move(name, positionals(args, {"-t", "--target-directory", "-S", "--suffix"}),
                   args, cwd, root, is_move=False)
    elif name in {"truncate", "dd"}:
        for p in pos:
            check_path("Bash", p.split("=", 1)[-1], {}, cwd, root)


CD_CMDS = {"cd", "pushd", "chdir", "set-location", "sl", "popd"}


def next_cwds(cwds, seg):
    """Candidate working directories after a segment. The original directory stays in
    the list (a cd may sit in a subshell or be undone), a followable cd adds its
    target, and one that cannot be followed (cd -, popd, a variable) adds None,
    meaning relative paths can no longer be resolved."""
    t = strip_prefix(seg)
    if not t or cmd_name(t) not in CD_CMDS:
        return cwds
    name, args = cmd_name(t), t[1:]
    pos = paths_in_segment(t)
    out = list(cwds)
    if name == "popd" or "-" in args or (pos and FUZZY.search(pos[0])) or (
            not pos and name == "pushd"):
        new = [None]
    elif not pos:
        new = [os.path.expanduser("~")]
    else:
        new = [os.path.join(c, os.path.expanduser(pos[0])) for c in cwds if c is not None]
    for n in new:
        if n not in out:
            out.append(n)
    return out[:16]


def check_shell(cmd, cwds, root, depth=0):
    if not isinstance(cwds, list):
        cwds = [cwds]
    for inner in inner_strings(cmd):
        if depth < 3:
            check_shell(inner, cwds, root, depth + 1)
    for seg in split_commands(cmd):
        for c in cwds:
            check_segment(seg, c, root, depth)
        cwds = next_cwds(cwds, seg)


# ------------------------------------------------- sensitivity: restricted
#
# The privacy skill says a `sensitivity: restricted` page never leaves the vault
# or lands in a report. This is the part of that rule a hook can check:
#   (a) Write/Edit/MultiEdit/NotebookEdit text headed for output/ or a path
#       outside the vault may not hold a verbatim run of RESTRICTED_MIN or more
#       characters from a restricted page;
#   (b) a shell command that names a restricted page (or a glob or directory that
#       holds one) and also writes to output/ or outside the vault, or runs a
#       sending tool (curl, scp, rsync, ssh, nc, gh ...), is refused;
#   (c) WebFetch, WebSearch and MCP tool inputs may not hold such a run.
# "Verbatim" means after lower-casing and collapsing every run of spaces and
# punctuation to one space, so bold, quotes, line wraps and bullets do not hide a
# copy. Paraphrase, short fragments and everything else stay prompt-only.
#
# Limits, so nobody mistakes this for a lock:
#   - only pages whose frontmatter says `sensitivity: restricted` count (not
#     private, not unlabelled pages, not labels the agent forgot to set);
#   - only runs of 200 or more normalised characters; a 199-character quote, a
#     paraphrase, a translation or text split into short pieces passes, and
#     each Write or Edit is judged alone (pieces added over several calls are
#     not added up);
#   - only text headed for output/, outside the vault, the web or an MCP tool;
#     copying a restricted page into another wiki page is prompt-only;
#   - shell: a command is refused only when it names the page (or a glob or
#     folder that holds it) and also writes to output/ or outside the vault, or
#     runs a sending tool. A path built at run time, hidden in a script file or
#     reached through find -exec or xargs is not seen;
#   - a script the agent runs (python3 x.py) can read and send anything.
# The page list is cached in .claude/guard-cache.json, keyed by mtime and size.
# Cost: one directory walk per export-bound call (about 12 ms on 3,000 pages
# on top of Python's start-up) plus about 0.7 ms per KB of text checked.
# Set RESTRICTED_CHECK = False to turn it off.
RESTRICTED_CHECK = True
RESTRICTED_MIN = 200          # normalised characters in a shared run
_WIN = 100                    # any shared run of 2*_WIN-1 chars holds a whole aligned window
EXPORT_DIRS = {"output"}      # vault folders whose content is meant to leave
SKIP_DIRS = {".git", ".obsidian", ".claude", ".trash", "node_modules", "__pycache__"}
CACHE_NAME = "guard-cache.json"
SEND_CMDS = {"curl", "wget", "scp", "sftp", "ssh", "rsync", "nc", "ncat", "netcat", "socat",
             "gh", "aws", "gsutil", "gcloud", "rclone", "mail", "mailx", "mutt", "sendmail",
             "invoke-webrequest", "iwr", "invoke-restmethod", "irm", "send-mailmessage"}
DIR_REF_CMDS = COPY_CMDS | MOVE_CMDS | {"rsync", "tar", "zip", "7z", "7za", "grep", "egrep",
                                        "fgrep", "rg", "ag", "ack", "scp", "compress-archive"}
FM_LABEL = re.compile(r"(?mi)^sensitivity[ \t]*:[ \t]*[\"']?restricted[\"']?[ \t\r]*(?:#.*)?$")
_CTX = {}
_PAGES = {}


def reset_ctx():
    _CTX.clear()
    _CTX.update({"dests": [], "tokens": [], "net": False})
    _PAGES.clear()


def normalise(text):
    return re.sub(r"[\W_]+", " ", text.lower()).strip()


def split_frontmatter(text):
    """(frontmatter, body). Frontmatter is '' when the page has none."""
    t = text.lstrip("﻿")
    if t.startswith("---"):
        m = re.search(r"\n---[ \t]*\r?(\n|$)", t[3:])
        if m:
            return t[3:3 + m.start()], t[3 + m.end():]
    return "", t


def _sample_hashes(norm_body):
    out = []
    for p in range(0, len(norm_body) - _WIN + 1, _WIN):
        out.append(zlib.crc32(norm_body[p:p + _WIN].encode("utf-8")))
    return out


def _read(path, limit):
    with open(path, "rb") as f:
        return f.read(limit).decode("utf-8", "replace")


def restricted_pages(root):
    """{vault-relative path: sampled window hashes} for every page labelled
    `sensitivity: restricted`. A cache in .claude/guard-cache.json holds each
    file's mtime and size; only files that changed since the last call are
    re-read, so a warm call costs one directory walk."""
    if "pages" in _PAGES:
        return _PAGES["pages"]
    base = norm(root)
    cache_path = os.path.join(root, ".claude", CACHE_NAME)
    try:
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        old = cache["files"] if cache.get("v") == 1 and isinstance(cache.get("files"), dict) else {}
    except (OSError, ValueError, KeyError, TypeError):
        old = {}
    files, changed = {}, False
    stack = [base]
    while stack:
        d = stack.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name not in SKIP_DIRS:
                            stack.append(e.path)
                        continue
                    if not e.name.lower().endswith(".md") or not e.is_file(follow_symlinks=False):
                        continue
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                rel = e.path[len(base) + 1:].replace(os.sep, "/")
                prev = old.get(rel)
                if (isinstance(prev, list) and len(prev) == 4 and prev[0] == st.st_mtime_ns
                        and prev[1] == st.st_size):
                    files[rel] = prev
                    continue
                changed = True
                ent = [st.st_mtime_ns, st.st_size, 0, []]
                try:
                    fm, _ = split_frontmatter(_read(e.path, 16384))
                    if FM_LABEL.search(fm):
                        _, body = split_frontmatter(_read(e.path, 8 << 20))
                        ent[2], ent[3] = 1, _sample_hashes(normalise(body))
                except OSError:
                    pass
                files[rel] = ent
    if changed or len(files) != len(old):
        try:
            if os.path.isdir(os.path.dirname(cache_path)):
                tmp = cache_path + f".{os.getpid()}.tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"v": 1, "files": files}, f, separators=(",", ":"))
                os.replace(tmp, cache_path)
        except OSError:
            pass
    pages = {rel: ent[3] for rel, ent in files.items() if ent[2]}
    _PAGES["pages"] = pages
    return pages


def _page_norm(root, rel):
    try:
        _, body = split_frontmatter(_read(os.path.join(norm(root), rel), 8 << 20))
    except OSError:
        return ""
    return normalise(body)


def _run(a, b, i, j):
    """Length of the common run through a[i] == b[j], extended both ways."""
    lo = 0
    while i - lo > 0 and j - lo > 0 and a[i - lo - 1] == b[j - lo - 1]:
        lo += 1
    hi = 0
    while i + hi < len(a) and j + hi < len(b) and a[i + hi] == b[j + hi]:
        hi += 1
    return lo + hi


def find_excerpt(text, root, exclude=()):
    """Vault-relative path of a restricted page that shares RESTRICTED_MIN or more
    normalised characters with `text`, or None. `exclude` holds lower-cased paths
    to skip (the page being written)."""
    if not RESTRICTED_CHECK or not isinstance(text, str) or len(text) < RESTRICTED_MIN:
        return None
    pages = {r: h for r, h in restricted_pages(root).items() if h and r.lower() not in exclude}
    if not pages:
        return None
    n = normalise(text)
    if len(n) < RESTRICTED_MIN:
        return None
    table = {}
    for rel, hs in pages.items():
        for h in hs:
            table.setdefault(h, []).append(rel)
    crc, seen, cache, w = zlib.crc32, set(), {}, _WIN
    if n.isascii():  # fast path: one byte per character, no per-window encode
        mv = memoryview(n.encode("ascii"))
        hs = [crc(mv[i:i + w]) for i in range(len(mv) - w + 1)]
    else:
        hs = [crc(n[i:i + w].encode("utf-8")) for i in range(len(n) - w + 1)]
    for ci, h in enumerate(hs):
        rels = table.get(h)
        if rels is None:
            continue
        window = n[ci:ci + w]
        for rel in rels:
            if (rel, ci) in seen:
                continue
            seen.add((rel, ci))
            t = cache.get(rel)
            if t is None:
                t = cache[rel] = _page_norm(root, rel)
            j = t.find(window)
            while j != -1:
                if _run(n, t, ci, j) >= RESTRICTED_MIN:
                    return rel
                j = t.find(window, j + 1)
    return None


def _strings(o, depth=0):
    if isinstance(o, str):
        yield o
    elif depth < 6 and isinstance(o, dict):
        for v in o.values():
            yield from _strings(v, depth + 1)
    elif depth < 6 and isinstance(o, (list, tuple)):
        for v in o:
            yield from _strings(v, depth + 1)


def check_restricted_write(tool, tin, paths, cwd, root):
    """(a): text written to output/ or outside the vault."""
    if not RESTRICTED_CHECK:
        return
    targets = []
    for p in paths:
        r = rel_to_root(p, cwd, root)
        if r is None or r.split("/")[0].lower() in EXPORT_DIRS:
            targets.append(r if r is not None else p)
    if not targets:
        return
    parts = written_texts(tool, tin)
    # the pieces of one MultiEdit are also tried joined, so a quote split across edits is seen
    joined = ["".join(parts), "\n".join(parts)] if len(parts) > 1 else []
    texts = [t for t in parts + joined if len(t) >= RESTRICTED_MIN]
    exclude = {t.lower() for t in targets}
    for t in texts:
        page = find_excerpt(t, root, exclude)
        if page:
            raise Block(f"the text holds a verbatim excerpt of {RESTRICTED_MIN} or more characters "
                        f"from '{page}', which is marked sensitivity: restricted, and it is headed "
                        "for output/ or outside the vault. Name the page and link it; do not copy "
                        "its words (privacy skill, hard stop b).",
                        rule="restricted-excerpt", target=log_path(targets[0]))


def log_path(p):
    p = "".join(ch for ch in str(p) if ch.isprintable())[:200]
    return "Write" if find_secret(p) else p


def check_restricted_net(tool, tin, root):
    """(c): WebFetch, WebSearch and MCP tool inputs."""
    if not RESTRICTED_CHECK:
        return
    for t in _strings(tin):
        if len(t) >= RESTRICTED_MIN:
            page = find_excerpt(t, root)
            if page:
                raise Block(f"the input of {tool} holds a verbatim excerpt of {RESTRICTED_MIN} or "
                            f"more characters from '{page}', which is marked sensitivity: "
                            "restricted. Restricted content never leaves the vault "
                            "(privacy skill, hard stop b).", rule="restricted-send", target=str(tool)[:80])


def is_export_path(d, cwd, root):
    if not d or d.startswith("/dev/") or d == "-":
        return False
    try:
        full, _ = lit_rel(d, cwd, root)
    except Block:
        return True  # cannot resolve it: assume it leaves
    return full is None or full.split("/")[0] in EXPORT_DIRS


def note_segment(tokens, name, args, pos, cwd, root):
    """Collect what check_restricted_shell needs from one command segment."""
    dests = list(redirect_targets(tokens))
    sub_args = args
    if name == "git" and args:  # git mv <src> <dest>: skip git's own options to find the subcommand
        a = list(args)
        while a and a[0].startswith("-"):
            opt = a.pop(0)
            if opt in GIT_OPTS_WITH_VALUE and a:
                a.pop(0)
        if a and a[0].lower() == "mv":
            name, sub_args = "mv", a[1:]
    if name == "tee" or name in PS_WRITE_CMDS:
        dests += pos
    elif name in MOVE_CMDS or name in COPY_CMDS or name == "rsync":
        p = positionals(sub_args, {"-t", "--target-directory", "-S", "--suffix"})
        topt = target_dir_option(sub_args)
        if topt is not None:
            dests.append(topt)
        elif len(p) >= 2:
            dests.append(p[-1])
    elif name == "dd":
        dests += [a.split("=", 1)[1] for a in args if a.startswith("of=")]
    for d in dests:
        if is_export_path(d, cwd, root):
            _CTX["dests"].append(d)
    if name in SEND_CMDS:
        _CTX["net"] = True
    dirs_ok = name in DIR_REF_CMDS
    skip = set(dests)
    for tok in tokens:
        if tok in skip or re.match(r"^(\d*|&)>", tok):
            continue  # the place a command writes is not something it reads
        _CTX["tokens"].append((cwd, tok, dirs_ok))


def _glob_match(pat, path):
    """Shell-style: * and ? never cross a /, so the pattern and the path must have
    the same number of segments."""
    ps, xs = pat.split("/"), path.split("/")
    return len(ps) == len(xs) and all(fnmatch.fnmatchcase(x, p) for p, x in zip(ps, xs))


def _expand_braces(pat, limit=64):
    out = [pat]
    for _ in range(4):
        nxt = []
        for p in out:
            m = re.search(r"\{([^{}]*)\}", p)
            if not m:
                nxt.append(p)
                continue
            for alt in m.group(1).split(",")[:limit]:
                nxt.append(p[:m.start()] + alt + p[m.end():])
        out = nxt[:limit]
    return out


def restricted_ref(tok, cwd, root, pages, dirs_ok):
    """The restricted page a token names (literally, by glob, or as a directory
    that holds it), or None."""
    lower = {r.lower(): r for r in pages}
    cands = {tok, tok.lstrip("<@")}
    if "=" in tok:
        cands.add(tok.split("=", 1)[1].lstrip("<@"))
    for c in cands:
        if not c or (c.startswith("-") and "=" not in c):
            continue
        try:
            m = FUZZY.search(c)
            if not m:
                r = rel_to_root(c, cwd, root)
                if r is None:
                    continue
                rl = r.lower()
                if rl in lower:
                    return lower[rl]
                if dirs_ok:
                    pre = rl + "/" if rl else ""
                    for k, v in lower.items():
                        if k.startswith(pre):
                            return v
                continue
            lit, rest = c[:m.start()], c[m.start():]
            d, sep, part = lit.rpartition("/")
            r = rel_to_root((d + "/") if sep else ".", cwd, root)
        except Block:
            continue
        if r is None:
            continue
        pat = ((r + "/" if r else "") + part + re.sub(r"\$\{?\w*\}?", "*", rest)).lower()
        for p in _expand_braces(pat):
            for k, v in lower.items():
                if _glob_match(p, k):
                    return v
                if dirs_ok:
                    parts = k.split("/")
                    for n in range(1, len(parts)):
                        if _glob_match(p, "/".join(parts[:n])):
                            return v
    return None


def check_restricted_shell(cmd, root):
    """(b), and (a) for text inside the command: runs after the shell is parsed."""
    if not RESTRICTED_CHECK or not (_CTX["dests"] or _CTX["net"]):
        return
    pages = restricted_pages(root)
    if not pages:
        return
    what = ("sends data out with" if _CTX["net"] else "writes to output/ or outside the vault with")
    low = cmd.lower().replace("\\", "/")
    hit = next((r for r in pages if r.lower() in low), None)
    if hit is None:
        for cwd, tok, dirs_ok in _CTX["tokens"]:
            hit = restricted_ref(tok, cwd, root, pages, dirs_ok)
            if hit:
                break
    if hit:
        raise Block(f"this command {what} '{hit}', which is marked sensitivity: restricted. "
                    "Restricted pages are not copied, piped or sent anywhere: name the page "
                    "and link it (privacy skill, hard stop b).",
                    rule="restricted-path", target=hit)
    page = find_excerpt(cmd, root)
    if page:
        raise Block(f"this command {what} a verbatim excerpt of {RESTRICTED_MIN} or more "
                    f"characters from '{page}', which is marked sensitivity: restricted "
                    "(privacy skill, hard stop b).", rule="restricted-excerpt", target=page)


# ------------------------------------------------------------------- main

NET_TOOLS = {"WebFetch", "WebSearch"}


def pre_tool_use(data):
    tool = data.get("tool_name", "")
    tin = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    reset_ctx()
    if tool in WRITE_TOOLS:
        if tool == "MultiEdit" and not tin.get("file_path"):
            paths = {e.get("file_path") or e.get("path") for e in tin.get("edits") or []}
        else:
            paths = {tin.get("file_path") or tin.get("notebook_path")}
        paths.discard(None)
        if not paths:
            raise Block("no file path in the tool input")
        for p in paths:
            check_path(tool, p, tin, cwd, root)
        check_secrets(written_texts(tool, tin))
        check_restricted_write(tool, tin, paths, cwd, root)
    elif tool in SHELL_TOOLS:
        cmd = tin.get("command") or ""
        check_shell(cmd, cwd, root)
        # Redirects, heredocs, tee and PowerShell writers carry content in the text.
        if re.search(r">|<<|\btee\b|set-content|add-content|out-file|\bsc\b|\bac\b|"
                     r"\bcommit\b|\bsed\b.*-[A-Za-z]*i|\bperl\b.*-[A-Za-z]*i|"
                     r"\bpython3?\b.*-c\b|\bnode(js)?\b.*(-e|--eval)\b|"
                     r"\bruby[0-9.]*\b.*\s-[A-Za-z0-9]*[eE]\b|\bphp[0-9.]*\b.*\s-[A-Za-z]*r\b",
                     cmd, re.I):
            check_secrets([cmd])
        check_restricted_shell(cmd, root)
    elif tool in NET_TOOLS or tool.startswith("mcp__"):
        check_restricted_net(tool, tin, root)


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


def log_target(data, root):
    """What to put in the log's `target`: a vault-relative path for a file tool, else
    the tool name. Never command text, content or anything that looks like a secret."""
    tool = data.get("tool_name") or data.get("hook_event_name") or "unknown"
    tin = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    if tool in WRITE_TOOLS:
        p = tin.get("file_path") or tin.get("notebook_path")
        if not p:
            edits = [e for e in (tin.get("edits") or []) if isinstance(e, dict)]
            p = next((e.get("file_path") or e.get("path") for e in edits), None)
        if isinstance(p, str) and p:
            try:
                r = rel_to_root(p, data.get("cwd") or os.getcwd(), root)
            except Block:
                r = None
            p = r if r is not None else p
            p = "".join(ch for ch in p if ch.isprintable())[:200]
            if not find_secret(p):
                return p
    return str(tool)[:80]


def write_log(data, rule, target, root):
    """Append {ts, tool, rule, target} to .claude/guard.log, rotating at LOG_MAX
    to guard.log.1. Best effort: a log that cannot be written never changes a block."""
    try:
        d = os.path.join(root, ".claude")
        if not os.path.isdir(d):
            return
        path = os.path.join(d, "guard.log")
        try:
            if os.path.getsize(path) >= LOG_MAX:
                os.replace(path, path + ".1")
        except OSError:
            pass
        line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                           "tool": str(data.get("tool_name") or data.get("hook_event_name") or "unknown")[:80],
                           "rule": rule, "target": target}, ensure_ascii=False) + "\n"
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except Exception:
        pass


def vault_root(data):
    return os.environ.get("CLAUDE_PROJECT_DIR") or (
        data.get("cwd") if isinstance(data.get("cwd"), str) else None) or os.getcwd()


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.stderr.write(BLOCK_MSG + "could not read the hook input.\n")
        return 2
    if not isinstance(data, dict):
        sys.stderr.write(BLOCK_MSG + "the hook input is not a JSON object.\n")
        return 2
    try:
        if data.get("hook_event_name") == "Stop":
            stop(data)
        else:
            pre_tool_use(data)
    except Block as b:
        sys.stderr.write(BLOCK_MSG + str(b) + "\n")
        root = vault_root(data)
        write_log(data, b.rule or classify(str(b)), b.target or log_target(data, root), root)
        return 2
    except Exception as e:  # fail closed: a guard that crashes must not wave things through
        if data.get("hook_event_name") == "Stop":
            return 0  # the Stop hook only warns; never trap the agent in a loop
        sys.stderr.write(BLOCK_MSG + f"internal error ({e!r}); refusing.\n")
        root = vault_root(data)
        write_log(data, "internal-error", log_target(data, root), root)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
