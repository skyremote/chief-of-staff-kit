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
    git log/diff/show/status, gh pr view...), with the options that write or
    run programs refused. The hook rewrites the program to its full path, so
    a shell function or alias cannot swap it for another program after the check
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
import shutil
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
    "shasum", "sha256sum", "md5", "git", "gh",
}

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
    "reset", "sync", "save", "store", "commit", "fork", "clear", "purge",
    "drop", "mutate", "generate", "compose", "forward", "mute", "block", "ban",
    "pin", "unpin", "star", "follow", "like", "log", "register", "tag", "untag",
    "order", "buy", "purchase", "sell", "confirm", "accept", "decline",
    "resolve", "dismiss", "snooze", "trigger", "invoke", "notify", "broadcast",
    "install", "uninstall", "provision", "scale", "restart", "reboot",
    "shutdown", "rollback", "revert", "replace", "download", "export", "sort",
    "organise", "organize", "tidy", "align", "distribute", "lock", "unlock",
    "record", "capture", "open", "launch", "sign", "signup", "login", "logout",
    "authorize", "authorise", "connect", "disconnect", "enroll", "enrol",
    "vote", "toggle", "increment", "decrement", "claim", "withdraw", "deposit",
    "redeem", "sms", "dial", "nudge", "remind", "alert",
}

READ_WORDS = {
    "get", "list", "search", "read", "find", "view", "describe", "lookup",
    "count", "inspect", "retrieve", "browse", "status", "whoami", "info",
    "stats", "history", "diff", "compare",
}

SQL_START = re.compile(
    r"^\s*(select|show|describe|desc|explain|with|insert|update|delete|drop|alter|create|"
    r"truncate|grant|revoke|merge|replace|upsert|copy|call|exec|execute|do|set|begin|"
    r"commit|rollback|vacuum|attach|detach|pragma|load|lock|unlock|rename|comment|"
    r"analyze|analyse|refresh|reindex|cluster|prepare|declare|use|kill|optimize|repair)\b",
    re.I)
SQL_SHAPE = re.compile(r"\b(from|into|table|set|where|values|function|procedure|trigger|index|"
                       r"view|schema|database|user|role|column|constraint|sequence|extension|"
                       r"system|begin)\b|;|--|/\*|\(|\$\$", re.I)
SQL_READ = re.compile(r"^\s*(select|show|describe|desc|explain)\b", re.I)
SQL_CHANGE = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|merge|"
                        r"replace|upsert|copy|call|exec|execute|set|vacuum|attach|detach|pragma|"
                        r"into|analyze|analyse|lock|load|do)\b", re.I)
SQL_COMMENTS = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)


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


def same_tree(path, root):
    """True when path is root or inside it, by file identity, not by spelling."""
    try:
        target = os.stat(root)
    except OSError:
        return False
    current = os.path.realpath(path)
    while True:
        try:
            info = os.stat(current)
            if (info.st_dev, info.st_ino) == (target.st_dev, target.st_ino):
                return True
        except OSError:
            pass
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent


def check_git(args, cwd, scratch):
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] != "--no-pager":
            raise Deny("git option %s is not allowed in a test run; git runs only in the "
                       "session's folder" % args[i])
        i += 1
    if i >= len(args):
        raise Deny("git with no command")
    if scratch and same_tree(cwd, scratch):
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
        if any(a.startswith("--web") or (a.startswith("-") and not a.startswith("--") and "w" in a)
               for a in args[2:]):
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
    if name == "git":
        check_git(args, cwd, scratch)
    elif name == "gh":
        check_gh(args)
    program = shutil.which(name)
    if not program or (scratch and same_tree(program, scratch)):
        raise Deny("`%s` was not found as a program" % name)
    body = command.lstrip()
    if not body.startswith(name) or (len(body) > len(name) and not body[len(name)].isspace()):
        raise Deny("the command could not be read")
    return shlex.quote(program) + body[len(name):]


def words_of_tool(tool_name):
    tail = tool_name.split("__", 2)[-1] if tool_name.count("__") >= 2 else tool_name
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", tail)
    return [w.lower() for w in re.split(r"[_\-\s.:/]+", spaced) if w]


def strings_in(value, key=None, depth=0):
    if depth > 8:
        raise Deny("the input is nested too deeply to check")
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for name, item in value.items():
            for pair in strings_in(item, str(name), depth + 1):
                yield pair
    elif isinstance(value, list):
        for item in value:
            for pair in strings_in(item, key, depth + 1):
                yield pair


def sql_changes_data(text):
    plain = SQL_COMMENTS.sub(" ", text or "")
    if not SQL_START.search(plain) or not SQL_SHAPE.search(text or ""):
        return bool(re.search(r";\s*(insert|update|delete|drop|alter|create|truncate)\b", plain, re.I))
    body = plain.strip().rstrip(";")
    if ";" in body or not SQL_READ.search(body):
        return True
    return bool(SQL_CHANGE.search(body))


def check_mcp_input(data):
    for key, text in strings_in(data):
        if key and "method" in key.lower() and text.strip().upper() not in ("GET", "HEAD", ""):
            raise Deny("a %s request would change something" % text.strip().upper()[:20])
        if sql_changes_data(text):
            raise Deny("the input holds a statement that could change data")


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
        updated = dict(data)
        updated["command"] = check_bash(str(data.get("command", "")), cwd, scratch)
        return updated
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
        updated = decide(event)
        log({"t": time.time(), "tool": tool, "decision": "allow", "input": short(data)})
        if updated is not None:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Test mode: one plain read command, run by full path.",
                "updatedInput": updated,
            }}))
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
