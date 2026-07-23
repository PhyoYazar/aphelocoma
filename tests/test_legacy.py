from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.doctor import DoctorContext, deployment_registry, run_checks
from aphelocoma.legacy import (
    LEGACY_PATH_LINE,
    cleanup_legacy_artifacts,
    inspect_legacy,
)
from aphelocoma.paths import resolve_paths


def isolated_paths(base, custom_legacy=None):
    home = base / "home"
    home.mkdir()
    environment = {
        "HOME": str(home),
        "APHELOCOMA_ROOT": str(base / "active"),
    }
    if custom_legacy is not None:
        environment["APHELOCOMA_HOME"] = str(custom_legacy)
    return resolve_paths(environment, tool_root=REPOSITORY)


class LegacyProtectionTests(unittest.TestCase):
    def test_released_v020_codex_hooks_are_exact_but_modified_peer_is_preserved(self):
        released = (
            b"[\n"
            b"  {\n"
            b'    "event": "Stop",\n'
            b'    "matcher": "",\n'
            b"    \"command\": \"echo '\\\\n Remember to run /journal to capture this session.'\"\n"
            b"  }\n"
            b"]\n"
        )
        for modified in (False, True):
            with self.subTest(modified=modified), tempfile.TemporaryDirectory(
                prefix="aph v020 codex hooks "
            ) as directory:
                paths = isolated_paths(Path(directory))
                hooks = paths.home / ".codex" / "hooks.json"
                hooks.parent.mkdir()
                hooks.write_bytes(
                    released + (b"\n// user edit\n" if modified else b"")
                )

                report = inspect_legacy(paths)
                result = cleanup_legacy_artifacts(paths)

                artifact = next(
                    item for item in report.artifacts if item.path == hooks
                )
                self.assertEqual(artifact.exact, not modified)
                self.assertEqual(hooks.exists(), modified)
                if modified:
                    self.assertFalse(result.ok)
                    self.assertIn(b"user edit", hooks.read_bytes())
                else:
                    self.assertTrue(result.ok)

    def test_doctor_reports_exact_legacy_path_stanza_before_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy path doctor ") as directory:
            paths = isolated_paths(Path(directory))
            shell_rc = paths.home / ".zshrc"
            shell_rc.write_text(
                "export KEEP=1\n# Aphelocoma\n" + LEGACY_PATH_LINE + "\n",
                encoding="utf-8",
            )
            before = shell_rc.read_bytes()

            report = inspect_legacy(paths)
            doctor = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )

            self.assertEqual(report.path_markers, (shell_rc,))
            diagnostic = next(item for item in doctor.checks if item.id == "legacy")
            self.assertEqual(diagnostic.status, "error")
            self.assertIn("path", diagnostic.message.lower())
            self.assertEqual(doctor.exit_code, 1)
            self.assertEqual(shell_rc.read_bytes(), before)

            cleanup = cleanup_legacy_artifacts(paths)
            cleaned = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )

            self.assertTrue(cleanup.ok)
            self.assertEqual(shell_rc.read_bytes(), b"export KEEP=1\n")
            self.assertEqual(
                next(item for item in cleaned.checks if item.id == "legacy").status,
                "ok",
            )

    def test_proven_legacy_skill_trees_are_removed_but_modified_trees_remain(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy skill proof ") as directory:
            paths = isolated_paths(Path(directory))
            claude_skill = paths.home / ".claude" / "skills" / "adr"
            claude_skill.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "skills" / "adr" / "skill.md",
                claude_skill / "SKILL.md",
            )
            shutil.copytree(
                REPOSITORY / "skills" / "adr" / "templates",
                claude_skill / "templates",
            )
            codex_skill = paths.home / ".codex" / "skills" / "adr"
            codex_skill.mkdir(parents=True)
            body = (REPOSITORY / "skills" / "adr" / "skill.md").read_text(
                encoding="utf-8"
            )
            codex_skill.joinpath("SKILL.md").write_text(
                "---\n"
                "name: adr\n"
                "description: Create a numbered Architecture Decision Record for a project.\n"
                "disable-model-invocation: true\n"
                "---\n\n"
                + body,
                encoding="utf-8",
            )
            shutil.copytree(
                REPOSITORY / "skills" / "adr" / "templates",
                codex_skill / "templates",
            )
            modified = paths.home / ".claude" / "skills" / "capture"
            modified.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "skills" / "capture" / "skill.md",
                modified / "SKILL.md",
            )
            (modified / "user-note").write_bytes(b"keep")

            report = inspect_legacy(paths)
            result = cleanup_legacy_artifacts(paths)

            by_path = {artifact.path: artifact for artifact in report.artifacts}
            self.assertTrue(by_path[claude_skill].exact)
            self.assertTrue(by_path[codex_skill].exact)
            self.assertFalse(by_path[modified].exact)
            self.assertFalse(claude_skill.exists())
            self.assertFalse(codex_skill.exists())
            self.assertTrue(modified.exists())
            self.assertEqual((modified / "user-note").read_bytes(), b"keep")
            self.assertFalse(result.ok)

    def test_legacy_cleanup_refuses_resolved_root_overlap_with_protected_data(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy cleanup root symlink ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            protected = base / "custom legacy"
            protected.mkdir()
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            root_parent = base / "root parent"
            root_parent.mkdir()
            (root_parent / "escape").symlink_to(
                protected,
                target_is_directory=True,
            )
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(root_parent / "escape" / "nested"),
                    "APHELOCOMA_HOME": str(protected),
                },
                tool_root=REPOSITORY,
            )

            result = cleanup_legacy_artifacts(paths)

            self.assertFalse(result.ok)
            self.assertTrue(any("protected legacy" in item.lower() for item in result.messages))
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])

    def test_legacy_cleanup_refuses_protected_data_inside_deletion_target(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy reverse cleanup ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            protected = home / ".claude" / "skills" / "adr" / "legacy-data"
            protected.mkdir(parents=True)
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(base / "active"),
                    "APHELOCOMA_HOME": str(protected),
                },
                tool_root=REPOSITORY,
            )

            result = cleanup_legacy_artifacts(paths)

            self.assertFalse(result.ok)
            self.assertTrue(any("overlaps protected" in item.lower() for item in result.messages))
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])

    def test_default_and_custom_legacy_data_are_detected_but_untouched(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy paths ") as directory:
            base = Path(directory)
            custom = base / "custom legacy"
            paths = isolated_paths(base, custom)
            default = paths.default_legacy_data
            for location, payload in ((default, b"default"), (custom, b"custom")):
                location.mkdir(parents=True)
                (location / "sentinel.bin").write_bytes(payload)
            before = {
                location: (location / "sentinel.bin").read_bytes()
                for location in (default, custom)
            }

            report = inspect_legacy(paths)
            cleanup = cleanup_legacy_artifacts(paths)

            self.assertEqual(
                set(report.protected_data),
                {default, custom},
            )
            self.assertTrue(cleanup.ok)
            for location, payload in before.items():
                self.assertEqual((location / "sentinel.bin").read_bytes(), payload)

    def test_exact_legacy_artifact_is_removed_but_modified_peer_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy cleanup ") as directory:
            paths = isolated_paths(Path(directory))
            exact = paths.home / ".claude" / "agents" / "architect.md"
            modified = paths.home / ".claude" / "agents" / "reviewer.md"
            exact.parent.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "adapters" / "claude-code" / "agents" / "architect.md",
                exact,
            )
            modified.write_bytes(b"user changed legacy-looking file\n")

            result = cleanup_legacy_artifacts(paths)

            self.assertFalse(exact.exists())
            self.assertTrue(modified.exists())
            self.assertFalse(result.ok)
            self.assertTrue(any("preserved" in message.lower() for message in result.messages))

    def test_legacy_doctor_reports_artifacts_but_not_protected_data_as_failure(self):
        with tempfile.TemporaryDirectory(prefix="aph legacy doctor ") as directory:
            paths = isolated_paths(Path(directory))
            paths.default_legacy_data.mkdir(parents=True)
            clean = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )
            self.assertTrue(clean.healthy)
            self.assertIn(
                "protected legacy data",
                next(item for item in clean.checks if item.id == "legacy").message.lower(),
            )

            legacy_agent = paths.home / ".claude" / "agents" / "architect.md"
            legacy_agent.parent.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "adapters" / "claude-code" / "agents" / "architect.md",
                legacy_agent,
            )
            unhealthy = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )

            diagnostic = next(item for item in unhealthy.checks if item.id == "legacy")
            self.assertEqual(diagnostic.status, "error")
            self.assertIn(str(legacy_agent), diagnostic.message)

    def test_unrelated_user_global_configuration_is_not_mislabeled_as_legacy(self):
        with tempfile.TemporaryDirectory(prefix="aph user global config ") as directory:
            paths = isolated_paths(Path(directory))
            claude = paths.home / ".claude"
            codex = paths.home / ".codex"
            claude.mkdir()
            codex.mkdir()
            (claude / "CLAUDE.md").write_bytes(b"# My ordinary instructions\n")
            (claude / "settings.json").write_bytes(b'{"theme": "dark"}\n')
            (codex / "AGENTS.md").write_bytes(b"# My Codex instructions\n")
            (codex / "hooks.json").write_bytes(b"{}\n")

            report = inspect_legacy(paths)
            doctor = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )

            self.assertEqual(report.artifacts, ())
            diagnostic = next(item for item in doctor.checks if item.id == "legacy")
            self.assertEqual(diagnostic.status, "ok")
