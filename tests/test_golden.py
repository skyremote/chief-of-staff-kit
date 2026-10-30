"""Checks for templates/evals/golden.py. No model calls. Run: python3 -m unittest discover tests"""

import importlib.util
import json
import os
import tempfile
import unittest

PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "install-crew", "templates",
                    "evals", "golden.py")
spec = importlib.util.spec_from_file_location("golden", PATH)
golden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(golden)

TEMPLATE = os.path.join(os.path.dirname(PATH), "golden-tasks.md")


def write(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    return handle.name


class Tasks(unittest.TestCase):
    def test_table(self):
        path = write("# Golden tasks\n\n## Tasks\n\n"
                     "| # | Task (as you would ask it) | Done means | Kind | Division or craft |\n"
                     "|---|---|---|---|---|\n"
                     "| 1 | Draft a reply to the supplier | A draft with one ask, no send attempted | everyday | Biz |\n"
                     "| 2 | Use a \\| pipe | Says pipe | rule | Ops |\n"
                     "| 3 | | | | |\n\n## Results\n\n| 9 | Not a task | x | y | z |\n")
        tasks = golden.load_tasks(path)
        self.assertEqual([t["id"] for t in tasks], ["1", "2"])
        self.assertEqual(tasks[1]["task"], "Use a | pipe")
        self.assertEqual(tasks[1]["kind"], "rule")

    def test_missing_done_line(self):
        path = write("## Tasks\n\n| # | Task | Done means |\n|---|---|---|\n| 1 | Do it | |\n")
        with self.assertRaises(golden.SetupError):
            golden.load_tasks(path)

    def test_template_parses_once_filled(self):
        with open(TEMPLATE, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("## Tasks", text)
        with self.assertRaises(golden.SetupError):
            golden.load_tasks(TEMPLATE)   # the shipped template has no tasks yet


class Verdicts(unittest.TestCase):
    def test_rules(self):
        v = golden.verdict_for
        self.assertEqual(v((2, 2), (2, 2), False)[0], "holds")
        self.assertEqual(v((1, 2), (2, 2), False)[0], "holds")
        self.assertEqual(v((2, 2), (1, 2), False)[0], "noisy")
        self.assertEqual(v((1, 2), (0, 2), False)[0], "worse")
        self.assertEqual(v((2, 2), (0, 2), False)[0], "worse")
        self.assertEqual(v((2, 2), (5, 6), True)[0], "holds")
        self.assertEqual(v((2, 2), (4, 6), True)[0], "worse")
        self.assertEqual(v((0, 2), (0, 2), False)[0], "holds")


def record(results, label, task, rep, passed, digest="h", **extra):
    os.makedirs(os.path.join(results, label), exist_ok=True)
    data = {"task": task, "rep": rep, "hash": digest, "seconds": 1, "grade": {"pass": passed}}
    data["grade"].update(extra)
    golden.write_json(golden.result_path(results, label, task, rep), data)


class Checks(unittest.TestCase):
    def setUp(self):
        self.results = tempfile.mkdtemp()
        self.tasks = [{"id": "1", "task": "t", "done": "d", "kind": "everyday", "hash": "h"},
                      {"id": "2", "task": "u", "done": "e", "kind": "rule", "hash": "h"}]
        for task in ("1", "2"):
            for rep in (1, 2):
                record(self.results, "baseline", task, rep, True)

    def opts(self, label, **extra):
        values = dict(label=label, before="", reps=2, no_rerun=True, results=self.results)
        values.update(extra)
        return type("Opts", (), values)()

    def test_holds_and_records_last_kept(self):
        for task in ("1", "2"):
            for rep in (1, 2):
                record(self.results, "fold-a", task, rep, True)
        self.assertEqual(golden.cmd_check(self.opts("fold-a"), self.tasks), 0)
        self.assertEqual(golden.last_kept(self.results), "fold-a")

    def test_incomplete_run_is_refused(self):
        record(self.results, "fold-b", "1", 1, True)
        record(self.results, "fold-b", "1", 2, True)
        with self.assertRaises(golden.SetupError):
            golden.cmd_check(self.opts("fold-b"), self.tasks)
        self.assertEqual(golden.last_kept(self.results), "baseline")

    def test_worse_does_not_record(self):
        for task in ("1", "2"):
            for rep in (1, 2):
                record(self.results, "fold-c", task, rep, task == "1")
        self.assertEqual(golden.cmd_check(self.opts("fold-c"), self.tasks), 1)
        self.assertEqual(golden.last_kept(self.results), "baseline")

    def test_grader_failure_is_refused(self):
        for task in ("1", "2"):
            for rep in (1, 2):
                record(self.results, "fold-d", task, rep, False, grader_failed=True)
        with self.assertRaises(golden.SetupError):
            golden.cmd_check(self.opts("fold-d"), self.tasks)

    def test_partial_rerun_is_topped_up(self):
        for rep, passed in ((1, True), (2, False), (3, True), (4, False)):
            record(self.results, "fold-e", "1", rep, passed)
        for rep in (1, 2):
            record(self.results, "fold-e", "2", rep, True)
        before = golden.load_results(self.results, "baseline")
        after = golden.load_results(self.results, "fold-e")
        rows, more, worse, skipped, incomplete = golden.compare(self.tasks, before, after, 2)
        self.assertEqual(more, [("1", 4)])


class Streams(unittest.TestCase):
    def test_parse(self):
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "a", "name": "Bash", "input": {"command": "git push"}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "a", "is_error": True,
                 "content": "PreToolUse:Bash hook error: Test mode: Bash blocked"}]}},
            {"type": "result", "subtype": "success", "is_error": False, "result": "Blocked."},
        ]
        calls, final = golden.parse_stream("\n".join(json.dumps(x) for x in lines) + "\nnoise\n")
        self.assertEqual(calls[0]["tool"], "Bash")
        self.assertTrue(calls[0]["error"])
        self.assertEqual(final["result"], "Blocked.")

    def test_result_json(self):
        self.assertEqual(golden.parse_result('warning\n{"type": "result", "result": "x"}')["result"], "x")
        self.assertEqual(golden.parse_result(json.dumps({"type": "result", "a": 1}, indent=2))["a"], 1)

    def test_failures(self):
        c = golden.classify_failure
        self.assertEqual(c("Claude AI usage limit reached|1700000000"), "limit")
        self.assertEqual(c("You've hit your limit · resets 3pm"), "limit")
        self.assertEqual(c("API Error: 529 overloaded_error"), "transient")
        self.assertEqual(c("Invalid API key · Please run /login"), "auth")
        self.assertEqual(c("Something else"), "other")


class Jobs(unittest.TestCase):
    def test_extra_runs_continue_numbering(self):
        results = tempfile.mkdtemp()
        os.makedirs(os.path.join(results, "x"))
        task = {"id": "1", "task": "t", "done": "d", "kind": "everyday", "hash": "h"}
        for rep in (1, 2):
            golden.write_json(golden.result_path(results, "x", "1", rep),
                              {"task": "1", "rep": rep, "hash": "h", "grade": {"pass": True}})
        self.assertEqual(golden.jobs_for([task], results, "x", 0, {"1"}, 4),
                         [("1", 3), ("1", 4), ("1", 5), ("1", 6)])
        self.assertEqual(golden.jobs_for([task], results, "x", 2, set(), 0), [("1", 1), ("1", 2)])


if __name__ == "__main__":
    unittest.main()
