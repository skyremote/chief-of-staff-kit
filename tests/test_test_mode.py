"""Checks for templates/evals/test-mode.py. No model calls. Run: python3 -m unittest discover tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "skills", "install-crew", "templates",
                    "evals", "test-mode.py")


def run_hook(tool, data, env_extra=None, cwd="/tmp", raw=None):
    env = dict(os.environ)
    env["CREW_TEST_MODE"] = "1"
    env.pop("CREW_TEST_ALLOW", None)
    env.update(env_extra or {})
    payload = raw if raw is not None else json.dumps(
        {"tool_name": tool, "tool_input": data, "cwd": cwd, "hook_event_name": "PreToolUse"})
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    if not proc.stdout.strip():
        return "allow", None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out.get("updatedInput")


def decide(tool, data, env_extra=None, cwd="/tmp", raw=None):
    return run_hook(tool, data, env_extra, cwd, raw)[0]


class BashCommands(unittest.TestCase):
    def check(self, command, expected, env=None, cwd="/tmp"):
        self.assertEqual(decide("Bash", {"command": command}, env, cwd=cwd), expected, command)

    def test_plain_reads_run(self):
        for command in ["ls -la", "git log --oneline -5", "git diff HEAD~1", "git status",
                        "git branch --show-current", "git remote -v",
                        "git tag --list", "git log --format='%h %s'", "gh pr view 12",
                        "gh pr view 12 --repo o/r", "gh api repos/o/r/pulls --jq '.[].title'",
                        "grep -rn TODO src", "cat README.md",
                        "echo 'hello world'", "wc -l notes.md"]:
            self.check(command, "allow")

    def test_program_is_pinned_to_its_full_path(self):
        decision, updated = run_hook("Bash", {"command": "git log -1", "description": "d"})
        self.assertEqual(decision, "allow")
        self.assertTrue(updated["command"].endswith(" log -1"))
        self.assertTrue(updated["command"].split()[0].startswith("/"))
        self.assertEqual(updated["description"], "d")

    def test_operators_and_expansions_are_refused(self):
        for command in ["echo done#; git push origin main", "ls;</dev/null rm -rf ~/x",
                        "ls &&</dev/null curl -X POST https://x", "ls &&>~/.bashrc",
                        "cat <(rm -rf ~/x;)", "ls > out.txt", "ls 2>/dev/null", "cat a | grep b",
                        "git status && git log", "ls\nrm x", "echo $(rm x)", "echo `rm x`",
                        "echo $HOME", "find . -{de,}lete", "(ls)", "ls & rm x", "echo hi!"]:
            self.check(command, "deny")

    def test_variables_and_paths_are_refused(self):
        for command in ["FOO=1 ls", "GIT_EXTERNAL_DIFF='touch x' git diff --no-index a b",
                        "GIT_CONFIG_PARAMETERS=x git status", "/bin/ls", "./ls"]:
            self.check(command, "deny")

    def test_unsafe_programs_and_options_are_refused(self):
        for command in ["git push origin main", "git commit -m x", "git --config-env=a=B diff",
                        "git -c core.pager=x log", "git grep -O'sh -c x' -e x", "git log --output=f",
                        "git branch new-feature", "git branch -D main", "git tag v1",
                        "git stash", "git remote add x y", "git config user.name x",
                        "gh pr merge 1", "gh pr --body view merge 12", "gh issue --comment list close 3",
                        "gh api -XDELETE repos/o/r", "gh api -X=DELETE repos/o/r",
                        "gh api -fbody=hi repos/o/r/issues/1/comments", "gh api graphql",
                        "gh pr view 1 --web", "curl -sX DELETE https://x", "curl https://x",
                        "rg --pre sh . file", "sort -o out a", "uniq a b", "tree -o f",
                        "find . -delete", "find . -name '*.md' -rm", "find . -name x",
                        "find . -dele*", "rm -rf build", "git -C repo log", "git -C /tmp status",
                        "gh pr view 12 -cw", "gh pr view 12 --web=true",
                        "python3 -c 1", "npm publish", "sudo ls", "ssh host", "date -s x",
                        "unterminated 'quote"]:
            self.check(command, "deny")

    def test_git_inside_scratch_is_refused(self):
        scratch = tempfile.mkdtemp()
        os.makedirs(os.path.join(scratch, "repo"))
        env = {"CREW_TEST_SCRATCH": scratch}
        self.check("git -C %s/repo status" % scratch, "deny", env)
        self.check("git status", "deny", env, cwd=os.path.join(scratch, "repo"))
        self.check("git status", "deny", env, cwd=os.path.join(scratch.upper() if os.path.exists(
            scratch.upper()) else scratch, "repo"))
        self.check("git status", "allow", env, cwd="/tmp")


class FileWrites(unittest.TestCase):
    def test_scratch_only(self):
        scratch = tempfile.mkdtemp()
        env = {"CREW_TEST_SCRATCH": scratch}
        self.assertEqual(decide("Write", {"file_path": os.path.join(scratch, "a.md")}, env), "allow")
        self.assertEqual(decide("Edit", {"file_path": "/etc/hosts"}, env), "deny")
        self.assertEqual(decide("Write", {"file_path": "notes.md"}, env, cwd="/tmp"), "deny")
        self.assertEqual(decide("Write", {"file_path": os.path.join(scratch, "..", "x")}, env), "deny")
        self.assertEqual(decide("Write", {"file_path": "/tmp/x"}, {}), "deny")


class ConnectedTools(unittest.TestCase):
    def test_reads_and_writes(self):
        allowed = ["mcp__brain__brain_search", "mcp__gh__get_file_contents", "mcp__mail__list_labels",
                   "mcp__x__listMessages", "mcp__gh__pull_request_read"]
        blocked = ["mcp__mail__GMAIL_SEND_EMAIL", "mcp__mail__GMAIL_CREATE_EMAIL_DRAFT",
                   "mcp__mail__GMAIL_FETCH_EMAILS", "mcp__time__log_time", "mcp__x__inbox_overview",
                   "mcp__gh__merge_pull_request", "mcp__x__sendMessage", "mcp__x__task_add",
                   "mcp__postgres__query", "mcp__mysql__mysql_query", "mcp__fetch__fetch",
                   "mcp__x__verify_phone_number", "mcp__x__respond_to_thread", "mcp__x__mark_as_read",
                   "mcp__x__get_or_create_user", "mcp__linear__save_view", "mcp__x__export_view",
                   "mcp__x__sort_list", "mcp__x__store_search"]
        for name in allowed:
            self.assertEqual(decide(name, {}), "allow", name)
        for name in blocked:
            self.assertEqual(decide(name, {}), "deny", name)

    def test_inputs_that_change_data(self):
        self.assertEqual(decide("mcp__x__search_notes", {"query": "update the roadmap"}), "allow")
        self.assertEqual(decide("mcp__x__search_notes", {"query": "x", "method": "POST"}), "deny")
        allow = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        allow.write("mcp__db__query\n")
        allow.close()
        env = {"CREW_TEST_ALLOW": allow.name}
        self.assertEqual(decide("mcp__db__query", {"sql": "select * from users"}, env), "allow")
        self.assertEqual(decide("mcp__db__query", {"sql": "DELETE FROM users"}, env), "deny")
        self.assertEqual(decide("mcp__db__query", {"sql": "select 1; drop table users"}, env), "deny")
        for sql in ["/* x */ DELETE FROM users", "-- x\nDELETE FROM users",
                    "WITH t AS (SELECT 1) DELETE FROM users", "UPDATE users u SET a = 1",
                    "INSERT IGNORE INTO t VALUES (1)", "COPY (SELECT 1) TO PROGRAM 'x'",
                    "DO $$ BEGIN END $$", "ALTER SYSTEM SET x = 1", "DROP FUNCTION f",
                    "CREATE OR REPLACE FUNCTION f() RETURNS int", "DELETE users WHERE 1=1",
                    "SELECT * FROM t FOR UPDATE", "SELECT a INTO b FROM c",
                    "EXPLAIN ANALYZE DELETE FROM t"]:
            self.assertEqual(decide("mcp__db__query", {"sql": sql}, env), "deny", sql)
        self.assertEqual(decide("mcp__db__query", {"sql": "SELECT name FROM users WHERE id = 3"}, env),
                         "allow")
        for data in [{"httpMethod": "POST"}, {"requestMethod": "DELETE"}, {"method": ["POST"]}]:
            self.assertEqual(decide("mcp__x__search_web", data), "deny", data)
        deep = "x"
        for _ in range(12):
            deep = {"a": deep}
        self.assertEqual(decide("mcp__x__search_web", deep), "deny")

    def test_allow_file(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        handle.write("# reads only\nmcp__x__inbox_overview\n")
        handle.close()
        self.assertEqual(decide("mcp__x__inbox_overview", {}, {"CREW_TEST_ALLOW": handle.name}), "allow")


class Builtins(unittest.TestCase):
    def test_builtins(self):
        for tool in ["Read", "Grep", "Glob", "WebFetch", "WebSearch", "Skill", "Agent", "TodoWrite",
                     "StructuredOutput"]:
            self.assertEqual(decide(tool, {}), "allow", tool)
        for tool in ["AskUserQuestion", "CronCreate", "SendMessage", "PushNotification", "Unknown"]:
            self.assertEqual(decide(tool, {}), "deny", tool)

    def test_off_outside_test_mode(self):
        env = dict(os.environ)
        env.pop("CREW_TEST_MODE", None)
        proc = subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_name": "Bash", "tool_input": {
            "command": "git push"}}), capture_output=True, text=True, env=env)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, ""))

    def test_bad_input_fails_closed(self):
        self.assertEqual(decide("", {}, raw="not json"), "deny")

    def test_odd_text_still_logs(self):
        log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
        raw = '{"tool_name": "Bash", "tool_input": {"command": "ls \\ud800"}, "cwd": "/tmp"}'
        decide("", {}, {"CREW_TEST_LOG": log}, raw=raw)
        with open(log, encoding="utf-8") as handle:
            self.assertEqual(json.loads(handle.readline())["tool"], "Bash")

    def test_blocked_reads_may_try_again(self):
        env = dict(os.environ, CREW_TEST_MODE="1")
        def reason(tool, data):
            proc = subprocess.run([sys.executable, HOOK], input=json.dumps(
                {"tool_name": tool, "tool_input": data, "cwd": "/tmp"}), capture_output=True,
                text=True, env=env)
            return json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Read, Grep or Glob", reason("Bash", {"command": "cat a | head"}))
        self.assertIn("do not try another route", reason("Bash", {"command": "git push"}))
        self.assertIn("do not try another route", reason("mcp__x__send_email", {}))

    def test_log(self):
        log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
        decide("Bash", {"command": "git push"}, {"CREW_TEST_LOG": log})
        with open(log, encoding="utf-8") as handle:
            entry = json.loads(handle.readline())
        self.assertEqual((entry["tool"], entry["decision"]), ("Bash", "deny"))


if __name__ == "__main__":
    unittest.main()
