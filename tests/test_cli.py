import json
import os
from pathlib import Path
import re
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


class CliSubprocessTests(unittest.TestCase):
    def run_aph(self, *arguments, environment=None):
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
                cwd=str(home),
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )
            return completed, home

    def test_help_exposes_only_hamilton_commands(self):
        completed, _ = self.run_aph("help")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        for command in (
            "deploy",
            "undeploy",
            "doctor",
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
            "status",
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
            "update",
            "uninstall",
            "version",
        ):
            with self.subTest(command=command):
                completed, _ = self.run_aph(command, "--help")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn(f"aph {command}", completed.stdout)


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
