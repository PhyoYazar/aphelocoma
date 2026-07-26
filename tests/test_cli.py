import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
APH = REPOSITORY / "bin" / "aph"
HAMILTON_FIXTURE = REPOSITORY / "tests" / "fixtures" / "hamilton" / "current"


class AphRunner:
    """Run the shipped entrypoint as a subprocess with an isolated HOME."""

    def run_aph(self, *arguments, environment=None, cwd=None):
        with tempfile.TemporaryDirectory(prefix="aph home 'quoted' ") as directory:
            home = Path(directory)
            env = os.environ.copy()
            env["HOME"] = str(home)
            for name in ("APHELOCOMA_HOME", "APHELOCOMA_ROOT", "NO_COLOR"):
                env.pop(name, None)
            if environment:
                env.update(environment)
            completed = subprocess.run(
                [sys.executable, str(APH), *arguments],
                cwd=str(home if cwd is None else cwd),
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )
            return completed, home


class CliSubprocessTests(AphRunner, unittest.TestCase):
    def test_help_exposes_only_hamilton_commands(self):
        completed, _ = self.run_aph("help")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        for command in (
            "deploy",
            "undeploy",
            "doctor",
            "status",
            "update",
            "uninstall",
            "version",
            "help",
        ):
            self.assertRegex(completed.stdout, rf"\b{command}\b")
        for removed in (
            "setup",
            "add",
            "sync",
            "view",
            "projects",
            "skills",
            "context",
        ):
            self.assertNotRegex(completed.stdout, rf"\b{removed}\b")

    def test_empty_command_and_help_option_show_help(self):
        empty, _ = self.run_aph()
        option, _ = self.run_aph("--help")

        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertEqual(option.returncode, 0, option.stderr)
        self.assertEqual(empty.stdout, option.stdout)

    def test_version_uses_the_checked_out_version_file(self):
        completed, _ = self.run_aph("version")
        expected = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, f"aph {expected}\n")

    def test_unknown_and_incomplete_commands_are_actionable_failures(self):
        unknown, _ = self.run_aph("setup")
        incomplete, _ = self.run_aph("deploy")
        unsupported, _ = self.run_aph("deploy", "cursor")

        self.assertEqual(unknown.returncode, 1)
        self.assertIn("Unknown command", unknown.stderr)
        self.assertEqual(incomplete.returncode, 1)
        self.assertIn("required", incomplete.stderr)
        self.assertEqual(unsupported.returncode, 1)
        self.assertIn("cursor", unsupported.stderr)

    def test_lifecycle_commands_are_implemented_not_placeholders(self):
        deploy, _ = self.run_aph("deploy", "claude")
        undeploy, _ = self.run_aph("undeploy", "codex")
        update, _ = self.run_aph("update")
        uninstall, _ = self.run_aph("uninstall")

        self.assertEqual(deploy.returncode, 0, deploy.stderr)
        self.assertEqual(undeploy.returncode, 0, undeploy.stderr)
        self.assertEqual(update.returncode, 1)
        self.assertIn("not installed", update.stderr.lower())
        self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
        for completed in (deploy, undeploy, update, uninstall):
            self.assertNotIn("not available", completed.stderr)

    def test_legacy_home_with_spaces_and_apostrophe_is_ignored_and_untouched(self):
        with tempfile.TemporaryDirectory(prefix="aph locations ") as directory:
            base = Path(directory)
            active = base / "active root"
            legacy = base / "Alex's legacy data"
            legacy.mkdir()
            sentinel = legacy / "keep me.txt"
            sentinel.write_text("untouched", encoding="utf-8")

            completed, _ = self.run_aph(
                "version",
                environment={
                    "APHELOCOMA_ROOT": str(active),
                    "APHELOCOMA_HOME": str(legacy),
                },
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(str(legacy), completed.stderr)
            self.assertIn("protected legacy", completed.stderr.lower())
            self.assertIn("ignored", completed.stderr.lower())
            self.assertFalse(active.exists())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "untouched")

    def test_noninteractive_output_contains_no_ansi_with_or_without_no_color(self):
        normal, _ = self.run_aph("help")
        no_color, _ = self.run_aph("help", environment={"NO_COLOR": "1"})
        ansi = re.compile(r"\x1b\[[0-9;]*m")

        self.assertIsNone(ansi.search(normal.stdout + normal.stderr))
        self.assertIsNone(ansi.search(no_color.stdout + no_color.stderr))
        self.assertEqual(normal.stdout, no_color.stdout)

    def test_doctor_json_is_machine_readable_and_reports_missing_git(self):
        with tempfile.TemporaryDirectory(prefix="aph empty path ") as directory:
            completed, _ = self.run_aph(
                "doctor",
                "--json",
                environment={"PATH": directory, "NO_COLOR": "1"},
            )

        self.assertEqual(completed.returncode, 1, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"], "action_required")
        self.assertEqual(
            [check["id"] for check in report["checks"]][:5],
            ["python", "git", "os", "aphelocoma_version", "hamilton_definition"],
        )
        git = next(check for check in report["checks"] if check["id"] == "git")
        self.assertEqual(git["status"], "error")
        self.assertIn("Install Git", git["remediation"])

    def test_healthy_doctor_has_human_and_json_contracts(self):
        human, _ = self.run_aph("doctor")
        machine, _ = self.run_aph("doctor", "--json")

        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertIn("Aphelocoma doctor: healthy", human.stdout)
        self.assertIn("[ok] Python", human.stdout)
        self.assertEqual(machine.returncode, 0, machine.stderr)
        report = json.loads(machine.stdout)
        self.assertEqual(report["status"], "healthy")
        self.assertTrue(all(check["status"] == "ok" for check in report["checks"]))

    def test_subcommand_help_is_successful(self):
        for command in (
            "deploy",
            "undeploy",
            "doctor",
            "status",
            "update",
            "uninstall",
            "version",
        ):
            with self.subTest(command=command):
                completed, _ = self.run_aph(command, "--help")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn(f"aph {command}", completed.stdout)


class CliStatusBoardTests(AphRunner, unittest.TestCase):
    """`aph status` renders the PROTOCOL.md §5.6 board without writing."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="aph status project ")
        self.addCleanup(self.tempdir.cleanup)
        self.project = Path(self.tempdir.name) / "project"
        shutil.copytree(HAMILTON_FIXTURE, self.project)

    def state_digests(self):
        state = self.project / ".aphelocoma"
        return {
            path.relative_to(state).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(state.rglob("*"))
            if path.is_file()
        }

    def write_metadata(self, **changes):
        path = self.project / ".aphelocoma" / "hamilton.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata.update(changes)
        path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    def write_tasks(self, tasks):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text(encoding="utf-8"))
        board["tasks"] = tasks
        path.write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")

    def sample_tasks(self):
        return [
            {
                "id": "T1",
                "title": "Ship the base",
                "owner": "fullstack-developer#2",
                "status": "done",
                "dependencies": [],
            },
            {
                "id": "T2",
                "title": "Unblock the pipeline",
                "owner": "devops-engineer",
                "status": "blocked",
                "dependencies": [],
            },
            {
                "id": "T3",
                "title": "Wait on the pipeline",
                "owner": "qa-engineer",
                "status": "pending",
                "dependencies": ["T2"],
            },
            {
                "id": "T4",
                "title": "Render the board",
                "owner": "fullstack-developer#1",
                "status": "assigned",
                "dependencies": ["T1"],
            },
        ]

    def test_board_reports_only_the_stage_and_the_task_list(self):
        completed, _ = self.run_aph("status", str(self.project))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        board = completed.stdout
        self.assertIn("fixture-current", board)
        self.assertRegex(board, r"(?m)^Phase\s+done\s*$")
        self.assertIn("1 of 1 tasks done", board)
        self.assertRegex(board, r"(?m)^\s+\[done\]\s+T1\s+Fixture task\s*$")
        for removed in ("schema 1", "protocol 1.0.0", "visibility", "Repo"):
            self.assertNotIn(removed, board)
        self.assertNotRegex(board, r"(?m)^Blocked\b")
        self.assertNotRegex(board, r"(?m)^Next\b")

    def test_blocked_task_still_reads_as_blocked_in_its_own_row(self):
        self.write_tasks(self.sample_tasks())

        completed, _ = self.run_aph("status", str(self.project))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        board = completed.stdout
        self.assertIn("1 of 4 tasks done", board)
        self.assertRegex(
            board, r"(?m)^\s+\[blocked\]\s+T2\s+Unblock the pipeline\s*$"
        )
        self.assertIn("[assigned]", board)
        self.assertIn("[pending]", board)
        self.assertNotRegex(board, r"(?m)^Blocked\b")

    def test_write_regenerates_the_status_file_and_names_it_on_stderr(self):
        self.write_tasks(self.sample_tasks())
        status_file = self.project / ".aphelocoma" / "STATUS.md"

        printed, _ = self.run_aph("status", str(self.project))
        written, _ = self.run_aph("status", str(self.project), "--write")

        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertEqual(written.stdout, printed.stdout)
        self.assertIn("STATUS.md", written.stderr)
        self.assertTrue(status_file.is_file())
        report = status_file.read_text(encoding="utf-8")
        self.assertIn("1 of 4 tasks done", report)
        for task in self.sample_tasks():
            self.assertIn(task["title"], report)
        self.assertRegex(report, r"(?m)^Generated \S+ from ledger seq 9\b")

    def assert_status_file_is_committable(self):
        """The board must exist as a file and must not be ignored by Git.

        `git check-ignore` answers about a pathname, not about a file, so it
        exits 1 just the same when nothing was ever written. The existence
        check is what makes the ignore check mean anything.
        """

        status_file = self.project / ".aphelocoma" / "STATUS.md"
        self.assertTrue(
            status_file.is_file(),
            f"--write must have produced {status_file} to commit",
        )
        ignored = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "check-ignore",
                "-q",
                ".aphelocoma/STATUS.md",
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(ignored.returncode, 1, "STATUS.md must stay committable")

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_written_status_file_is_committable_not_ignored(self):
        subprocess.run(
            ["git", "init", "-q", str(self.project)],
            check=False,
            capture_output=True,
        )
        self.run_aph("status", str(self.project), "--write")

        self.assert_status_file_is_committable()

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_committable_check_fails_when_no_board_was_written(self):
        subprocess.run(
            ["git", "init", "-q", str(self.project)],
            check=False,
            capture_output=True,
        )
        self.run_aph("status", str(self.project))

        with self.assertRaises(AssertionError):
            self.assert_status_file_is_committable()

    def unwritable_state(self):
        """Make `.aphelocoma/` readable but not writable for one run."""

        state = self.project / ".aphelocoma"
        original = state.stat().st_mode
        state.chmod(0o500)
        self.addCleanup(state.chmod, original)
        return state

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root ignores directory permissions",
    )
    def test_failed_write_still_prints_the_board(self):
        self.write_tasks(self.sample_tasks())
        printed, _ = self.run_aph("status", str(self.project))
        state = self.unwritable_state()

        failed, _ = self.run_aph("status", str(self.project), "--write")

        self.assertEqual(failed.returncode, 1)
        self.assertEqual(failed.stdout, printed.stdout)
        self.assertIn("1 of 4 tasks done", failed.stdout)
        self.assertIn("STATUS.md", failed.stderr)
        self.assertIn("Fix:", failed.stderr)
        self.assertFalse((state / "STATUS.md").exists())

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root ignores directory permissions",
    )
    def test_failed_write_leaves_stdout_one_parseable_json_document(self):
        plain, _ = self.run_aph("status", str(self.project), "--json")
        self.unwritable_state()

        failed, _ = self.run_aph("status", str(self.project), "--json", "--write")

        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout), json.loads(plain.stdout))
        self.assertIn("STATUS.md", failed.stderr)
        self.assertIn("Fix:", failed.stderr)

    def test_write_leaves_json_output_untouched(self):
        plain, _ = self.run_aph("status", str(self.project), "--json")
        written, _ = self.run_aph("status", str(self.project), "--json", "--write")

        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertEqual(json.loads(written.stdout), json.loads(plain.stdout))
        self.assertTrue((self.project / ".aphelocoma" / "STATUS.md").is_file())

    def test_json_output_follows_the_doctor_convention(self):
        completed, _ = self.run_aph("status", str(self.project), "--json")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["project"],
            {
                "name": "fixture-current",
                "phase": "done",
                "schema_version": 1,
                "protocol_version": "1.0.0",
                "visibility": "tracked",
            },
        )
        self.assertEqual(report["progress"], {"done": 1, "total": 1})
        self.assertEqual(
            report["tasks"],
            [
                {
                    "id": "T1",
                    "title": "Fixture task",
                    "status": "done",
                    "owner": "fullstack-developer",
                    "dependencies": [],
                }
            ],
        )
        self.assertEqual(report["blocked"], [])
        self.assertIsNone(report["next"])
        self.assertEqual(report["repo"]["state"], "absent")
        self.assertIsNone(report["repo"]["branch"])
        self.assertIn("not in a Git repository", report["repo"]["summary"])

    def test_default_path_is_the_current_directory(self):
        completed, _ = self.run_aph("status", cwd=self.project)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("fixture-current", completed.stdout)

    def test_status_without_write_never_writes_to_project_state(self):
        subprocess.run(
            ["git", "init", "-q", str(self.project)],
            check=False,
            capture_output=True,
        )
        self.run_aph("status", str(self.project), "--write")
        before = self.state_digests()

        self.run_aph("status", str(self.project))
        self.run_aph("status", str(self.project), "--json")
        self.run_aph("status", cwd=self.project)

        self.assertEqual(self.state_digests(), before)
        self.assertIn("ledger/events.jsonl", before)
        self.assertIn("STATUS.md", before)

        self.write_metadata(schema_version=99)
        refused_before = self.state_digests()
        refused, _ = self.run_aph("status", str(self.project))
        refused_json, _ = self.run_aph("status", str(self.project), "--json")

        self.assertEqual(refused.returncode, 1)
        self.assertEqual(refused_json.returncode, 1)
        self.assertEqual(self.state_digests(), refused_before)

    def test_missing_project_state_is_an_actionable_failure(self):
        with tempfile.TemporaryDirectory(prefix="aph status empty ") as directory:
            completed, _ = self.run_aph("status", directory)

        self.assertEqual(completed.returncode, 1)
        self.assertIn("No Hamilton project state", completed.stderr)
        self.assertIn("Fix:", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_unsupported_version_refuses_in_both_output_forms(self):
        self.write_metadata(schema_version=99)

        human, _ = self.run_aph("status", str(self.project))
        machine, _ = self.run_aph("status", str(self.project), "--json")

        self.assertEqual(human.returncode, 1)
        self.assertIn("newer than supported", human.stderr)
        self.assertIn("upgrade aphelocoma", human.stderr.lower())
        self.assertNotIn("Traceback", human.stderr)
        self.assertEqual(machine.returncode, 1)
        report = json.loads(machine.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["error"]["path"], "hamilton.json")
        self.assertIn("upgrade aphelocoma", report["error"]["remediation"].lower())

    def test_board_is_colourless_and_states_every_status_as_a_word(self):
        self.write_tasks(
            [
                {
                    "id": "T1",
                    "title": "Fixture task",
                    "owner": "fullstack-developer",
                    "status": "done",
                    "dependencies": [],
                },
                {
                    "id": "T2",
                    "title": "Second task",
                    "owner": "qa-engineer",
                    "status": "in_review",
                    "dependencies": ["T1"],
                },
            ]
        )
        ansi = re.compile(r"\x1b\[[0-9;]*m")

        normal, _ = self.run_aph("status", str(self.project))
        no_color, _ = self.run_aph(
            "status", str(self.project), environment={"NO_COLOR": "1"}
        )

        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertIsNone(ansi.search(normal.stdout + normal.stderr))
        self.assertIsNone(ansi.search(no_color.stdout + no_color.stderr))
        self.assertEqual(normal.stdout, no_color.stdout)
        for status_word in ("[done]", "[in_review]"):
            self.assertIn(status_word, normal.stdout)


class CliInternalFailureTests(unittest.TestCase):
    def test_unexpected_failure_returns_two_without_traceback(self):
        from aphelocoma import cli

        with mock.patch.object(cli, "run_doctor", side_effect=RuntimeError("broken registry")):
            stdout = __import__("io").StringIO()
            stderr = __import__("io").StringIO()
            with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
                result = cli.main(["doctor"])

        self.assertEqual(result, 2)
        self.assertIn("unexpected failure", stderr.getvalue().lower())
        self.assertIn("broken registry", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_status_internal_failure_returns_two_without_traceback(self):
        from aphelocoma import cli, hamilton_state

        with mock.patch.object(
            hamilton_state,
            "summarize_project",
            side_effect=RuntimeError("broken board"),
        ):
            stdout = __import__("io").StringIO()
            stderr = __import__("io").StringIO()
            with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
                result = cli.main(["status", str(REPOSITORY)])

        self.assertEqual(result, 2)
        self.assertIn("unexpected failure", stderr.getvalue().lower())
        self.assertIn("broken board", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
