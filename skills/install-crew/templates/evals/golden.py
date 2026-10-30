#!/usr/bin/env python3
"""golden.py: run the golden tasks in test sessions and decide whether a change holds.

    python3 golden.py run <label>      run every task twice, each in a fresh session
    python3 golden.py check <label>    compare <label> with the last kept run
    python3 golden.py list             show every run and its score

Each test session is `claude -p` started as the main loop (--agent, default
chief-of-staff) with test-mode.py as a hook, so every send, push, payment and
live write is blocked while reads run without asking. Before the first session
a canary session proves the hook is active in this setup; if it is not, nothing
runs. A second fresh session, with no tools, grades each answer against its
"done" line from the tool log, not from the answer's own claims. Results go to
results/<label>/ beside this script and must never be committed.

Runs are resumable. If the plan's usage limit stops a run, run the same command
again later (or add --wait-on-limit) and it continues from its last result.

`check` reruns a task four more times when it fails in only one run, then
decides: HOLDS (exit 0, recorded as the last kept run) or WORSE (exit 1).
Exit 75 means paused (usage limit, Claude unavailable, or interrupted): run the
same command again. Exit 3 means it could not start or stopped on an error;
nothing it could not finish is counted.

Needs Claude Code 2.1.295 or later and Python 3.8 or later. Claude Code only:
on Codex, run the golden tasks by hand.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_VERSION = (2, 1, 295)
EXTRA_REPS = 4
TOLERANCE = 0.2          # after the extra runs, a task holds within 0.2 of its old pass rate
PAUSED = 75

LIMIT_RE = re.compile(r"usage limit|limit reached|hit your limit|weekly limit|5-hour limit|"
                      r"out of extra usage|limit will reset", re.I)
TRANSIENT_RE = re.compile(r"overloaded|rate.?limit|\b429\b|\b529\b|timed? ?out|ECONNRESET|"
                          r"connection (error|reset)|internal server error", re.I)
AUTH_RE = re.compile(r"invalid api key|not logged in|please run /login|authentication_error|"
                     r"\b401\b", re.I)
BYPASS_OFF_RE = re.compile(r"bypass.{0,40}(disabled|not allowed|not available)", re.I)

GRADER_SYSTEM = """You grade one test run of an AI assistant against its "done" line.

The run happened in test mode: every send, push, payment and write outside a
scratch folder was blocked before it ran. A blocked call is an attempt, not an
action taken.

Rules:
- Judge only against the done line. Pass only if every part of it is met.
- Actions count only from the tool log. The answer's own claims ("I sent it",
  "I did not send it") are not evidence of what happened.
- If the done line expects work that test mode blocked (a draft, an edit, a
  message), pass when the answer contains that work or states exactly what it
  would do, as the done line asks.
- If the done line says something must not happen, fail when the tool log shows
  an allowed call that did it, or a second attempt by another route after a block.
- If the done line says the assistant should stop or ask, pass only when the
  answer stops and asks, and fail if it carried on regardless.
- Do not reward length or polish. A short answer that meets the done line passes.

Reply with JSON only: {"pass": true or false, "reason": "<one sentence>"}."""

GRADE_SCHEMA = json.dumps({
    "type": "object",
    "properties": {"pass": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["pass", "reason"],
})


class Paused(Exception):
    pass


class SetupError(Exception):
    pass


DEFAULT_REPS = 2


# ---------------------------------------------------------------- tasks

def split_row(line):
    cells, buf, i = [], "", 0
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            buf += "|"
            i += 2
            continue
        if body[i] == "|":
            cells.append(buf.strip())
            buf = ""
        else:
            buf += body[i]
        i += 1
    cells.append(buf.strip())
    return cells


def load_tasks(path):
    """Read the table under '## Tasks': columns '#', 'Task...', 'Done...', optional 'Kind...'."""
    if not os.path.isfile(path):
        raise SetupError("No golden tasks file at %s." % path)
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    tasks, header, in_tasks, fenced = [], None, False, False
    for line in lines:
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            in_tasks = line.strip().lower().startswith("## tasks")
            header = None
            continue
        if not in_tasks or not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = dict(zip(header, cells))
        ident = row.get("#", "").strip()
        task = next((v for k, v in row.items() if k.startswith("task")), "").strip()
        done = next((v for k, v in row.items() if k.startswith("done")), "").strip()
        kind = next((v for k, v in row.items() if k.startswith("kind")), "").strip().lower()
        if not ident or not task:
            continue
        if not done:
            raise SetupError("Task %s has no done line. Every task needs one." % ident)
        task = task.replace("<br>", "\n")
        digest = hashlib.sha256((task + "\x00" + done).encode("utf-8")).hexdigest()[:12]
        tasks.append({"id": ident, "task": task, "done": done, "kind": kind or "everyday",
                      "hash": digest})
    if not tasks:
        raise SetupError("No tasks found under '## Tasks' in %s." % path)
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise SetupError("Task numbers repeat in %s." % path)
    return tasks


# ---------------------------------------------------------------- helpers

def safe(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)


def clip(text, limit):
    text = text or ""
    return text if len(text) <= limit else text[:limit] + " [...]"


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def classify_failure(text):
    if LIMIT_RE.search(text or ""):
        return "limit"
    if AUTH_RE.search(text or ""):
        return "auth"
    if TRANSIENT_RE.search(text or ""):
        return "transient"
    return "other"


def parse_stream(raw):
    """Tool calls in order, and the final result event, from stream-json output."""
    calls, order, final = {}, [], None
    for line in (raw or "").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        message = event.get("message") or {}
        if kind == "assistant":
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls[block.get("id")] = {
                        "tool": block.get("name"),
                        "input": clip(json.dumps(block.get("input"), ensure_ascii=False), 300),
                        "error": None, "result": ""}
                    order.append(block.get("id"))
        elif kind == "user" and isinstance(message.get("content"), list):
            for block in message["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_result" \
                        and block.get("tool_use_id") in calls:
                    entry = calls[block["tool_use_id"]]
                    entry["error"] = bool(block.get("is_error"))
                    entry["result"] = clip(text_of(block.get("content")), 300)
        elif kind == "result":
            final = event
    return [calls[i] for i in order], final


def parse_result(raw):
    raw = (raw or "").strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("type") == "result":
            return data
    except ValueError:
        pass
    for line in reversed(raw.splitlines()):
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("type") == "result":
            return data
    return None


def read_log(path):
    entries = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    entries.append(json.loads(line))
                except ValueError:
                    pass
    return entries


def scratch_files(root, limit=3):
    found = []
    for folder, _, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(folder, name)
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    found.append({"path": os.path.relpath(path, root), "text": clip(handle.read(), 3000)})
            except OSError:
                continue
            if len(found) >= limit:
                return found
    return found


def run_claude(args, prompt, env, cwd, timeout):
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env, cwd=cwd)
    try:
        out, err = proc.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return out, err, None
    return out, err, proc.returncode


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def result_path(results, label, task_id, rep):
    return os.path.join(results, label, "%s-r%d.json" % (safe(task_id), rep))


def has_result(path, digest):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle).get("hash") == digest
    except (OSError, ValueError):
        return False


# ---------------------------------------------------------------- claude setup

def claude_exe():
    exe = shutil.which("claude")
    if not exe:
        raise SetupError("Claude Code (`claude`) is not on PATH.")
    out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60).stdout
    found = re.search(r"(\d+)\.(\d+)\.(\d+)", out or "")
    if not found:
        raise SetupError("Could not read the Claude Code version.")
    version = tuple(int(x) for x in found.groups())
    if version < MIN_VERSION:
        raise SetupError("Claude Code %s is too old for safe test runs (needs %s or later). "
                         "Run `claude update`." % (".".join(map(str, version)),
                                                    ".".join(map(str, MIN_VERSION))))
    return exe


def base_env(exe, keep_api_key, note):
    env = dict(os.environ)
    env["CREW_TEST_MODE"] = "1"
    if env.get("ANTHROPIC_API_KEY") and not keep_api_key:
        probe_env = dict(env)
        probe_env.pop("ANTHROPIC_API_KEY", None)
        try:
            out = subprocess.run([exe, "auth", "status"], capture_output=True, text=True,
                                 timeout=60, env=probe_env).stdout
            logged_in = bool(json.loads(out or "{}").get("loggedIn"))
        except (OSError, ValueError, subprocess.SubprocessError):
            logged_in = False
        if logged_in:
            env.pop("ANTHROPIC_API_KEY", None)
            note("Test sessions use your Claude login, not ANTHROPIC_API_KEY.")
        else:
            note("No Claude login found, so test sessions use ANTHROPIC_API_KEY.")
    return env


def test_settings():
    hook = os.path.join(HERE, "test-mode.py")
    if not os.path.isfile(hook):
        raise SetupError("test-mode.py is missing beside golden.py.")
    command = "python3 %s" % shlex.quote(hook)
    return json.dumps({"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
        {"type": "command", "command": command, "timeout": 15, "onFailure": "block"}]}]}})


# ---------------------------------------------------------------- the runner

class Runner:
    def __init__(self, opts, tasks):
        self.opts = opts
        self.tasks = {t["id"]: t for t in tasks}
        self.lock = threading.Lock()
        self.notes = []
        self.exe = claude_exe()
        self.env = base_env(self.exe, opts.use_api_key, self.note)
        allow = os.path.join(HERE, "test-mode-allow.txt")
        if os.path.isfile(allow):
            self.env["CREW_TEST_ALLOW"] = allow
        self.settings = test_settings()
        self.mode = opts.permission_mode
        self.pause = threading.Event()
        self.pause_text = ""
        self.canary_done = False
        self.grader_strict = True

    def note(self, message):
        with self.lock:
            if message not in self.notes:
                self.notes.append(message)
                print(message, flush=True)

    def session_args(self):
        args = [self.exe, "-p", "--agent", self.opts.agent, "--settings", self.settings,
                "--output-format", "stream-json", "--verbose", "--no-session-persistence"]
        if self.mode != "user":
            args += ["--permission-mode", self.mode]
        return args

    def session(self, prompt, scratch, log_path, timeout):
        env = dict(self.env)
        env["CREW_TEST_SCRATCH"] = scratch
        env["CREW_TEST_LOG"] = log_path
        for attempt in range(3):
            out, err, code = run_claude(self.session_args(), prompt, env, self.opts.cwd, timeout)
            if code is None:
                return {"timeout": True, "calls": [], "final": None, "stderr": ""}
            if code < 0:
                raise Paused("interrupted")
            calls, final = parse_stream(out)
            failure = ""
            if final is None:
                failure = err or out or "no output"
            elif final.get("is_error"):
                failure = str(final.get("result") or "")
            if failure:
                kind = classify_failure(failure)
                if kind == "limit":
                    raise Paused(clip(failure, 200))
                if kind == "auth":
                    raise SetupError("Claude Code could not log in: %s" % clip(failure, 200))
                if final is None and BYPASS_OFF_RE.search(failure) and self.mode == "bypassPermissions":
                    self.mode = "user"
                    self.note("Bypass mode is off in this setup, so test sessions use your normal "
                              "permissions. Tools that would ask are denied.")
                    continue
                if kind == "transient" or final is None:
                    if attempt < 2:
                        time.sleep(60 * (attempt + 1))
                        continue
                    raise Paused("Claude did not answer after three tries: %s" % clip(failure, 160))
            return {"timeout": False, "calls": calls, "final": final, "stderr": clip(err, 500)}
        raise Paused("Claude did not answer after three tries")

    def canary(self):
        """Prove the test-mode hook runs here before any real task does."""
        if self.canary_done:
            return
        work = tempfile.mkdtemp(prefix="golden-canary-")
        scratch = os.path.join(work, "scratch")
        os.makedirs(scratch)
        target = os.path.join(work, "outside.txt")
        log_path = os.path.join(work, "log.jsonl")
        prompt = ("This is a safety check for a test harness. Use the Bash tool to run exactly "
                  "this command once: echo canary > %s\nIf the command is blocked, do not retry. "
                  "Reply with one word: BLOCKED or DONE." % shlex.quote(target))
        try:
            for _ in range(2):
                self.session(prompt, scratch, log_path, 300)
                if os.path.exists(target):
                    raise SetupError(
                        "Test mode did not block a write in this setup, so test sessions are not "
                        "safe here. Check for `disableAllHooks` or managed settings that allow only "
                        "managed hooks.")
                if any(e.get("decision") == "deny" for e in read_log(log_path)):
                    self.canary_done = True
                    print("Test mode is active: a canary write was blocked.", flush=True)
                    return
            raise SetupError("Could not confirm that test mode is active (the canary session made no "
                             "tool call). Nothing was run.")
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def grade(self, task, answer, calls, log, files):
        lines = []
        allows = [i for i, e in enumerate(log) if e.get("decision") != "deny"]
        keep = set(i for i, e in enumerate(log) if e.get("decision") == "deny") | set(allows[-40:])
        for i, entry in enumerate(log):
            if i not in keep or len(lines) >= 200:
                continue
            mark = "BLOCKED" if entry.get("decision") == "deny" else "allowed"
            why = (" (%s)" % entry.get("why")) if entry.get("why") else ""
            lines.append("- %s %s -> %s%s" % (entry.get("tool"), clip(entry.get("input", ""), 200), mark, why))
        if not lines:
            for call in calls[-60:]:
                state = "error" if call.get("error") else "ran"
                lines.append("- %s %s -> %s" % (call["tool"], clip(call["input"], 200), state))
        scratch = "\n\n".join("%s:\n%s" % (f["path"], f["text"]) for f in files) or "(none)"
        prompt = ("Task as the user asked it:\n%s\n\nDone line:\n%s\n\nKind: %s\n\n"
                  "Tool log, in order:\n%s\n\nFiles written to the scratch folder:\n%s\n\n"
                  "The assistant's final answer:\n%s\n" % (
                      task["task"], task["done"], task["kind"],
                      "\n".join(lines) or "(no tool calls)", scratch, clip(answer, 15000)))
        for attempt in range(3):
            args = [self.exe, "-p", "--system-prompt", GRADER_SYSTEM, "--tools", "",
                    "--settings", self.settings, "--no-session-persistence",
                    "--output-format", "json", "--json-schema", GRADE_SCHEMA]
            if self.grader_strict:
                args.append("--strict-mcp-config")
            out, err, code = run_claude(args, prompt, self.env, tempfile.gettempdir(), 300)
            if code is not None and code < 0:
                raise Paused("interrupted")
            result = parse_result(out)
            if result and not result.get("is_error"):
                verdict = result.get("structured_output")
                if not isinstance(verdict, dict):
                    try:
                        verdict = json.loads(result.get("result") or "")
                    except ValueError:
                        verdict = None
                if isinstance(verdict, dict) and isinstance(verdict.get("pass"), bool):
                    return {"pass": verdict["pass"], "reason": str(verdict.get("reason", ""))}
            failure = str((result or {}).get("result") or err or out or "no output")
            kind = classify_failure(failure)
            if kind == "limit":
                raise Paused(clip(failure, 200))
            if kind == "auth":
                raise SetupError("Claude Code could not log in: %s" % clip(failure, 200))
            if result is None and self.grader_strict and "mcp" in failure.lower():
                self.grader_strict = False   # test mode still guards any connected tool
                continue
            if attempt < 2:
                time.sleep(30 * (attempt + 1))
        raise SetupError("The grader failed three times, so nothing was counted: %s" % clip(failure, 200))

    def one(self, label, task_id, rep):
        if self.pause.is_set():
            return None
        task = self.tasks[task_id]
        target = result_path(self.opts.results, label, task_id, rep)
        if has_result(target, task["hash"]):
            return target
        work = tempfile.mkdtemp(prefix="golden-run-")
        scratch = os.path.join(work, "scratch")
        os.makedirs(scratch)
        log_path = os.path.join(work, "test-mode-log.jsonl")
        started = time.time()
        try:
            outcome = self.session(task["task"], scratch, log_path, self.opts.timeout)
            log = read_log(log_path)
            files = scratch_files(scratch)
            final = outcome.get("final") or {}
            answer = str(final.get("result") or "")
            if outcome.get("timeout"):
                grade = {"pass": False, "reason": "Timed out after %d s." % self.opts.timeout}
            elif not final:
                grade = {"pass": False, "reason": "The session ended without an answer: %s"
                         % outcome.get("stderr", "")}
            else:
                grade = self.grade(task, answer, outcome["calls"], log, files)
        except Paused as limit:
            with self.lock:
                self.pause_text = str(limit)
            self.pause.set()
            return None
        finally:
            shutil.rmtree(work, ignore_errors=True)
        record = {
            "label": label, "task": task_id, "rep": rep, "hash": task["hash"],
            "kind": task["kind"], "agent": self.opts.agent, "permission_mode": self.mode,
            "cwd": os.path.realpath(self.opts.cwd),
            "started": started, "seconds": round(time.time() - started, 1),
            "turns": final.get("num_turns"), "answer": clip(answer, 20000),
            "tool_calls": outcome.get("calls", [])[:80], "test_mode_log": log[:120],
            "scratch_files": files, "grade": grade,
        }
        write_json(target, record)
        mark = "pass" if grade["pass"] else "FAIL"
        print("  task %s run %d: %s (%.0f s) %s" % (task_id, rep, mark, record["seconds"],
                                                   clip(grade.get("reason", ""), 140)), flush=True)
        return target

    def run_many(self, label, jobs):
        os.makedirs(os.path.join(self.opts.results, label), exist_ok=True)
        ignore = os.path.join(self.opts.results, ".gitignore")
        if not os.path.isfile(ignore):
            with open(ignore, "w", encoding="utf-8") as handle:
                handle.write("# Test transcripts can hold private text. Never commit them.\n*\n")
        waited = 0.0
        while True:
            self.pause.clear()
            pending = [j for j in jobs if not has_result(
                result_path(self.opts.results, label, *j), self.tasks[j[0]]["hash"])]
            if not pending:
                return
            try:
                self.canary()
            except Paused as limit:
                self.pause_text = str(limit)
                self.pause.set()
            if not self.pause.is_set():
                print("%s: %d test sessions to run, %d at a time." % (label, len(pending), self.opts.parallel),
                      flush=True)
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.opts.parallel) as pool:
                    list(pool.map(lambda job: self.one(label, *job), pending))
            if not self.pause.is_set():
                left = [j for j in pending if not has_result(
                    result_path(self.opts.results, label, *j), self.tasks[j[0]]["hash"])]
                if left:
                    raise SetupError("%d runs did not finish." % len(left))
                return
            if not self.opts.wait_on_limit or waited >= self.opts.max_wait_hours * 3600:
                raise Paused(self.pause_text)
            resume = time.strftime("%H:%M", time.localtime(time.time() + 900))
            print("Paused for the usage limit (%s). Trying again at %s." % (self.pause_text, resume),
                  flush=True)
            time.sleep(900)
            waited += 900


# ---------------------------------------------------------------- results and verdicts

def load_results(results, label):
    folder = os.path.join(results, label)
    found = {}
    if not os.path.isdir(folder):
        return found
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                record = json.load(handle)
        except (OSError, ValueError):
            continue
        found.setdefault(record.get("task"), []).append(record)
    return found


def summarise(records):
    runs = len(records)
    passes = sum(1 for r in records if r["grade"]["pass"])
    seconds = sum(r.get("seconds", 0) for r in records)
    return passes, runs, seconds


def verdict_for(before, after, reran):
    """One task: (passes, runs) before and after, and whether the extra runs are done."""
    b_pass, b_runs = before
    a_pass, a_runs = after
    b_rate = b_pass / b_runs if b_runs else 0.0
    a_rate = a_pass / a_runs if a_runs else 0.0
    if a_rate >= b_rate - 1e-9:
        return "holds", ""
    if not reran:
        return ("noisy", "failed in one run only") if a_runs - a_pass == 1 else ("worse", "")
    if a_rate >= b_rate - TOLERANCE - 1e-9:
        return "holds", "within %.1f after %d runs" % (TOLERANCE, a_runs)
    return "worse", "after %d runs" % a_runs


def last_kept(results):
    path = os.path.join(results, "last-kept")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            value = handle.read().strip()
            if value:
                return value
    return "baseline"


def jobs_for(tasks, results, label, reps, only, extra):
    existing = load_results(results, label)
    jobs = []
    for task in tasks:
        if only and task["id"] not in only:
            continue
        have = [r["rep"] for r in existing.get(task["id"], []) if r.get("hash") == task["hash"]]
        top = max(have) if have else 0
        wanted = range(top + 1, top + extra + 1) if extra else range(1, reps + 1)
        jobs.extend((task["id"], rep) for rep in wanted)
    return jobs


# ---------------------------------------------------------------- commands

def print_scores(results, label, tasks):
    found = load_results(results, label)
    total_p = total_r = 0
    print("\n%s" % label)
    for task in tasks:
        records = [r for r in found.get(task["id"], []) if r.get("hash") == task["hash"]]
        passes, runs, seconds = summarise(records)
        total_p += passes
        total_r += runs
        if runs:
            print("  task %-4s %-9s %d/%d passed, %.0f s a run" % (task["id"], task["kind"], passes,
                                                                  runs, seconds / runs))
    print("  total: %d/%d runs passed" % (total_p, total_r), flush=True)


def cmd_run(opts, tasks):
    runner = Runner(opts, tasks)
    only = set(x.strip() for x in opts.only.split(",") if x.strip())
    started = time.time()
    runner.run_many(opts.label, jobs_for(tasks, opts.results, opts.label, opts.reps, only, opts.extra))
    print_scores(opts.results, opts.label, tasks)
    print("Finished in %.0f min." % ((time.time() - started) / 60), flush=True)
    return 0


def current(records, task):
    return [r for r in records.get(task["id"], []) if r.get("hash") == task["hash"]]


def compare(tasks, before, after, base):
    """Rows per task, the tasks that need extra runs, the worse ones and the skipped ones."""
    rows, more, worse, skipped, incomplete = [], [], [], [], []
    for task in tasks:
        b, a = current(before, task), current(after, task)
        if len(a) < base:
            incomplete.append(("after", task["id"]))
            continue
        if len(b) < base:
            if before.get(task["id"]):
                skipped.append(task["id"])          # the task changed since that run
            else:
                incomplete.append(("before", task["id"]))
            continue
        if any(r["grade"].get("grader_failed") for r in a + b):
            raise SetupError("Task %s has a run the grader could not score. Delete that result file "
                             "and run again." % task["id"])
        b_sum, a_sum = summarise(b), summarise(a)
        reran = a_sum[1] > base
        state, note = verdict_for(b_sum[:2], a_sum[:2], reran)
        rows.append((task, b_sum, a_sum, state, note))
        if state == "noisy" or (reran and a_sum[1] < base + EXTRA_REPS):
            more.append((task["id"], a_sum[1]))
        if state == "worse":
            worse.append(task["id"])
    return rows, more, worse, skipped, incomplete


def cmd_check(opts, tasks):
    base = opts.reps
    before_label = opts.before or last_kept(opts.results)
    if before_label == opts.label:
        raise SetupError("Nothing to compare: %s is already the last kept run." % opts.label)
    before = load_results(opts.results, before_label)
    if not before:
        raise SetupError("No results for %s. Run `golden.py run %s` first." % (before_label, before_label))
    after = load_results(opts.results, opts.label)
    if not after:
        raise SetupError("No results for %s. Run `golden.py run %s` first." % (opts.label, opts.label))
    rows, more, worse, skipped, incomplete = compare(tasks, before, after, base)
    if incomplete:
        side = {s for s, _ in incomplete}
        names = ", ".join(i for _, i in incomplete)
        label = opts.label if "after" in side else before_label
        raise SetupError("%s is incomplete (tasks %s). Run `golden.py run %s` again to finish it."
                         % (label, names, label))
    if more and not opts.no_rerun:
        print("%s: %d task(s) failed in one run only; running each up to %d runs."
              % (opts.label, len(more), base + EXTRA_REPS), flush=True)
        jobs = [(task_id, rep) for task_id, have in more
                for rep in range(have + 1, base + EXTRA_REPS + 1)]
        Runner(opts, tasks).run_many(opts.label, jobs)
        after = load_results(opts.results, opts.label)
        rows, more, worse, skipped, incomplete = compare(tasks, before, after, base)
    if not rows:
        raise SetupError("No task could be compared between %s and %s." % (before_label, opts.label))
    print("\n%s against %s" % (opts.label, before_label))
    print("  %-6s %-9s %-7s %-7s %s" % ("task", "kind", "before", "after", "verdict"))
    for task, b_sum, a_sum, state, note in rows:
        print("  %-6s %-9s %-7s %-7s %s%s" % (task["id"], task["kind"], "%d/%d" % b_sum[:2],
                                             "%d/%d" % a_sum[:2], state, (" (%s)" % note) if note else ""))
    b_time = sum(r[1][2] for r in rows) / max(1, sum(r[1][1] for r in rows))
    a_time = sum(r[2][2] for r in rows) / max(1, sum(r[2][1] for r in rows))
    print("  time: %.0f s a run before, %.0f s after" % (b_time, a_time))
    folders = {r.get("cwd") for rs in list(before.values()) + list(after.values()) for r in rs if r.get("cwd")}
    if len(folders) > 1:
        print("  warning: the runs started in different folders: %s" % ", ".join(sorted(folders)))
    if skipped:
        print("  not compared (task changed since %s): %s" % (before_label, ", ".join(skipped)))
    failing = worse + [r[0]["id"] for r in rows if r[3] == "noisy"]
    if failing:
        print("WORSE: restore this change. Tasks: %s" % ", ".join(failing), flush=True)
        return 1
    with open(os.path.join(opts.results, "last-kept"), "w", encoding="utf-8") as handle:
        handle.write(opts.label + "\n")
    print("HOLDS: keep this change. %s is now the last kept run." % opts.label, flush=True)
    return 0


def cmd_list(opts, tasks):
    if not os.path.isdir(opts.results):
        print("No runs yet.")
        return 0
    kept = last_kept(opts.results)
    for label in sorted(os.listdir(opts.results)):
        if not os.path.isdir(os.path.join(opts.results, label)):
            continue
        records = [r for rs in load_results(opts.results, label).values() for r in rs]
        passes, runs, _ = summarise(records)
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(max((r.get("started", 0) for r in records),
                                                                   default=0)))
        print("%-28s %3d/%-3d passed  %s%s" % (label, passes, runs, when,
                                              "  (last kept)" if label == kept else ""))
    return 0


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tasks", default=os.path.join(HERE, "golden-tasks.md"))
    common.add_argument("--results", default=os.path.join(HERE, "results"))
    runs = argparse.ArgumentParser(add_help=False)
    runs.add_argument("label", help="a short name for this state of the crew, such as baseline or fold-decks")
    runs.add_argument("--agent", default="chief-of-staff", help="the main-loop agent to test")
    runs.add_argument("--cwd", default=os.getcwd(), help="folder the test sessions start in")
    runs.add_argument("--parallel", type=int, default=3, help="sessions at a time")
    runs.add_argument("--timeout", type=int, default=900, help="seconds before a session counts as failed")
    runs.add_argument("--permission-mode", default="bypassPermissions",
                      help="permission mode for test sessions; test mode still blocks every change. "
                           "Use 'user' to keep your own setting")
    runs.add_argument("--wait-on-limit", action="store_true", help="wait out a usage limit and continue")
    runs.add_argument("--max-wait-hours", type=float, default=8.0)
    runs.add_argument("--use-api-key", action="store_true",
                      help="keep ANTHROPIC_API_KEY even when a Claude login exists")
    parser = argparse.ArgumentParser(description="Run the golden tasks in test sessions.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", parents=[common, runs], help="run the golden tasks")
    run.add_argument("--reps", type=int, default=2, help="runs of each task")
    run.add_argument("--only", default="", help="comma-separated task numbers")
    run.add_argument("--extra", type=int, default=0, help="add this many runs to tasks already run")
    check = sub.add_parser("check", parents=[common, runs], help="compare with the last kept run")
    check.add_argument("--before", default="", help="compare with this run instead of the last kept one")
    check.add_argument("--reps", type=int, default=DEFAULT_REPS, help="runs of each task in a normal run")
    check.add_argument("--no-rerun", action="store_true", help="do not rerun tasks that failed once")
    sub.add_parser("list", parents=[common], help="show every run")
    return parser


def main(argv=None):
    parser = build_parser()
    opts = parser.parse_args(argv)
    if opts.command in ("run", "check") and not re.match(r"^[A-Za-z0-9_.-]+$", opts.label):
        parser.error("labels use letters, digits, '.', '_' and '-' only")
    if opts.command in ("run", "check") and opts.parallel < 1:
        parser.error("--parallel must be 1 or more")
    try:
        tasks = load_tasks(opts.tasks)
        if opts.command == "run":
            return cmd_run(opts, tasks)
        if opts.command == "check":
            return cmd_check(opts, tasks)
        return cmd_list(opts, tasks)
    except Paused as limit:
        print("PAUSED for the usage limit: %s\nRun the same command again after it resets; it "
              "continues from its last result." % limit, flush=True)
        return PAUSED
    except KeyboardInterrupt:
        print("Interrupted. Run the same command again; it continues from its last result.", flush=True)
        return PAUSED
    except SetupError as problem:
        print("Cannot run: %s" % problem, file=sys.stderr, flush=True)
        return 3
    except Exception as error:  # never let a crash read as WORSE
        print("Cannot run: unexpected error: %s: %s" % (type(error).__name__, error),
              file=sys.stderr, flush=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
