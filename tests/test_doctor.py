from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.doctor import (
    Diagnostic,
    DoctorContext,
    CheckRegistry,
    base_registry,
    run_checks,
)
from aphelocoma.paths import resolve_paths


def context_for(tool_root):
    paths = resolve_paths({"HOME": str(tool_root / "home")}, tool_root=tool_root)
    return DoctorContext(paths=paths)


class DoctorChecksTests(unittest.TestCase):
    def test_base_registry_is_ordered_and_has_unique_ids(self):
        registry = base_registry()

        self.assertEqual(
            registry.ids(),
            ("python", "git", "os", "aphelocoma_version", "hamilton_definition"),
        )

    def test_current_checkout_passes_all_base_checks(self):
        report = run_checks(context_for(REPOSITORY), base_registry())

        self.assertTrue(report.healthy)
        self.assertEqual(report.exit_code, 0)
        self.assertTrue(all(item.status == "ok" for item in report.checks))

    def test_missing_git_is_actionable(self):
        with mock.patch("aphelocoma.doctor.shutil.which", return_value=None):
            report = run_checks(context_for(REPOSITORY), base_registry())

        self.assertFalse(report.healthy)
        self.assertEqual(report.exit_code, 1)
        diagnostic = next(item for item in report.checks if item.id == "git")
        self.assertEqual(diagnostic.status, "error")
        self.assertIn("Install Git", diagnostic.remediation)

    def test_missing_version_and_definition_are_separate_findings(self):
        with tempfile.TemporaryDirectory(prefix="aph incomplete install ") as directory:
            report = run_checks(context_for(Path(directory)), base_registry())

        by_id = {item.id: item for item in report.checks}
        self.assertEqual(by_id["aphelocoma_version"].status, "error")
        self.assertIn("Reinstall", by_id["aphelocoma_version"].remediation)
        self.assertEqual(by_id["hamilton_definition"].status, "error")
        self.assertIn("Reinstall", by_id["hamilton_definition"].remediation)
        self.assertEqual(report.exit_code, 1)

    def test_partial_definition_with_one_role_reports_exact_missing_inventory(self):
        with tempfile.TemporaryDirectory(prefix="aph partial definition ") as directory:
            tool_root = Path(directory)
            required_by_old_probe = (
                "skills/aph-hamilton/skill.md",
                "skills/aph-hamilton/metadata.yaml",
                "skills/aph-hamilton/references/PROTOCOL.md",
                "skills/aph-hamilton/references/sizes.yaml",
                "skills/aph-hamilton/references/validate.py",
                "skills/aph-hamilton/references/roles.index.md",
                "skills/aph-hamilton/references/roles/ceo.md",
            )
            (tool_root / "VERSION").write_text("0.3.0\n", encoding="utf-8")
            for relative in required_by_old_probe:
                path = tool_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")

            report = run_checks(context_for(tool_root), base_registry())

        diagnostic = next(
            item for item in report.checks if item.id == "hamilton_definition"
        )
        self.assertEqual(diagnostic.status, "error")
        self.assertIn("skills/aph-hamilton/references/CRAFT.md", diagnostic.message)
        self.assertIn("skills/aph-hamilton/references/CRITIQUE.md", diagnostic.message)
        self.assertIn(
            "skills/aph-hamilton/references/roles/cto.md",
            diagnostic.message,
        )
        self.assertIn("Reinstall", diagnostic.remediation)

    def test_registry_rejects_duplicate_check_ids(self):
        registry = CheckRegistry()

        registry.register(
            "duplicate",
            lambda context: Diagnostic("duplicate", "ok", "first", None),
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            registry.register(
                "duplicate",
                lambda context: Diagnostic("duplicate", "ok", "second", None),
            )

    def test_machine_report_has_stable_shape(self):
        report = run_checks(context_for(REPOSITORY), base_registry()).as_dict()

        self.assertEqual(list(report), ["schema_version", "status", "checks"])
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(
            list(report["checks"][0]),
            ["id", "status", "message", "remediation"],
        )
