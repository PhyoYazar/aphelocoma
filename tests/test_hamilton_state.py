import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURES = ROOT / "tests" / "fixtures" / "hamilton"
REFERENCES = ROOT / "skills" / "aph-hamilton" / "references"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.hamilton_state import (  # noqa: E402
    CURRENT_PROTOCOL_VERSION,
    CURRENT_SCHEMA_VERSION,
    MigrationError,
    StatusError,
    migrate_project,
    schema_validation_errors,
    summarize_project,
    validate_project,
    write_status_report,
)


class ProjectFixture(unittest.TestCase):
    fixture_name = "current"

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name) / "project"
        shutil.copytree(FIXTURES / self.fixture_name, self.project)

    def tearDown(self):
        self.tempdir.cleanup()

    def read_events(self):
        path = self.project / ".aphelocoma" / "ledger" / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines() if line]

    def write_events(self, events):
        path = self.project / ".aphelocoma" / "ledger" / "events.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events))

    def issue_codes(self, report):
        return {issue.code for issue in report.errors}


class ValidationVersionTests(ProjectFixture):
    def test_current_state_validates(self):
        report = validate_project(self.project, tracked_files=[])
        self.assertTrue(report.ok, [issue.message for issue in report.errors])

    def test_unversioned_state_requires_migration(self):
        shutil.rmtree(self.project)
        shutil.copytree(FIXTURES / "unversioned-v02", self.project)

        report = validate_project(self.project, tracked_files=[])

        self.assertFalse(report.ok)
        self.assertIn("migration_required", self.issue_codes(report))
        issue = next(i for i in report.errors if i.code == "migration_required")
        self.assertIn("migrate.py", issue.remediation)

    def test_future_schema_version_is_refused_with_upgrade_remediation(self):
        path = self.project / ".aphelocoma" / "hamilton.json"
        data = json.loads(path.read_text())
        data["schema_version"] = CURRENT_SCHEMA_VERSION + 1
        path.write_text(json.dumps(data))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("unsupported_schema_version", self.issue_codes(report))
        issue = next(i for i in report.errors if i.code == "unsupported_schema_version")
        self.assertIn("upgrade Aphelocoma", issue.remediation)

    def test_future_protocol_version_is_refused(self):
        path = self.project / ".aphelocoma" / "hamilton.json"
        data = json.loads(path.read_text())
        data["protocol_version"] = "999.0.0"
        path.write_text(json.dumps(data))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("unsupported_protocol_version", self.issue_codes(report))

    def test_protocol_prerelease_and_build_metadata_are_not_current(self):
        path = self.project / ".aphelocoma" / "hamilton.json"
        source = json.loads(path.read_text())
        for version in ("1.0.0-alpha", "1.0.0+local"):
            with self.subTest(version=version):
                data = dict(source)
                data["protocol_version"] = version
                path.write_text(json.dumps(data))

                report = validate_project(self.project, tracked_files=[])

                self.assertIn(
                    "incompatible_protocol_version",
                    self.issue_codes(report),
                )


class MechanicalStateSchemaTests(ProjectFixture):
    def test_missing_required_hamilton_created_is_rejected_by_schema(self):
        path = self.project / ".aphelocoma" / "hamilton.json"
        metadata = json.loads(path.read_text())
        del metadata["created"]
        path.write_text(json.dumps(metadata))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("schema_required", self.issue_codes(report))

    def test_missing_required_task_title_is_rejected_by_schema(self):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text())
        del board["tasks"][0]["title"]
        path.write_text(json.dumps(board))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("schema_required", self.issue_codes(report))

    def test_forbidden_extra_event_property_is_rejected_by_schema(self):
        events = self.read_events()
        events[0]["unexpected"] = "not in state.schema.json"
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "schema_additional_property",
            self.issue_codes(report),
        )


class MigrationTests(ProjectFixture):
    fixture_name = "unversioned-v02"

    def snapshot(self):
        aph = self.project / ".aphelocoma"
        return {
            path.relative_to(aph).as_posix(): path.read_bytes()
            for path in aph.rglob("*")
            if path.is_file()
        }

    def structural_snapshot(self, root):
        snapshot = {}
        pending = [Path(root)]
        while pending:
            directory = pending.pop()
            for path in sorted(directory.iterdir(), reverse=True):
                relative = path.relative_to(root).as_posix()
                if path.is_symlink():
                    snapshot[relative] = ("symlink", os.readlink(path))
                elif path.is_dir():
                    snapshot[relative] = ("directory", None)
                    pending.append(path)
                elif path.is_file():
                    snapshot[relative] = ("file", path.read_bytes())
        return snapshot

    def event_prefix_digest(self, events, through_seq):
        digest = hashlib.sha256()
        for event in events:
            if event.get("seq", 0) > through_seq:
                continue
            digest.update(
                json.dumps(
                    event,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
        return digest.hexdigest()

    def task_states_digest(self, task_states):
        return hashlib.sha256(
            json.dumps(
                task_states,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        ).hexdigest()

    def test_check_reports_migration_without_writing(self):
        before = self.snapshot()

        result = migrate_project(self.project, apply=False)

        self.assertEqual("migration_required", result.status)
        self.assertIsNone(result.backup)
        self.assertEqual(before, self.snapshot())

    def test_apply_creates_backup_and_validates_migrated_state(self):
        result = migrate_project(self.project, apply=True)

        self.assertEqual("migrated", result.status)
        self.assertTrue(result.backup.is_dir())
        hamilton = json.loads(
            (self.project / ".aphelocoma" / "hamilton.json").read_text()
        )
        self.assertEqual(CURRENT_SCHEMA_VERSION, hamilton["schema_version"])
        self.assertEqual(CURRENT_PROTOCOL_VERSION, hamilton["protocol_version"])
        settings = (self.project / ".aphelocoma" / "settings.yaml").read_text()
        self.assertIn("visibility: tracked", settings)
        self.assertTrue(validate_project(self.project, tracked_files=[]).ok)

    def test_apply_normalizes_realistic_v02_state_and_baselines_legacy_history(self):
        metadata_path = self.project / ".aphelocoma" / "hamilton.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["updated"] = "2026-07-24T09:48:05Z"
        metadata_path.write_text(json.dumps(metadata))

        board_path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(board_path.read_text())
        task = board["tasks"][0]
        task["depends_on"] = []
        task["spec"] = None
        task["note"] = "Preserve this legacy task note."
        board_path.write_text(json.dumps(board))

        events = self.read_events()
        events[0].pop("to")
        events[1].pop("task")
        events = [
            event for event in events if event["event"] != "work_started"
        ]
        for seq, event in enumerate(events, start=1):
            event["seq"] = seq
        self.write_events(events)
        before = self.snapshot()

        result = migrate_project(self.project, apply=True)

        backup = {
            path.relative_to(result.backup).as_posix(): path.read_bytes()
            for path in result.backup.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, backup)
        migrated_metadata = json.loads(metadata_path.read_text())
        normalized_events = [
            {
                **event,
                "task": event.get("task"),
                "to": event.get("to"),
            }
            for event in events
        ]
        prefix_digest = self.event_prefix_digest(
            normalized_events,
            len(events),
        )
        task_states = [{"id": "T1", "status": "done"}]
        task_states_digest = self.task_states_digest(task_states)
        self.assertEqual(
            "2026-07-24T09:48:05Z",
            migrated_metadata["updated"],
        )
        self.assertEqual(
            {
                "source": "unversioned-v0.2",
                "through_seq": len(events),
                "prefix_digest": prefix_digest,
                "task_states_digest": task_states_digest,
                "task_states": task_states,
            },
            migrated_metadata["history_baseline"],
        )
        migrated_board = json.loads(board_path.read_text())
        migrated_task = migrated_board["tasks"][0]
        self.assertNotIn("depends_on", migrated_task)
        self.assertEqual([], migrated_task["dependencies"])
        self.assertIsNone(migrated_task["spec"])
        self.assertEqual(
            "Preserve this legacy task note.",
            migrated_task["note"],
        )
        migrated_events = self.read_events()
        self.assertEqual(len(events) + 1, len(migrated_events))
        for legacy, migrated in zip(
            normalized_events,
            migrated_events[: len(events)],
        ):
            self.assertEqual(legacy, migrated)
        self.assertEqual(
            {
                "ts": migrated_events[-1]["ts"],
                "seq": len(events) + 1,
                "event": "migration_baseline",
                "actor": "orchestrator",
                "task": None,
                "to": None,
                "note": (
                    "Migrated unversioned v0.2 history through seq %d with event "
                    "SHA-256 %s and task-state SHA-256 %s; strict replay begins "
                    "after this marker."
                    % (len(events), prefix_digest, task_states_digest)
                ),
            },
            migrated_events[-1],
        )
        report = validate_project(self.project, tracked_files=[])
        self.assertTrue(report.ok, [issue.message for issue in report.errors])

    def test_post_migration_history_is_still_strictly_replayed(self):
        migrate_project(self.project, apply=True)
        events = self.read_events()
        events.append(
            {
                "ts": "2026-07-24T09:48:06Z",
                "seq": len(events) + 1,
                "event": "work_started",
                "actor": "fullstack-developer",
                "task": "T1",
                "to": None,
                "note": "Invalidly restarted a completed task.",
            }
        )
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("invalid_transition", self.issue_codes(report))

    def test_history_baseline_cannot_be_self_declared_or_advanced(self):
        shutil.rmtree(self.project)
        shutil.copytree(FIXTURES / "current", self.project)
        events = [
            event
            for event in self.read_events()
            if event["event"] != "work_started"
        ]
        for seq, event in enumerate(events, start=1):
            event["seq"] = seq
        self.write_events(events)
        metadata_path = self.project / ".aphelocoma" / "hamilton.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["history_baseline"] = {
            "source": "unversioned-v0.2",
            "through_seq": len(events),
            "prefix_digest": self.event_prefix_digest(events, len(events)),
            "task_states_digest": self.task_states_digest(
                [{"id": "T1", "status": "done"}]
            ),
            "task_states": [{"id": "T1", "status": "done"}],
        }
        metadata_path.write_text(json.dumps(metadata))

        self_declared = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "invalid_history_baseline",
            self.issue_codes(self_declared),
        )

        shutil.rmtree(self.project)
        shutil.copytree(FIXTURES / "unversioned-v02", self.project)
        migrate_project(self.project, apply=True)
        events = self.read_events()
        events.append(
            {
                "ts": "2026-07-24T09:48:07Z",
                "seq": len(events) + 1,
                "event": "work_started",
                "actor": "fullstack-developer",
                "task": "T1",
                "to": None,
                "note": "Invalidly restarted a completed task.",
            }
        )
        self.write_events(events)
        metadata = json.loads(metadata_path.read_text())
        metadata["history_baseline"]["through_seq"] = len(events)
        metadata["history_baseline"]["prefix_digest"] = self.event_prefix_digest(
            events,
            len(events),
        )
        metadata_path.write_text(json.dumps(metadata))

        advanced = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "invalid_history_baseline",
            self.issue_codes(advanced),
        )

    def test_history_baseline_rejects_task_snapshot_tampering(self):
        migrate_project(self.project, apply=True)
        metadata_path = self.project / ".aphelocoma" / "hamilton.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["history_baseline"]["task_states"][0]["status"] = "assigned"
        metadata_path.write_text(json.dumps(metadata))

        board_path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(board_path.read_text())
        board["tasks"][0]["status"] = "in_progress"
        board_path.write_text(json.dumps(board))

        events = self.read_events()
        events.append(
            {
                "ts": "2026-07-24T09:48:08Z",
                "seq": len(events) + 1,
                "event": "work_started",
                "actor": "fullstack-developer",
                "task": "T1",
                "to": None,
                "note": "Invalidly restarted a completed task.",
            }
        )
        self.write_events(events)

        tampered = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "invalid_history_baseline",
            self.issue_codes(tampered),
        )

    def test_conflicting_legacy_and_current_dependencies_roll_back(self):
        board_path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(board_path.read_text())
        board["tasks"][0]["dependencies"] = []
        board["tasks"][0]["depends_on"] = None
        board_path.write_text(json.dumps(board))
        before = self.snapshot()

        with self.assertRaisesRegex(
            MigrationError,
            "conflicting depends_on and dependencies",
        ):
            migrate_project(self.project, apply=True)

        self.assertEqual(before, self.snapshot())

    def test_injected_failure_preserves_original_byte_for_byte(self):
        before = self.snapshot()

        with self.assertRaises(MigrationError):
            migrate_project(self.project, apply=True, inject_failure="after_write")

        self.assertEqual(before, self.snapshot())
        backups = list(self.project.glob(".aphelocoma.backup-v0.2-*"))
        self.assertEqual(1, len(backups))

    def test_migration_cli_check_and_apply(self):
        script = REFERENCES / "migrate.py"
        env = dict(os.environ, PYTHONPATH=str(SRC))
        checked = subprocess.run(
            [sys.executable, str(script), "check", str(self.project)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(1, checked.returncode, checked.stdout + checked.stderr)
        self.assertIn("migration required", checked.stdout.lower())

        applied = subprocess.run(
            [sys.executable, str(script), "apply", str(self.project)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(0, applied.returncode, applied.stdout + applied.stderr)
        self.assertIn("backup", applied.stdout.lower())

    @unittest.skipUnless(
        shutil.which("git"), "Git is required for this regression"
    )
    def test_git_repo_backup_is_recoverable_but_not_trackable(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)

        result = migrate_project(self.project, apply=True)

        self.assertTrue(result.backup.is_dir())
        self.assertTrue(
            result.backup.is_relative_to((self.project / ".git").resolve())
        )
        status = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("aphelocoma-backups", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_git_repo_failure_rolls_back_and_hides_backup_from_status(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        before = self.snapshot()

        with self.assertRaises(MigrationError) as raised:
            migrate_project(
                self.project,
                apply=True,
                inject_failure="after_write",
            )

        self.assertEqual(before, self.snapshot())
        self.assertTrue(raised.exception.backup.is_dir())
        self.assertTrue(
            raised.exception.backup.is_relative_to(
                (self.project / ".git").resolve()
            )
        )
        status = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("aphelocoma-backups", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_same_second_git_backup_collision_stays_under_git_metadata(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        fixed = datetime(2026, 7, 23, 8, 45, 0)
        backup_root = (
            self.project / ".git" / "aphelocoma-backups"
        ).resolve()
        backup_root.mkdir(parents=True)
        collision = backup_root / "v0.2-20260723T084500Z"
        collision.mkdir()

        with patch("aphelocoma.hamilton_state.datetime") as clock:
            clock.now.return_value = fixed
            result = migrate_project(self.project, apply=True)

        self.assertEqual(
            backup_root / "v0.2-20260723T084500Z-1",
            result.backup,
        )
        self.assertTrue(result.backup.is_dir())
        status = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("v0.2-20260723T084500Z-1", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_nested_project_backup_uses_enclosing_repo_git_metadata(self):
        repository = Path(self.tempdir.name)
        initialized = subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)

        result = migrate_project(self.project, apply=True)

        backup_root = (
            repository / ".git" / "aphelocoma-backups"
        ).resolve()
        self.assertTrue(result.backup.is_relative_to(backup_root))
        self.assertTrue(result.backup.is_dir())
        status = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("aphelocoma-backups", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_invalid_nested_git_context_refuses_migration_without_backup(self):
        repository = Path(self.tempdir.name)
        initialized = subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        (self.project / ".git").write_text(
            "gitdir: ../missing-git-directory\n"
        )
        before = self.snapshot()

        with self.assertRaises(MigrationError) as raised:
            migrate_project(self.project, apply=True)

        self.assertIsNone(raised.exception.backup)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(
            [],
            list(self.project.glob(".aphelocoma.backup-v0.2-*")),
        )
        self.assertFalse(
            (repository / ".git" / "aphelocoma-backups").exists()
        )
        status = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn(".aphelocoma.backup-v0.2-", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_head_only_nested_gitdir_refuses_migration_without_backup(self):
        repository = Path(self.tempdir.name)
        initialized = subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        fake_gitdir = repository / "fake-gitdir"
        fake_gitdir.mkdir()
        (fake_gitdir / "HEAD").write_text("ref: refs/heads/main\n")
        (self.project / ".git").write_text(
            "gitdir: ../fake-gitdir\n"
        )
        before = self.snapshot()

        with self.assertRaises(MigrationError) as raised:
            migrate_project(self.project, apply=True)

        self.assertIsNone(raised.exception.backup)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((fake_gitdir / "aphelocoma-backups").exists())
        self.assertEqual(
            [],
            list(self.project.glob(".aphelocoma.backup-v0.2-*")),
        )
        status = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("aphelocoma-backup", status.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_symlinked_git_backup_root_is_rejected_before_copy(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        visible_backups = self.project / "visible-backups"
        visible_backups.mkdir()
        (self.project / ".git" / "aphelocoma-backups").symlink_to(
            visible_backups,
            target_is_directory=True,
        )
        before = self.snapshot()

        with self.assertRaises(MigrationError) as raised:
            migrate_project(self.project, apply=True)

        self.assertIsNone(raised.exception.backup)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], list(visible_backups.iterdir()))
        status = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertNotIn("visible-backups/", status.stdout)

    def test_internal_state_symlink_is_rejected_before_external_write(self):
        aph = self.project / ".aphelocoma"
        state = aph / "state"
        external = Path(self.tempdir.name) / "external-state"
        shutil.copytree(state, external)
        shutil.rmtree(state)
        state.symlink_to(external, target_is_directory=True)
        before_project = self.structural_snapshot(aph)
        before_external = self.structural_snapshot(external)

        with self.assertRaises(MigrationError) as raised:
            migrate_project(
                self.project,
                apply=True,
                inject_failure="after_write",
            )

        self.assertIsNone(raised.exception.backup)
        self.assertEqual(before_project, self.structural_snapshot(aph))
        self.assertEqual(before_external, self.structural_snapshot(external))
        self.assertEqual(
            [],
            list(self.project.glob(".aphelocoma.backup-v0.2-*")),
        )
        for pattern in (
            ".aphelocoma.migrate-*",
            ".aphelocoma.original-*",
            ".aphelocoma.validate-*",
        ):
            self.assertEqual([], list(self.project.glob(pattern)))

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_nested_worktree_project_backup_uses_gitdir_file_target(self):
        root = Path(self.tempdir.name)
        worktree = root / "worktree"
        nested = worktree / "apps" / "project"
        metadata = root / "metadata" / "worktrees" / "fixture"
        metadata.parent.mkdir(parents=True)
        initialized = subprocess.run(
            [
                "git",
                "init",
                "-q",
                "--separate-git-dir",
                str(metadata),
                str(worktree),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        shutil.copytree(FIXTURES / "unversioned-v02", nested)

        result = migrate_project(nested, apply=True)

        self.assertTrue(
            result.backup.is_relative_to(
                (metadata / "aphelocoma-backups").resolve()
            )
        )
        self.assertTrue(result.backup.is_dir())

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_migration_rolls_back_when_dispatch_result_is_force_tracked(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        dispatch = (
            self.project
            / ".aphelocoma"
            / "dispatch"
            / "T1--fullstack-developer"
        )
        dispatch.mkdir(parents=True)
        result_path = dispatch / "result.json"
        result_path.write_text('{"status":"blocked"}\n')
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "add",
                "-f",
                ".aphelocoma/dispatch/T1--fullstack-developer/result.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, tracked.returncode, tracked.stderr)
        before = self.snapshot()

        with self.assertRaises(MigrationError) as raised:
            migrate_project(self.project, apply=True)

        self.assertEqual(before, self.snapshot())
        self.assertTrue(raised.exception.backup.is_dir())
        metadata = json.loads(
            (self.project / ".aphelocoma" / "hamilton.json").read_text()
        )
        self.assertNotIn("schema_version", metadata)


class LedgerInvariantTests(ProjectFixture):
    def set_board_status(self, status):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text())
        board["tasks"][0]["status"] = status
        path.write_text(json.dumps(board))

    def test_every_live_status_requires_matching_lifecycle_history(self):
        source = self.read_events()
        cases = (
            ("pending", 3),
            ("assigned", 4),
            ("in_progress", 5),
            ("in_review", 7),
            ("done", 9),
        )
        for status, event_count in cases:
            with self.subTest(status=status):
                self.set_board_status(status)
                self.write_events(source[:event_count])
                report = validate_project(self.project, tracked_files=[])
                self.assertNotIn(
                    "lifecycle_status_mismatch",
                    self.issue_codes(report),
                    [issue.message for issue in report.errors],
                )

    def test_in_review_with_empty_history_is_rejected(self):
        self.set_board_status("in_review")
        self.write_events([])

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "lifecycle_status_mismatch",
            self.issue_codes(report),
        )

    def test_in_progress_requires_work_started_history(self):
        self.set_board_status("in_progress")
        self.write_events(self.read_events()[:4])

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "lifecycle_status_mismatch",
            self.issue_codes(report),
        )

    def test_in_review_requires_handoff_history(self):
        self.set_board_status("in_review")
        self.write_events(self.read_events()[:6])

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "lifecycle_status_mismatch",
            self.issue_codes(report),
        )

    def test_blocked_live_status_matches_blocked_history(self):
        self.set_board_status("blocked")
        events = self.read_events()[:5]
        events.append(
            {
                "ts": "2026-07-23T00:00:05Z",
                "seq": 6,
                "event": "blocked",
                "actor": "fullstack-developer",
                "task": "T1",
                "to": None,
                "note": "Blocked safely.",
            }
        )
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertNotIn(
            "lifecycle_status_mismatch",
            self.issue_codes(report),
            [issue.message for issue in report.errors],
        )

    def test_blocked_live_status_without_blocked_history_is_rejected(self):
        self.set_board_status("blocked")
        self.write_events(self.read_events()[:5])

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "lifecycle_status_mismatch",
            self.issue_codes(report),
        )

    def test_review_failed_assigns_until_subsequent_work_started(self):
        events = self.read_events()
        events[-1]["event"] = "review_failed"
        events[-1]["note"] = "Review failed with blocking findings."
        self.set_board_status("assigned")
        self.write_events(events)

        assigned = validate_project(self.project, tracked_files=[])

        self.assertNotIn(
            "lifecycle_status_mismatch",
            self.issue_codes(assigned),
            [issue.message for issue in assigned.errors],
        )

        events.append(
            {
                "ts": "2026-07-23T00:00:09Z",
                "seq": 10,
                "event": "work_started",
                "actor": "fullstack-developer",
                "task": "T1",
                "to": None,
                "note": "Bounce-back work started.",
            }
        )
        self.set_board_status("in_progress")
        self.write_events(events)

        restarted = validate_project(self.project, tracked_files=[])

        self.assertNotIn(
            "lifecycle_status_mismatch",
            self.issue_codes(restarted),
            [issue.message for issue in restarted.errors],
        )

    def test_reviewer_cannot_be_task_builder(self):
        events = self.read_events()
        critique = next(e for e in events if e["event"] == "critique")
        critique["actor"] = "fullstack-developer"
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("reviewer_is_builder", self.issue_codes(report))

    def test_critique_before_handoff_is_rejected(self):
        events = self.read_events()
        critique_index = next(
            i for i, event in enumerate(events) if event["event"] == "critique"
        )
        critique = events.pop(critique_index)
        handoff_index = next(
            i for i, event in enumerate(events) if event["event"] == "handoff"
        )
        events.insert(handoff_index, critique)
        for seq, event in enumerate(events, start=1):
            event["seq"] = seq
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("invalid_transition", self.issue_codes(report))

    def test_review_passed_before_critique_is_rejected(self):
        events = [
            event for event in self.read_events() if event["event"] != "critique"
        ]
        for seq, event in enumerate(events, start=1):
            event["seq"] = seq
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("review_before_critique", self.issue_codes(report))

    def test_event_reference_to_missing_task_is_rejected(self):
        events = self.read_events()
        events.append(
            {
                "ts": "2026-07-23T00:00:09Z",
                "seq": len(events) + 1,
                "event": "artifact_written",
                "actor": "fullstack-developer",
                "task": "T404",
                "to": None,
                "note": "Missing reference.",
            }
        )
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("unknown_task_reference", self.issue_codes(report))

    def test_missing_dependency_reference_is_rejected(self):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text())
        board["tasks"][0]["dependencies"] = ["T404"]
        path.write_text(json.dumps(board))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("unknown_dependency", self.issue_codes(report))

    def test_work_started_before_assignment_is_rejected(self):
        events = self.read_events()
        assignment = next(e for e in events if e["event"] == "task_assigned")
        events.remove(assignment)
        for seq, event in enumerate(events, start=1):
            event["seq"] = seq
        self.write_events(events)

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("invalid_transition", self.issue_codes(report))

    def test_duplicate_task_ids_are_rejected(self):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text())
        board["tasks"].append(dict(board["tasks"][0]))
        path.write_text(json.dumps(board))

        report = validate_project(self.project, tracked_files=[])

        self.assertIn("duplicate_task_id", self.issue_codes(report))


class PrivacyTests(ProjectFixture):
    def test_tracked_dispatch_results_are_rejected(self):
        report = validate_project(
            self.project,
            tracked_files=[".aphelocoma/dispatch/T1--qa-engineer/result.json"],
        )

        self.assertIn("tracked_transient", self.issue_codes(report))

    def test_local_visibility_rejects_any_tracked_hamilton_state(self):
        settings = self.project / ".aphelocoma" / "settings.yaml"
        settings.write_text(settings.read_text().replace("tracked", "local", 1))

        report = validate_project(
            self.project,
            tracked_files=[".aphelocoma/state/tasks.json"],
        )

        self.assertIn("tracked_local_state", self.issue_codes(report))

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_nested_local_project_detects_repo_relative_tracked_state(self):
        repository = Path(self.tempdir.name)
        initialized = subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        settings = self.project / ".aphelocoma" / "settings.yaml"
        settings.write_text(settings.read_text().replace("tracked", "local", 1))
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "add",
                "project/.aphelocoma/state/tasks.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, tracked.returncode, tracked.stderr)

        report = validate_project(self.project)

        self.assertIn("tracked_local_state", self.issue_codes(report))

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_inner_repo_does_not_hide_outer_tracked_state_and_dispatch(self):
        repository = Path(self.tempdir.name)
        initialized = subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        settings = self.project / ".aphelocoma" / "settings.yaml"
        settings.write_text(settings.read_text().replace("tracked", "local", 1))
        dispatch = (
            self.project / ".aphelocoma" / "dispatch" / "T1--qa-engineer"
        )
        dispatch.mkdir(parents=True)
        (dispatch / "result.json").write_text('{"verdict":"pass"}\n')
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "add",
                "-f",
                "project/.aphelocoma/state/tasks.json",
                "project/.aphelocoma/dispatch/T1--qa-engineer/result.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, staged.returncode, staged.stderr)
        nested = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, nested.returncode, nested.stderr)

        report = validate_project(self.project)
        codes = self.issue_codes(report)

        self.assertIn("tracked_local_state", codes)
        self.assertIn("tracked_transient", codes)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_index_v4_local_visibility_detects_staged_state(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        configured = subprocess.run(
            ["git", "-C", str(self.project), "config", "index.version", "4"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, configured.returncode, configured.stderr)
        settings = self.project / ".aphelocoma" / "settings.yaml"
        settings.write_text(settings.read_text().replace("tracked", "local", 1))
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "add",
                ".aphelocoma/state/tasks.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, staged.returncode, staged.stderr)

        report = validate_project(self.project)

        self.assertIn("tracked_local_state", self.issue_codes(report))

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_index_v4_detects_force_tracked_dispatch_result(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        configured = subprocess.run(
            ["git", "-C", str(self.project), "config", "index.version", "4"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, configured.returncode, configured.stderr)
        dispatch = (
            self.project / ".aphelocoma" / "dispatch" / "T1--qa-engineer"
        )
        dispatch.mkdir(parents=True)
        result_path = dispatch / "result.json"
        result_path.write_text('{"verdict":"pass"}\n')
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "add",
                "-f",
                ".aphelocoma/dispatch/T1--qa-engineer/result.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, staged.returncode, staged.stderr)

        report = validate_project(self.project)

        self.assertIn("tracked_transient", self.issue_codes(report))

    @unittest.skipUnless(shutil.which("git"), "Git is required for this regression")
    def test_split_index_v4_detects_tracked_local_state_and_dispatch(self):
        initialized = subprocess.run(
            ["git", "init", "-q", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        for key, value in (
            ("index.version", "4"),
            ("core.splitIndex", "true"),
        ):
            configured = subprocess.run(
                ["git", "-C", str(self.project), "config", key, value],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, configured.returncode, configured.stderr)
        settings = self.project / ".aphelocoma" / "settings.yaml"
        settings.write_text(settings.read_text().replace("tracked", "local", 1))
        dispatch = (
            self.project / ".aphelocoma" / "dispatch" / "T1--qa-engineer"
        )
        dispatch.mkdir(parents=True)
        (dispatch / "result.json").write_text('{"verdict":"pass"}\n')
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "add",
                "-f",
                ".aphelocoma/state/tasks.json",
                ".aphelocoma/dispatch/T1--qa-engineer/result.json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, staged.returncode, staged.stderr)
        split = subprocess.run(
            [
                "git",
                "-C",
                str(self.project),
                "update-index",
                "--index-version=4",
                "--split-index",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, split.returncode, split.stderr)
        index = (self.project / ".git" / "index").read_bytes()
        self.assertEqual(4, int.from_bytes(index[4:8], "big"))
        self.assertTrue(list((self.project / ".git").glob("sharedindex.*")))

        report = validate_project(self.project)
        codes = self.issue_codes(report)

        self.assertIn("tracked_local_state", codes)
        self.assertIn("tracked_transient", codes)

    def test_tracking_lookup_failure_is_privacy_error(self):
        (self.project / ".git").mkdir()

        with patch(
            "aphelocoma.hamilton_state.subprocess.run",
            side_effect=OSError("git unavailable"),
        ):
            report = validate_project(self.project)

        self.assertFalse(report.ok)
        self.assertIn("tracked_state_unknown", self.issue_codes(report))

    def test_representative_secret_in_durable_ledger_is_rejected(self):
        examples = (
            "credential AKIAIOSFODNN7EXAMPLE",
            "access_token=not-a-real-token-value",
            "-----BEGIN PRIVATE KEY-----",
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
        )
        source = (
            self.project / ".aphelocoma" / "ledger" / "events.jsonl"
        ).read_text()
        for secret in examples:
            with self.subTest(secret=secret):
                events_path = (
                    self.project / ".aphelocoma" / "ledger" / "events.jsonl"
                )
                events_path.write_text(
                    source
                    + json.dumps(
                        {
                            "ts": "2026-07-23T00:00:09Z",
                            "seq": 10,
                            "event": "assumption_logged",
                            "actor": "cto",
                            "task": None,
                            "to": None,
                            "note": secret,
                        }
                    )
                    + "\n"
                )
                report = validate_project(self.project, tracked_files=[])
                self.assertIn("secret_material", self.issue_codes(report))

    def test_dispatch_scratch_is_not_scanned_as_durable_state(self):
        dispatch = self.project / ".aphelocoma" / "dispatch" / "T1"
        dispatch.mkdir(parents=True)
        (dispatch / "prompt.md").write_text("sk-example-not-durable")

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])


class ContractTests(unittest.TestCase):
    def test_state_schema_declares_current_versions_and_visibility(self):
        schema = json.loads((REFERENCES / "state.schema.json").read_text())
        metadata = schema["properties"]["hamilton"]
        self.assertEqual(
            CURRENT_SCHEMA_VERSION,
            metadata["properties"]["schema_version"]["const"],
        )
        self.assertEqual(
            CURRENT_PROTOCOL_VERSION,
            metadata["properties"]["protocol_version"]["const"],
        )
        visibility = schema["properties"]["settings"]["properties"]["visibility"]
        self.assertEqual(["tracked", "local"], visibility["enum"])

    def test_result_schemas_are_strict_and_keep_codex_contract(self):
        implementer = json.loads(
            (REFERENCES / "result.implementer.schema.json").read_text()
        )
        reviewer = json.loads(
            (REFERENCES / "result.reviewer.schema.json").read_text()
        )
        self.assertFalse(implementer["additionalProperties"])
        self.assertFalse(reviewer["additionalProperties"])
        self.assertIn("blocked_reason", implementer["required"])
        self.assertEqual(["in_review", "blocked"], implementer["properties"]["status"]["enum"])
        self.assertEqual(["pass", "fail"], reviewer["properties"]["verdict"]["enum"])
        self.assertEqual(["subagent"], reviewer["properties"]["tier"]["enum"])

    def test_implementer_schema_rejects_contradictory_status_payloads(self):
        schema = json.loads(
            (REFERENCES / "result.implementer.schema.json").read_text()
        )
        base = {
            "task": "T1",
            "role": "fullstack-developer#2",
            "status": "blocked",
            "artifacts": [],
            "events": [
                {
                    "event": "blocked",
                    "to": None,
                    "note": "Blocked safely.",
                }
            ],
            "blocked_reason": "A dependency is missing.",
        }
        self.assertEqual([], schema_validation_errors(base, schema))

        missing_reason = dict(base, blocked_reason=None)
        wrong_event = dict(
            base,
            events=[
                {
                    "event": "handoff",
                    "to": "qa-engineer",
                    "note": "Contradictory.",
                }
            ],
        )
        in_review_with_reason = dict(
            base,
            status="in_review",
            artifacts=["artifact.txt"],
            events=[
                {
                    "event": "work_started",
                    "to": None,
                    "note": "Started.",
                },
                {
                    "event": "artifact_written",
                    "to": None,
                    "note": "Written.",
                },
                {
                    "event": "handoff",
                    "to": "qa-engineer",
                    "note": "Ready.",
                },
            ],
            blocked_reason="must be null",
        )
        for payload in (missing_reason, wrong_event, in_review_with_reason):
            with self.subTest(payload=payload):
                self.assertTrue(schema_validation_errors(payload, schema))

    def test_implementer_schema_requires_exclusive_lifecycle_branch(self):
        schema = json.loads(
            (REFERENCES / "result.implementer.schema.json").read_text()
        )
        lifecycle = [
            {
                "event": "work_started",
                "to": None,
                "note": "Started.",
            },
            {
                "event": "artifact_written",
                "to": None,
                "note": "Written.",
            },
            {
                "event": "handoff",
                "to": "qa-engineer",
                "note": "Ready.",
            },
        ]
        in_review = {
            "task": "T1",
            "role": "fullstack-developer#2",
            "status": "in_review",
            "artifacts": ["artifact.txt"],
            "events": lifecycle,
            "blocked_reason": None,
        }
        blocked = {
            "task": "T1",
            "role": "fullstack-developer#2",
            "status": "blocked",
            "artifacts": [],
            "events": [
                {
                    "event": "blocked",
                    "to": None,
                    "note": "Blocked safely.",
                }
            ],
            "blocked_reason": "A dependency is missing.",
        }
        self.assertEqual([], schema_validation_errors(in_review, schema))
        self.assertEqual([], schema_validation_errors(blocked, schema))

        missing_artifact_event = dict(
            in_review,
            events=[lifecycle[0], lifecycle[2]],
        )
        in_review_with_blocked = dict(
            in_review,
            events=lifecycle
            + [
                {
                    "event": "blocked",
                    "to": None,
                    "note": "Contradictory.",
                }
            ],
        )
        blocked_with_handoff = dict(
            blocked,
            events=blocked["events"]
            + [
                {
                    "event": "handoff",
                    "to": "qa-engineer",
                    "note": "Contradictory.",
                }
            ],
        )
        no_artifacts = dict(in_review, artifacts=[])
        reordered = dict(
            in_review,
            events=[lifecycle[2], lifecycle[1], lifecycle[0]],
        )
        duplicate = dict(
            in_review,
            events=[lifecycle[0], lifecycle[0], lifecycle[2]],
        )
        work_started_wrong_target = dict(
            in_review,
            events=[
                dict(lifecycle[0], to="qa-engineer"),
                lifecycle[1],
                lifecycle[2],
            ],
        )
        artifact_wrong_target = dict(
            in_review,
            events=[
                lifecycle[0],
                dict(lifecycle[1], to="qa-engineer"),
                lifecycle[2],
            ],
        )
        handoff_missing_reviewer = dict(
            in_review,
            events=[
                lifecycle[0],
                lifecycle[1],
                dict(lifecycle[2], to=""),
            ],
        )
        blocked_wrong_target = dict(
            blocked,
            events=[
                {
                    "event": "blocked",
                    "to": "qa-engineer",
                    "note": "Wrong target.",
                }
            ],
        )
        for payload in (
            missing_artifact_event,
            in_review_with_blocked,
            blocked_with_handoff,
            no_artifacts,
            reordered,
            duplicate,
            work_started_wrong_target,
            artifact_wrong_target,
            handoff_missing_reviewer,
            blocked_wrong_target,
        ):
            with self.subTest(payload=payload):
                self.assertTrue(schema_validation_errors(payload, schema))

    def test_reviewer_pass_schema_rejects_blocking_finding(self):
        schema = json.loads(
            (REFERENCES / "result.reviewer.schema.json").read_text()
        )
        payload = {
            "task": "T1",
            "role": "qa-engineer",
            "verdict": "pass",
            "tier": "subagent",
            "findings": [
                {
                    "severity": "blocking",
                    "note": "This cannot pass.",
                }
            ],
            "summary": "Contradictory pass.",
        }

        self.assertTrue(schema_validation_errors(payload, schema))

    def test_reviewer_fail_schema_requires_blocking_finding(self):
        schema = json.loads(
            (REFERENCES / "result.reviewer.schema.json").read_text()
        )
        base = {
            "task": "T1",
            "role": "qa-engineer",
            "verdict": "fail",
            "tier": "subagent",
            "findings": [
                {
                    "severity": "blocking",
                    "note": "Must be fixed.",
                }
            ],
            "summary": "Blocking finding.",
        }
        self.assertEqual([], schema_validation_errors(base, schema))
        for findings in (
            [],
            [{"severity": "should-fix", "note": "Not blocking."}],
        ):
            with self.subTest(findings=findings):
                payload = dict(base, findings=findings)
                self.assertTrue(schema_validation_errors(payload, schema))

    def test_codex_dispatch_semantics_remain_explicit(self):
        dispatch = (REFERENCES / "DISPATCH-CODEX.md").read_text()
        parallel = (REFERENCES / "PARALLEL.md").read_text()
        for required in (
            "codex exec",
            "--output-schema",
            "--sandbox read-only",
            "agent_type: \"hamilton-<role-id>\"",
            "model",
            "reasoning_effort",
        ):
            self.assertIn(required, dispatch)
        self.assertIn("single writer", parallel.lower())
        self.assertIn("role", parallel.lower())

    def test_review_failed_protocol_matches_deterministic_replay(self):
        protocol = " ".join(
            (REFERENCES / "PROTOCOL.md").read_text().split()
        )

        self.assertIn(
            "`review_failed` → `assigned`; a subsequent `work_started` → "
            "`in_progress`.",
            protocol,
        )
        self.assertNotIn("`assigned`/`in_progress`", protocol)


class DoctorRegistrationTests(ProjectFixture):
    def test_registers_project_version_integrity_and_privacy_checks(self):
        from aphelocoma.hamilton_state import register_doctor_checks

        class Registry:
            def __init__(self):
                self.callbacks = {}

            def register(self, check_id, callback):
                self.callbacks[check_id] = callback

        registry = Registry()
        register_doctor_checks(registry)

        self.assertEqual(
            {
                "hamilton-project-version",
                "hamilton-project-integrity",
                "hamilton-project-privacy",
            },
            set(registry.callbacks),
        )

    def test_registered_checks_report_current_state_healthy(self):
        from aphelocoma.doctor import (
            CheckRegistry,
            DoctorContext,
            run_checks,
        )
        from aphelocoma.hamilton_state import register_doctor_checks
        from aphelocoma.paths import resolve_paths

        registry = CheckRegistry()
        register_doctor_checks(registry)
        context = DoctorContext(
            paths=resolve_paths({}, tool_root=ROOT),
            cwd=self.project,
        )

        report = run_checks(context, registry)

        self.assertTrue(report.healthy)
        self.assertEqual(
            (
                "hamilton-project-version",
                "hamilton-project-integrity",
                "hamilton-project-privacy",
            ),
            tuple(check.id for check in report.checks),
        )

    def test_registered_version_check_requires_v02_migration(self):
        from aphelocoma.doctor import (
            CheckRegistry,
            DoctorContext,
            run_checks,
        )
        from aphelocoma.hamilton_state import register_doctor_checks
        from aphelocoma.paths import resolve_paths

        shutil.rmtree(self.project)
        shutil.copytree(FIXTURES / "unversioned-v02", self.project)
        registry = CheckRegistry()
        register_doctor_checks(registry)
        context = DoctorContext(
            paths=resolve_paths({}, tool_root=ROOT),
            cwd=self.project,
        )

        report = run_checks(context, registry)
        version = next(
            check
            for check in report.checks
            if check.id == "hamilton-project-version"
        )

        self.assertEqual("error", version.status)
        self.assertIn("migrate.py", version.remediation)

    def test_registered_privacy_check_fails_closed_when_tracking_is_unknown(self):
        from aphelocoma.doctor import (
            CheckRegistry,
            DoctorContext,
            run_checks,
        )
        from aphelocoma.hamilton_state import register_doctor_checks
        from aphelocoma.paths import resolve_paths

        (self.project / ".git").mkdir()
        registry = CheckRegistry()
        register_doctor_checks(registry)
        context = DoctorContext(
            paths=resolve_paths({}, tool_root=ROOT),
            cwd=self.project,
        )

        with patch(
            "aphelocoma.hamilton_state.subprocess.run",
            side_effect=OSError("git unavailable"),
        ):
            report = run_checks(context, registry)
        privacy = next(
            check
            for check in report.checks
            if check.id == "hamilton-project-privacy"
        )

        self.assertEqual("error", privacy.status)
        self.assertIn("could not be determined", privacy.message)


class ConventionsWarningTests(ProjectFixture):
    def test_missing_conventions_warns_after_planning(self):
        conventions = (
            self.project / ".aphelocoma" / "state" / "conventions.md"
        )
        conventions.unlink()

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "missing_conventions",
            {issue.code for issue in report.warnings},
        )

    def test_stub_conventions_warns_after_planning(self):
        conventions = (
            self.project / ".aphelocoma" / "state" / "conventions.md"
        )
        conventions.write_text("# Conventions\n\n_No active project yet._\n")

        report = validate_project(self.project, tracked_files=[])

        self.assertIn(
            "stub_conventions",
            {issue.code for issue in report.warnings},
        )


class StatusBoardTests(ProjectFixture):
    """The read-only progress board described by PROTOCOL.md §5.6."""

    def hamilton_path(self):
        return self.project / ".aphelocoma" / "hamilton.json"

    def read_metadata(self):
        return json.loads(self.hamilton_path().read_text(encoding="utf-8"))

    def write_metadata(self, metadata):
        self.hamilton_path().write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )

    def write_tasks(self, tasks, phase="implementation"):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text(encoding="utf-8"))
        board["phase"] = phase
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

    def run_git(self, *arguments, when=None):
        environment = dict(os.environ)
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            }
        )
        if when is not None:
            environment["GIT_AUTHOR_DATE"] = when
            environment["GIT_COMMITTER_DATE"] = when
        completed = subprocess.run(
            ["git", "-C", str(self.project), *arguments],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return completed.stdout

    def start_repository(self):
        self.run_git("init", "-q", ".")
        self.run_git("symbolic-ref", "HEAD", "refs/heads/work")

    def commit_all(self, message, when):
        self.run_git("add", "-A", when=when)
        self.run_git(
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            message,
            when=when,
        )

    def test_summary_reports_identity_versions_and_progress(self):
        self.write_tasks(self.sample_tasks())

        summary = summarize_project(self.project)

        self.assertEqual(summary.project, "fixture-current")
        self.assertEqual(summary.phase, "done")
        self.assertEqual(summary.schema_version, CURRENT_SCHEMA_VERSION)
        self.assertEqual(summary.protocol_version, CURRENT_PROTOCOL_VERSION)
        self.assertEqual(summary.visibility, "tracked")
        self.assertEqual(summary.done_count, 1)
        self.assertEqual(summary.total_count, 4)
        self.assertEqual(
            [(task.id, task.status, task.owner) for task in summary.tasks],
            [
                ("T1", "done", "fullstack-developer#2"),
                ("T2", "blocked", "devops-engineer"),
                ("T3", "pending", "qa-engineer"),
                ("T4", "assigned", "fullstack-developer#1"),
            ],
        )

    def test_blocked_tasks_are_called_out_and_gate_the_next_action(self):
        self.write_tasks(self.sample_tasks())

        summary = summarize_project(self.project)

        self.assertEqual([task.id for task in summary.blocked], ["T2"])
        self.assertIsNotNone(summary.next_task)
        self.assertEqual(summary.next_task.id, "T4")
        self.assertEqual(summary.next_task.owner, "fullstack-developer#1")

    def test_completed_project_has_no_next_actionable_task(self):
        summary = summarize_project(self.project)

        self.assertEqual(summary.done_count, 1)
        self.assertEqual(summary.total_count, 1)
        self.assertIsNone(summary.next_task)
        self.assertEqual(summary.blocked, ())

    def test_summary_dictionary_is_stable_and_machine_readable(self):
        self.write_tasks(self.sample_tasks())

        payload = summarize_project(self.project).as_dict()

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(
            payload["project"],
            {
                "name": "fixture-current",
                "phase": "done",
                "schema_version": CURRENT_SCHEMA_VERSION,
                "protocol_version": CURRENT_PROTOCOL_VERSION,
                "visibility": "tracked",
            },
        )
        self.assertEqual(payload["progress"], {"done": 1, "total": 4})
        self.assertEqual(
            payload["tasks"][3],
            {
                "id": "T4",
                "title": "Render the board",
                "status": "assigned",
                "owner": "fullstack-developer#1",
                "dependencies": ["T1"],
            },
        )
        self.assertEqual([task["id"] for task in payload["blocked"]], ["T2"])
        self.assertEqual(payload["next"]["id"], "T4")
        self.assertEqual(payload["repo"]["state"], "absent")
        self.assertIn("summary", payload["repo"])

    def test_non_git_project_states_the_absence_plainly(self):
        summary = summarize_project(self.project)

        self.assertEqual(summary.repo.state, "absent")
        self.assertIsNone(summary.repo.branch)
        self.assertIsNone(summary.repo.head)
        self.assertIsNone(summary.repo.commits_since_start)
        self.assertIn("not in a Git repository", summary.repo.summary)

    def test_unreadable_git_worktree_degrades_instead_of_crashing(self):
        (self.project / ".git").write_text(
            "gitdir: ./nowhere-at-all\n", encoding="utf-8"
        )

        summary = summarize_project(self.project)

        self.assertEqual(summary.repo.state, "unavailable")
        self.assertIsNone(summary.repo.branch)
        self.assertIsNone(summary.repo.commits_since_start)
        self.assertIn("could not be read", summary.repo.summary)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_repo_line_reports_branch_head_commit_count_and_dirty_tree(self):
        self.start_repository()
        self.commit_all("before kickoff", "2026-07-22T00:00:00+00:00")
        (self.project / "artifact.txt").write_text("changed\n", encoding="utf-8")
        self.commit_all("first crew commit", "2026-07-23T01:00:00+00:00")
        (self.project / "artifact.txt").write_text("changed twice\n", encoding="utf-8")
        self.commit_all("second crew commit", "2026-07-23T02:00:00+00:00")
        (self.project / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")

        summary = summarize_project(self.project)

        self.assertEqual(summary.repo.state, "ok")
        self.assertEqual(summary.repo.branch, "work")
        self.assertFalse(summary.repo.detached)
        self.assertEqual(
            summary.repo.head,
            self.run_git("rev-parse", "--short", "HEAD").strip(),
        )
        self.assertEqual(summary.repo.commits_since_start, 2)
        self.assertFalse(summary.repo.clean)
        self.assertEqual(summary.repo.changed_files, 1)
        self.assertIn("branch work", summary.repo.summary)
        self.assertIn("2 commits since kickoff", summary.repo.summary)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_clean_worktree_is_reported_as_clean(self):
        self.start_repository()
        self.commit_all("only commit", "2026-07-23T01:00:00+00:00")

        summary = summarize_project(self.project)

        self.assertTrue(summary.repo.clean)
        self.assertEqual(summary.repo.changed_files, 0)
        self.assertIn("working tree clean", summary.repo.summary)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_ambient_git_configuration_cannot_hide_uncommitted_work(self):
        self.start_repository()
        self.commit_all("only commit", "2026-07-23T01:00:00+00:00")
        (self.project / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
        self.run_git("config", "status.showUntrackedFiles", "no")
        self.run_git("config", "log.showSignature", "true")

        summary = summarize_project(self.project)

        self.assertFalse(summary.repo.clean)
        self.assertEqual(summary.repo.changed_files, 1)
        self.assertEqual(summary.repo.commits_since_start, 1)
        self.assertIn("1 uncommitted or untracked file", summary.repo.summary)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_detached_head_reports_no_branch_and_never_guesses_one(self):
        self.start_repository()
        self.commit_all("only commit", "2026-07-23T01:00:00+00:00")
        head = self.run_git("rev-parse", "HEAD").strip()
        self.run_git("checkout", "-q", "--detach", head)

        summary = summarize_project(self.project)

        self.assertEqual(summary.repo.state, "ok")
        self.assertIsNone(summary.repo.branch)
        self.assertTrue(summary.repo.detached)
        self.assertIn("detached HEAD", summary.repo.summary)

    @unittest.skipUnless(shutil.which("git"), "Git is required for this behavior")
    def test_unknown_run_start_reports_unknown_rather_than_a_number(self):
        self.start_repository()
        self.commit_all("only commit", "2026-07-23T01:00:00+00:00")
        metadata = self.read_metadata()
        del metadata["created"]
        self.write_metadata(metadata)

        summary = summarize_project(self.project)

        self.assertIsNone(summary.repo.commits_since_start)
        self.assertIn("unknown", summary.repo.summary)
        self.assertNotIn("0 commits", summary.repo.summary)

    def test_missing_project_state_is_an_actionable_status_error(self):
        empty = Path(self.tempdir.name) / "empty"
        empty.mkdir()

        with self.assertRaises(StatusError) as raised:
            summarize_project(empty)

        self.assertIn("No Hamilton project state", str(raised.exception))
        self.assertTrue(raised.exception.remediation)

    def test_missing_directory_is_an_actionable_status_error(self):
        with self.assertRaises(StatusError) as raised:
            summarize_project(Path(self.tempdir.name) / "not-there")

        self.assertIn("not a directory", str(raised.exception))
        self.assertTrue(raised.exception.remediation)

    def test_unsupported_schema_version_refuses_with_upgrade_remediation(self):
        metadata = self.read_metadata()
        metadata["schema_version"] = CURRENT_SCHEMA_VERSION + 98
        self.write_metadata(metadata)

        with self.assertRaises(StatusError) as raised:
            summarize_project(self.project)

        self.assertIn("newer than supported", str(raised.exception))
        self.assertIn("upgrade Aphelocoma", raised.exception.remediation)

    def test_prerelease_protocol_refuses_with_its_own_remediation(self):
        metadata = self.read_metadata()
        metadata["protocol_version"] = "1.0.0-alpha"
        self.write_metadata(metadata)

        with self.assertRaises(StatusError) as raised:
            summarize_project(self.project)

        self.assertIn("distinct contracts", raised.exception.remediation)

    def test_unreadable_task_board_names_the_artifact_and_remediation(self):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        path.write_text("{not json", encoding="utf-8")

        with self.assertRaises(StatusError) as raised:
            summarize_project(self.project)

        self.assertEqual(raised.exception.path, "state/tasks.json")
        self.assertTrue(raised.exception.remediation)

    def test_privacy_findings_do_not_refuse_the_board(self):
        (self.project / ".aphelocoma" / "settings.yaml").write_text(
            "visibility: local\n", encoding="utf-8"
        )

        summary = summarize_project(self.project)

        self.assertEqual(summary.visibility, "local")

    def test_unknown_visibility_is_reported_as_unknown_not_guessed(self):
        (self.project / ".aphelocoma" / "settings.yaml").write_text(
            "redact_sensitive: true\n", encoding="utf-8"
        )

        summary = summarize_project(self.project)

        self.assertIsNone(summary.visibility)


class StatusReportFileTests(ProjectFixture):
    """`.aphelocoma/STATUS.md` — the regenerated board file of PROTOCOL §5.6."""

    def status_path(self):
        return self.project / ".aphelocoma" / "STATUS.md"

    def write_tasks(self, tasks):
        path = self.project / ".aphelocoma" / "state" / "tasks.json"
        board = json.loads(path.read_text(encoding="utf-8"))
        board["tasks"] = tasks
        path.write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")

    def regenerate(self):
        return write_status_report(self.project, summarize_project(self.project))

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
        ]

    def test_report_names_the_stage_the_progress_and_every_task(self):
        self.write_tasks(self.sample_tasks())

        path = self.regenerate()

        self.assertEqual(path, self.status_path().resolve())
        text = path.read_text(encoding="utf-8")
        self.assertIn("fixture-current", text)
        self.assertIn("done", text)
        self.assertIn("1 of 2 tasks done", text)
        for task in self.sample_tasks():
            self.assertIn(task["id"], text)
            self.assertIn(task["title"], text)
            self.assertIn(task["status"], text)

    def test_every_write_regenerates_the_whole_file(self):
        self.write_tasks(self.sample_tasks())
        self.regenerate()
        self.status_path().write_text(
            self.status_path().read_text(encoding="utf-8") + "hand-edited drift\n",
            encoding="utf-8",
        )
        self.write_tasks(self.sample_tasks()[:1])

        text = self.regenerate().read_text(encoding="utf-8")

        self.assertNotIn("hand-edited drift", text)
        self.assertNotIn("Unblock the pipeline", text)
        self.assertIn("Ship the base", text)
        self.assertEqual(text.count("Ship the base"), 1)
        self.assertIn("1 of 1 tasks done", text)

    def test_stamp_names_the_utc_time_and_the_ledger_sequence(self):
        text = self.regenerate().read_text(encoding="utf-8")

        self.assertRegex(
            text,
            r"(?m)^Generated \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z "
            r"from ledger seq 9\b",
        )

    def test_unreadable_ledger_stamps_an_unknown_sequence(self):
        (self.project / ".aphelocoma" / "ledger" / "events.jsonl").unlink()

        text = self.regenerate().read_text(encoding="utf-8")

        self.assertIn("from ledger seq unknown", text)

    def test_write_is_atomic_and_leaves_no_temporary_file_behind(self):
        self.regenerate()

        leftovers = [
            path.name
            for path in (self.project / ".aphelocoma").iterdir()
            if path.name.endswith(".tmp")
        ]

        self.assertEqual(leftovers, [])

    def test_table_syntax_in_a_title_cannot_break_the_row(self):
        self.write_tasks(
            [
                {
                    "id": "T1",
                    "title": "Pipe | and\nnewline",
                    "owner": "fullstack-developer",
                    "status": "done",
                    "dependencies": [],
                }
            ]
        )

        text = self.regenerate().read_text(encoding="utf-8")

        row = next(
            line
            for line in text.splitlines()
            if line.startswith("|") and "T1" in line
        )
        self.assertIn(r"Pipe \| and newline", row)
        self.assertEqual(row.count("|") - row.count(r"\|"), 4)

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root ignores directory permissions",
    )
    def test_unwritable_state_directory_is_an_actionable_status_error(self):
        state = self.project / ".aphelocoma"
        original = state.stat().st_mode
        state.chmod(0o500)
        try:
            with self.assertRaises(StatusError) as raised:
                self.regenerate()
        finally:
            state.chmod(original)

        self.assertIn("STATUS.md", raised.exception.path)
        self.assertTrue(raised.exception.remediation)


class StatusReportStalenessTests(ProjectFixture):
    """A stale board is a visibility miss: it warns, and never blocks resume."""

    def status_path(self):
        return self.project / ".aphelocoma" / "STATUS.md"

    def status_warnings(self, report):
        return [
            issue
            for issue in report.warnings
            if issue.code.endswith("status_report")
        ]

    def test_missing_status_report_warns_without_erroring(self):
        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        warnings = self.status_warnings(report)
        self.assertEqual([issue.code for issue in warnings], ["missing_status_report"])
        self.assertIn("STATUS.md", warnings[0].message)
        self.assertIn("aph status --write", warnings[0].remediation)

    def test_current_status_report_raises_no_warning(self):
        write_status_report(self.project, summarize_project(self.project))

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        self.assertEqual(self.status_warnings(report), [])

    def test_stale_status_report_names_how_far_behind_it_is(self):
        write_status_report(self.project, summarize_project(self.project))
        text = self.status_path().read_text(encoding="utf-8")
        self.status_path().write_text(
            re.sub(r"from ledger seq \d+", "from ledger seq 6", text),
            encoding="utf-8",
        )

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        warnings = self.status_warnings(report)
        self.assertEqual([issue.code for issue in warnings], ["stale_status_report"])
        self.assertIn("3 event", warnings[0].message)
        self.assertIn("9", warnings[0].message)
        self.assertIn("aph status --write", warnings[0].remediation)

    def test_unstamped_status_report_is_not_trusted_as_current(self):
        self.status_path().write_text("# Hand-written board\n", encoding="utf-8")

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        self.assertEqual(
            [issue.code for issue in self.status_warnings(report)],
            ["stale_status_report"],
        )

    def restamp(self, sequence):
        """Rewrite only the stamp's ``seq``, leaving the rest of the board."""

        text = self.status_path().read_text(encoding="utf-8")
        self.status_path().write_text(
            re.sub(r"from ledger seq \d+", "from ledger seq %s" % sequence, text),
            encoding="utf-8",
        )

    def test_stamp_ahead_of_the_ledger_warns_instead_of_being_trusted(self):
        write_status_report(self.project, summarize_project(self.project))
        self.restamp(42)

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        warnings = self.status_warnings(report)
        self.assertEqual(
            [issue.code for issue in warnings], ["inconsistent_status_report"]
        )
        self.assertIn("42", warnings[0].message)
        self.assertIn("9", warnings[0].message)
        self.assertIn("ahead", warnings[0].message)
        self.assertIn("aph status --write", warnings[0].remediation)

    def test_stamp_naming_no_sequence_says_so_rather_than_missing(self):
        write_status_report(self.project, summarize_project(self.project))
        self.restamp("unknown")

        report = validate_project(self.project, tracked_files=[])

        self.assertTrue(report.ok, [issue.message for issue in report.errors])
        warnings = self.status_warnings(report)
        self.assertEqual(
            [issue.code for issue in warnings], ["unsequenced_status_report"]
        )
        self.assertIn("no ledger seq", warnings[0].message)
        self.assertNotIn("no readable generated stamp", warnings[0].message)
        self.assertIn("aph status --write", warnings[0].remediation)

    def test_writer_and_validator_read_the_same_last_seq(self):
        # A rolled-back tail: the last line's seq is 5 while the file's highest
        # seq is 9, so a writer and a validator that disagree about "last" also
        # disagree about whether this board is current.
        events = self.read_events()
        events.append(dict(events[-1], seq=5))
        self.write_events(events)

        write_status_report(self.project, summarize_project(self.project))

        self.assertRegex(
            self.status_path().read_text(encoding="utf-8"),
            r"(?m)^Generated \S+ from ledger seq 5\b",
        )
        report = validate_project(self.project, tracked_files=[])
        # The ledger itself is not gap-free, which is a separate error; the
        # board written from that same ledger must still read as current.
        self.assertEqual(self.status_warnings(report), [])


class UnversionedStatusBoardTests(ProjectFixture):
    fixture_name = "unversioned-v02"

    def test_unversioned_state_refuses_with_migration_remediation(self):
        with self.assertRaises(StatusError) as raised:
            summarize_project(self.project)

        self.assertIn("unversioned Hamilton v0.2", str(raised.exception))
        self.assertIn("migrate.py", raised.exception.remediation)


if __name__ == "__main__":
    unittest.main()
