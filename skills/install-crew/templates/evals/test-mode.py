#!/usr/bin/env python3
"""test-mode.py: the safety hook for golden-task test sessions.

golden.py adds this script as a PreToolUse hook to every test session it
starts (through `claude -p --settings`) and sets CREW_TEST_MODE=1. It does not
belong in your settings file: outside a test session it allows everything.

Test sessions run with bypass permissions so reads never wait for a prompt
nobody can answer, which makes this hook the only guard. In a test session
nothing may be sent, changed or published, so it allows only calls that read:

  - built-in read tools (Read, Grep, Glob, WebSearch, WebFetch, Skill, Agent...)
  - Write and Edit inside the run's scratch folder (CREW_TEST_SCRATCH)
  - one plain read command at a time in the shell: no shell operators at all
    (no ; & | < > ( ) { } $ ` ! or new lines), from a short list (ls, cat, grep,
    find, git log/diff/show/status, gh pr view...), with the options that
    write or run programs refused
  - connected (MCP) tools whose name reads as a plain lookup (get, list,
    search, read...), holds no write word (send, create, update, delete...)
    and carries no SQL write or non-GET method in its input

Everything else is denied with a reason the model sees, and every decision is
appended to CREW_TEST_LOG as one JSON line. Web reads (WebFetch, WebSearch)
still run: a GET request is not stopped.

A connected tool that only reads but is denied by name can be allowed by
listing its exact name, one per line, in test-mode-allow.txt beside golden.py
(golden.py passes it as CREW_TEST_ALLOW).

Fails closed: any error here denies the call, and golden.py sets
"onFailure": "block" so a crash or timeout blocks too.
"""

import json
import os
import re
import shlex
import sys
import time

READ_TOOLS = {
    "Read", "Grep", "Glob", "LS", "WebSearch", "WebFetch", "TodoWrite",
    "Skill", "Agent", "Task", "ToolSearch", "BashOutput", "TaskOutput",
    "ListMcpResourcesTool", "ReadMcpResourceTool", "ReadMcpResourceDirTool",
    "EnterPlanMode", "ExitPlanMode", "StructuredOutput",
}

FILE_WRITE_TOOLS = {
    "Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}

# Shell: one plain command. Any of these characters means more than one
# command, a redirect, an expansion or a subshell, so the call is refused.
SHELL_OPERATORS = set(";&|<>(){}$`!\n\r")

# Programs with no option that writes a file, sends data or runs another
# program. find, git and gh have such options and get their own checks.
PLAIN_READERS = {
    "ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "pwd", "echo",
    "printf", "which", "stat", "du", "df", "diff", "cmp", "comm", "nl",
    "basename", "dirname", "realpath", "readlink", "uname", "whoami",
    "shasum", "sha256sum", "md5", "find", "git", "gh",
}

FIND_UNSAFE = ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fls")

GIT_READ = {"status", "log", "diff", "show", "blame", "ls-files", "rev-parse",
            "describe", "shortlog", "branch", "tag", "remote"}
GIT_UNSAFE_PREFIXES = ("--output", "--ext-diff", "--exec", "--upload-pack",
                       "--receive-pack", "--config-env")

GH_READ = {
    ("pr", "view"), ("pr", "list"), ("pr", "diff"), ("pr", "checks"), ("pr", "status"),
    ("issue", "view"), ("issue", "list"), ("issue", "status"),
    ("repo", "view"), ("run", "view"), ("run", "list"),
    ("release", "view"), ("release", "list"),
}

WRITE_WORDS = {
    "send", "create", "update", "delete", "remove", "del", "post", "publish",
    "write", "edit", "patch", "put", "insert", "upsert", "modify", "move",
    "trash", "archive", "unarchive", "label", "draft", "comment", "add", "set",
    "unset", "cancel", "invite", "schedule", "reschedule", "book", "pay",
    "payment", "charge", "refund", "transfer", "deploy", "merge", "push",
    "reply", "respond", "react", "upload", "execute", "exec", "run", "start",
    "stop", "kill", "apply", "approve", "reject", "submit", "mark",
    "subscribe", "unsubscribe", "share", "revoke", "grant", "assign", "close",
    "enable", "disable", "rename", "duplicate", "attach", "import", "restore",
    "reset", "sync", "commit", "fork", "clear", "purge", "drop", "mutate",
    "compose", "forward", "mute", "ban", "follow", "like", "register", "buy",
    "purchase", "sell", "confirm", "accept", "decline", "resolve", "dismiss",
    "snooze", "trigger", "invoke", "notify", "broadcast", "install",
    "uninstall", "provision", "scale", "restart", "reboot", "shutdown",
    "rollback", "revert", "replace", "organise", "organize", "tidy", "align",
    "distribute", "launch", "sign", "signup", "login", "logout", "authorize",
    "authorise", "connect", "disconnect", "enroll", "enrol", "vote", "toggle",
    "increment", "decrement", "claim", "withdraw", "deposit", "redeem", "sms",
    "dial", "nudge", "remind", "alert",
}

READ_WORDS = {
    "get", "list", "search", "read", "find", "view", "describe", "lookup",
    "count", "inspect", "retrieve", "browse", "status", "whoami", "info",
    "stats", "history", "diff", "compare",
}

SQL_WRITE = re.compile(
    r"(^|;)\s*(insert\s+into|update\s+\S+\s+set|delete\s+from|drop\s+(table|database|schema|"
    r"index|view|user|role)|alter\s+(table|database|schema|user|role)|create\s+(table|database|"
    r"schema|index|view|user|role)|truncate\s+(table\s+)?\S+|grant\s+\S+|revoke\s+\S+|merge\s+into|"
    r"replace\s+into|upsert\s+into|copy\s+\S+\s+(from|to)|call\s+\S+\s*\(|exec(ute)?\s+\S+)",
    re.I)


class Deny(Exception):
    pass


def short(value, limit=300):
    text = value if isinstance(value, str) else json.dumps(value)
    return text if len(text) <= limit else text[:limit] + "..."


def inside(path, root, cwd):
    if not path or not root:
        return False
    full = os.path.realpath(os.path.join(cwd or os.getcwd(), os.path.expanduser(path)))
    base = os.path.realpath(root)
    return full == base or full.startswith(base + os.sep)


def words_of_command(command):
    if any(c in SHELL_OPERATORS for c in command):
        raise Deny("shell operators are not allowed in a test run; run one plain read command")
    lexer = shlex.shlex(command, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        words = list(lexer)
    except ValueError:
        raise Deny("the command could not be read")
    if not words:
        raise Deny("empty command")
    return words


def check_find(args):
    if any(a.startswith(FIND_UNSAFE) for a in args):
        raise Deny("find would delete files or run a program")


def check_git(args, cwd, scratch):
    i, where = 0, cwd
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            where = os.path.join(where or os.getcwd(), os.path.expanduser(args[i + 1]))
            i += 2
        elif args[i] == "--no-pager":
            i += 1
        else:
            raise Deny("git option %s is not allowed in a test run" % args[i])
    if i >= len(args):
        raise Deny("git with no command")
    if scratch and inside(where, scratch, cwd):
        raise Deny("git cannot run inside the scratch folder")
    sub, rest = args[i], args[i + 1:]
    if sub not in GIT_READ:
        raise Deny("git %s changes the repository or a remote" % sub)
    if any(a.startswith(GIT_UNSAFE_PREFIXES) for a in rest):
        raise Deny("git %s with that option would write a file or run a program" % sub)
    positional = [a for a in rest if not a.startswith("-")]
    if sub == "branch":
        listing = {"--list", "-l", "--show-current", "-a", "-r", "-v", "-vv", "--all",
                   "--remotes", "--verbose", "--contains", "--merged", "--no-merged",
                   "--sort", "--format", "--points-at", "--no-color", "--color"}
        flags = [a for a in rest if a.startswith("-")]
        if any(f.split("=", 1)[0] not in listing for f in flags) or \
                (positional and not ({"--list", "-l"} & set(flags))):
            raise Deny("git branch would change branches")
    elif sub == "tag":
        if rest and not ({"-l", "--list"} & set(rest)):
            raise Deny("git tag would create or delete a tag")
        if any(a.startswith("-") and a not in ("-l", "--list") and not a.startswith("-n")
               for a in rest):
            raise Deny("git tag would create or delete a tag")
    elif sub == "remote":
        if not (rest in ([], ["-v"], ["--verbose"]) or (rest and rest[0] in ("show", "get-url"))):
            raise Deny("git remote would change remotes")


def check_gh(args):
    if len(args) >= 2 and (args[0], args[1]) in GH_READ:
        if any(a in ("-w", "--web") for a in args[2:]):
            raise Deny("gh --web opens a browser")
        return
    if args and args[0] == "api":
        rest, i, path = args[1:], 0, None
        while i < len(rest):
            a = rest[i]
            if a in ("--jq", "-q"):
                i += 2
                continue
            if a == "--paginate" or a.startswith("--jq="):
                i += 1
                continue
            if a.startswith("-") or path is not None:
                raise Deny("gh api accepts only a path, --jq and --paginate in a test run")
            path = a
            i += 1
        if not path or path == "graphql":
            raise Deny("gh api accepts only a REST path in a test run")
        return
    raise Deny("gh %s is not on the read-only list" % " ".join(args[:2]))


def check_bash(command, cwd, scratch):
    words = words_of_command(command)
    name, args = words[0], words[1:]
    if "=" in name or "/" in name:
        raise Deny("only plain read commands run in a test, with no variables or paths")
    if name not in PLAIN_READERS:
        raise Deny("`%s` is not on the read-only list" % name)
    if any(a.startswith("-") and any(c in a for c in "*?[") for a in args):
        raise Deny("an option with a wildcard cannot be checked")
    if name == "find":
        check_find(args)
    elif name == "git":
        check_git(args, cwd, scratch)
    elif name == "gh":
        check_gh(args)


def words_of_tool(tool_name):
    tail = tool_name.split("__", 2)[-1] if tool_name.count("__") >= 2 else tool_name
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", tail)
    return [w.lower() for w in re.split(r"[_\-\s.:/]+", spaced) if w]


def strings_in(value, depth=0):
    if depth > 6:
        return
    if isinstance(value, str):
        yield None, value
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                yield str(key), item
            else:
                for pair in strings_in(item, depth + 1):
                    yield pair
    elif isinstance(value, list):
        for item in value:
            for pair in strings_in(item, depth + 1):
                yield pair


def check_mcp_input(data):
    for key, text in strings_in(data):
        if key and key.lower() in ("method", "http_method", "verb") and \
                text.strip().upper() not in ("GET", "HEAD", ""):
            raise Deny("a %s request would change something" % text.strip().upper())
        if SQL_WRITE.search(text or ""):
            raise Deny("the input holds a statement that changes data")


def allow_list():
    path = os.environ.get("CREW_TEST_ALLOW", "")
    if not path or not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip() and not line.startswith("#")}


def decide(event):
    tool = event.get("tool_name") or ""
    data = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    scratch = os.environ.get("CREW_TEST_SCRATCH", "")
    if tool in READ_TOOLS:
        return
    if tool in FILE_WRITE_TOOLS:
        if inside(data.get(FILE_WRITE_TOOLS[tool], ""), scratch, cwd):
            return
        raise Deny("it writes a real file; writes are allowed only under %s"
                   % (scratch or "the scratch folder"))
    if tool == "Bash":
        check_bash(str(data.get("command", "")), cwd, scratch)
        return
    if tool == "AskUserQuestion":
        raise Deny("nobody can answer in a test run; put the question in your answer")
    if tool.startswith("mcp__"):
        if tool not in allow_list():
            words = words_of_tool(tool)
            if any(w in WRITE_WORDS for w in words):
                raise Deny("connected tools that change things are blocked")
            if not any(w in READ_WORDS for w in words):
                raise Deny("this connected tool is not known to only read")
        check_mcp_input(data)
        return
    raise Deny("%s is not on the read-only list" % tool)


def log(entry):
    path = os.environ.get("CREW_TEST_LOG", "")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except (OSError, ValueError):
        pass


def deny(tool, why):
    reason = ("Test mode: %s blocked (%s). This is a golden-task test run, so nothing "
              "may be sent, changed or published. Say in your answer exactly what you "
              "would have done, and do not try another route." % (tool or "this call", why))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))


def main():
    if os.environ.get("CREW_TEST_MODE") != "1":
        return 0
    tool, data = "", {}
    try:
        event = json.loads(sys.stdin.read() or "{}")
        if not isinstance(event, dict):
            raise Deny("the hook input was not an object")
        tool = str(event.get("tool_name") or "")
        data = event.get("tool_input") or {}
        decide(event)
        log({"t": time.time(), "tool": tool, "decision": "allow", "input": short(data)})
    except Deny as blocked:
        log({"t": time.time(), "tool": tool, "decision": "deny", "why": str(blocked), "input": short(data)})
        deny(tool, str(blocked))
    except Exception as error:  # fail closed
        log({"t": time.time(), "tool": tool, "decision": "deny",
             "why": "test mode error: %s" % type(error).__name__, "input": short(data)})
        deny(tool, "test mode could not check this call")
    return 0


if __name__ == "__main__":
    sys.exit(main())
