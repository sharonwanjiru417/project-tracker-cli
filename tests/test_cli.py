"""End-to-end tests of the CLI using a temporary data file."""

import contextlib
import io
import json
import os
import tempfile
import unittest

from main import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "data.json")

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *argv):
        """Run the CLI, returning (exit_code, captured_stdout)."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["--data-file", self.path, *argv])
        return code, buffer.getvalue()

    def test_full_workflow_persists(self):
        self.assertEqual(self.run_cli("add-user", "--name", "Alex")[0], 0)
        self.assertEqual(self.run_cli("add-project", "--user", "Alex",
                                      "--title", "CLI Tool", "--due-date", "2030-01-01")[0], 0)
        self.assertEqual(self.run_cli("add-task", "--project", "CLI Tool",
                                      "--title", "Implement add-task", "--assign", "Alex")[0], 0)
        self.assertEqual(self.run_cli("complete-task", "--id", "1")[0], 0)

        with open(self.path) as handle:
            saved = json.load(handle)
        self.assertEqual(saved["tasks"][0]["status"], "completed")
        self.assertEqual(saved["projects"][0]["due_date"], "2030-01-01")

        code, out = self.run_cli("list-projects", "--user", "Alex")
        self.assertEqual(code, 0)
        self.assertIn("CLI Tool", out)

    def test_search_finds_project(self):
        self.run_cli("add-user", "--name", "Alex")
        self.run_cli("add-project", "--user", "Alex", "--title", "Website")
        code, out = self.run_cli("search-projects", "--query", "web")
        self.assertEqual(code, 0)
        self.assertIn("Website", out)

    def test_unknown_user_returns_error_code(self):
        code, out = self.run_cli("add-project", "--user", "Ghost", "--title", "X")
        self.assertEqual(code, 1)
        self.assertIn("not found", out)

    def test_bad_date_returns_error_code(self):
        self.run_cli("add-user", "--name", "Alex")
        code, out = self.run_cli("add-project", "--user", "Alex",
                                 "--title", "X", "--due-date", "someday")
        self.assertEqual(code, 1)
        self.assertIn("Could not understand date", out)

    def test_no_command_prints_help(self):
        code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("COMMAND", out)

    def test_corrupt_file_does_not_crash(self):
        with open(self.path, "w") as handle:
            handle.write("garbage")
        self.assertEqual(self.run_cli("add-user", "--name", "Alex")[0], 0)


if __name__ == "__main__":
    unittest.main()
