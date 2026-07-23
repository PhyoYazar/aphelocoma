import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.deploy import (
    CODEX_BLOCK_END,
    CODEX_BLOCK_START,
    DeploymentError,
    deploy_hamilton,
    undeploy_hamilton,
)
from aphelocoma.doctor import DoctorContext, deployment_registry, run_checks
from aphelocoma.manifest import (
    ManifestError,
    digest_path,
    load_manifest,
    manifest_path,
    save_manifest,
)
from aphelocoma.paths import resolve_paths


def isolated_paths(base):
    home = base / "user's home"
    home.mkdir()
    root = base / "active root"
    return resolve_paths(
        {
            "HOME": str(home),
            "APHELOCOMA_ROOT": str(root),
        },
        tool_root=REPOSITORY,
    )


class DeploymentTests(unittest.TestCase):
    def test_symlinked_host_parent_is_refused_before_any_write(self):
        for tool in ("claude", "codex"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory(
                prefix=f"aph {tool} parent symlink "
            ) as directory:
                paths = isolated_paths(Path(directory))
                external = Path(directory) / "external host"
                external.mkdir()
                sentinel = external / "sentinel"
                sentinel.write_bytes(b"keep")
                (paths.home / f".{tool}").symlink_to(
                    external,
                    target_is_directory=True,
                )

                with self.assertRaisesRegex(DeploymentError, "symlink"):
                    deploy_hamilton(paths, tool)

                self.assertEqual(sentinel.read_bytes(), b"keep")
                self.assertEqual(list(external.iterdir()), [sentinel])
                self.assertFalse(manifest_path(paths.root, tool).exists())

    def test_resolved_root_and_backup_symlinks_cannot_escape_into_legacy_data(self):
        for protected_kind in ("default", "custom"):
            with self.subTest(protected=protected_kind), tempfile.TemporaryDirectory(
                prefix="aph deploy resolved legacy "
            ) as directory:
                base = Path(directory)
                home = base / "home"
                home.mkdir()
                protected = (
                    home / ".aphelocoma" / "data"
                    if protected_kind == "default"
                    else base / "custom legacy"
                )
                protected.mkdir(parents=True)
                sentinel = protected / "sentinel"
                sentinel.write_bytes(b"keep")
                root_parent = base / "root parent"
                root_parent.mkdir()
                (root_parent / "escape").symlink_to(
                    protected,
                    target_is_directory=True,
                )
                environment = {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(root_parent / "escape" / "nested"),
                }
                if protected_kind == "custom":
                    environment["APHELOCOMA_HOME"] = str(protected)
                paths = resolve_paths(environment, tool_root=REPOSITORY)

                with self.assertRaisesRegex(DeploymentError, "protected legacy"):
                    deploy_hamilton(paths, "claude")

                self.assertEqual(sentinel.read_bytes(), b"keep")
                self.assertEqual(list(protected.iterdir()), [sentinel])

        with tempfile.TemporaryDirectory(
            prefix="aph deploy backup symlink "
        ) as directory:
            base = Path(directory)
            protected = base / "custom legacy"
            protected.mkdir()
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            paths = isolated_paths(base)
            paths.root.mkdir()
            (paths.root / "backups").symlink_to(
                protected,
                target_is_directory=True,
            )

            with self.assertRaisesRegex(DeploymentError, "symlink"):
                deploy_hamilton(paths, "claude")

            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])
            self.assertFalse((paths.home / ".claude").exists())

    def test_claude_deploy_is_hamilton_only_idempotent_and_reversible(self):
        with tempfile.TemporaryDirectory(prefix="aph deploy claude ") as directory:
            paths = isolated_paths(Path(directory))
            claude_home = paths.home / ".claude"
            claude_home.mkdir()
            user_config = claude_home / "CLAUDE.md"
            user_config.write_bytes(b"# User instructions\n")

            first = deploy_hamilton(paths, "claude")
            first_manifest = load_manifest(manifest_path(paths.root, "claude"), "claude")
            second = deploy_hamilton(paths, "claude")

            self.assertTrue(first.ok)
            self.assertTrue(second.ok)
            self.assertEqual(user_config.read_bytes(), b"# User instructions\n")
            skill = claude_home / "skills" / "aph-hamilton"
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "references" / "PROTOCOL.md").is_file())
            self.assertEqual(
                sorted(path.name for path in (claude_home / "skills").iterdir()),
                ["aph-hamilton"],
            )
            self.assertEqual(
                len(list((claude_home / "agents").glob("hamilton-*.md"))),
                27,
            )
            self.assertEqual(first_manifest["tool"], "claude")
            self.assertEqual(first_manifest["schema_version"], 1)
            self.assertTrue(
                all("digest" in artifact for artifact in first_manifest["artifacts"])
            )

            removed = undeploy_hamilton(paths, "claude")
            repeated = undeploy_hamilton(paths, "claude")

            self.assertTrue(removed.ok, removed.messages)
            self.assertTrue(repeated.ok, repeated.messages)
            self.assertFalse(skill.exists())
            self.assertEqual(
                list((claude_home / "agents").glob("hamilton-*.md")),
                [],
            )
            self.assertEqual(user_config.read_bytes(), b"# User instructions\n")

    def test_collision_is_backed_up_and_restored_on_undeploy(self):
        with tempfile.TemporaryDirectory(prefix="aph deploy collision ") as directory:
            paths = isolated_paths(Path(directory))
            skill = paths.home / ".claude" / "skills" / "aph-hamilton"
            skill.mkdir(parents=True)
            (skill / "personal.txt").write_bytes(b"preexisting skill")
            agent = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            agent.parent.mkdir(parents=True)
            agent.write_bytes(b"preexisting agent")

            result = deploy_hamilton(paths, "claude")
            deployment = load_manifest(result.manifest_path, "claude")

            self.assertTrue(result.ok)
            by_path = {artifact["path"]: artifact for artifact in deployment["artifacts"]}
            self.assertIsNotNone(by_path[str(skill)]["backup"])
            self.assertIsNotNone(by_path[str(agent)]["backup"])
            self.assertNotEqual((skill / "SKILL.md").read_bytes(), b"preexisting skill")

            removed = undeploy_hamilton(paths, "claude")

            self.assertTrue(removed.ok, removed.messages)
            self.assertEqual((skill / "personal.txt").read_bytes(), b"preexisting skill")
            self.assertEqual(agent.read_bytes(), b"preexisting agent")

    def test_undeploy_preserves_modified_owned_file_and_reports_drift(self):
        with tempfile.TemporaryDirectory(prefix="aph deploy drift ") as directory:
            paths = isolated_paths(Path(directory))
            deploy_hamilton(paths, "claude")
            agent = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            agent.write_bytes(b"user modified this generated role\n")

            result = undeploy_hamilton(paths, "claude")

            self.assertFalse(result.ok)
            self.assertTrue(agent.exists())
            self.assertEqual(agent.read_bytes(), b"user modified this generated role\n")
            self.assertTrue(manifest_path(paths.root, "claude").exists())
            self.assertTrue(any("drift" in message.lower() for message in result.messages))

    def test_corrupt_manifest_refuses_deploy_and_undeploy_without_touching_host(self):
        with tempfile.TemporaryDirectory(prefix="aph corrupt manifest ") as directory:
            paths = isolated_paths(Path(directory))
            target = paths.home / ".claude" / "personal.txt"
            target.parent.mkdir()
            target.write_bytes(b"keep")
            path = manifest_path(paths.root, "claude")
            path.parent.mkdir(parents=True)
            path.write_text("{bad json", encoding="utf-8")

            with self.assertRaises(ManifestError):
                deploy_hamilton(paths, "claude")
            with self.assertRaises(ManifestError):
                undeploy_hamilton(paths, "claude")

            self.assertEqual(target.read_bytes(), b"keep")

    def test_codex_deploy_preserves_user_config_and_undeploys_only_managed_block(self):
        with tempfile.TemporaryDirectory(prefix="aph deploy codex ") as directory:
            paths = isolated_paths(Path(directory))
            codex_home = paths.home / ".codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_bytes(b'model = "user-model"\n')

            result = deploy_hamilton(paths, "codex")
            repeated = deploy_hamilton(paths, "codex")

            self.assertTrue(result.ok)
            self.assertTrue(repeated.ok)
            text = config.read_text(encoding="utf-8")
            self.assertIn('model = "user-model"', text)
            self.assertEqual(text.count("[agents.hamilton-"), 27)
            self.assertEqual(
                len(list((codex_home / "agents").glob("hamilton-*.toml"))),
                27,
            )
            self.assertTrue(
                (codex_home / "skills" / "aph-hamilton" / "SKILL.md").is_file()
            )

            removed = undeploy_hamilton(paths, "codex")

            self.assertTrue(removed.ok, removed.messages)
            self.assertEqual(config.read_bytes(), b'model = "user-model"\n')
            self.assertEqual(
                list((codex_home / "agents").glob("hamilton-*.toml")),
                [],
            )

    def test_codex_deploy_refuses_unowned_canonical_block_before_host_mutation(self):
        with tempfile.TemporaryDirectory(prefix="aph codex unowned block ") as directory:
            paths = isolated_paths(Path(directory))
            config = paths.home / ".codex" / "config.toml"
            config.parent.mkdir()
            config.write_text(
                CODEX_BLOCK_START
                + "\n[agents.user-owned]\n"
                + 'config_file = "./agents/user-owned.toml"\n'
                + CODEX_BLOCK_END
                + "\n",
                encoding="utf-8",
            )
            before = config.read_bytes()

            with self.assertRaisesRegex(DeploymentError, "unowned"):
                deploy_hamilton(paths, "codex")

            self.assertEqual(config.read_bytes(), before)
            self.assertFalse((paths.home / ".codex" / "skills").exists())
            self.assertFalse((paths.home / ".codex" / "agents").exists())
            self.assertFalse(manifest_path(paths.root, "codex").exists())
            report = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )
            deployments = next(
                item for item in report.checks if item.id == "deployments"
            )
            self.assertEqual(deployments.status, "error")
            self.assertIn("unowned", deployments.message.lower())
            self.assertEqual(report.exit_code, 1)

    def test_codex_managed_block_drift_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory(prefix="aph codex block drift ") as directory:
            paths = isolated_paths(Path(directory))
            deploy_hamilton(paths, "codex")
            config = paths.home / ".codex" / "config.toml"
            text = config.read_text(encoding="utf-8")
            config.write_text(
                text.replace(
                    "[agents.hamilton-cto]",
                    "[agents.hamilton-cto]\ncustom = true",
                ),
                encoding="utf-8",
            )

            result = undeploy_hamilton(paths, "codex")

            self.assertFalse(result.ok)
            self.assertIn("custom = true", config.read_text(encoding="utf-8"))
            self.assertTrue(any("managed block drift" in item.lower() for item in result.messages))

    def test_tampered_codex_manifest_markers_cannot_delete_user_configuration(self):
        with tempfile.TemporaryDirectory(prefix="aph codex marker tamper ") as directory:
            paths = isolated_paths(Path(directory))
            config = paths.home / ".codex" / "config.toml"
            config.parent.mkdir()
            config.write_bytes(b'model = "keep"\n')
            result = deploy_hamilton(paths, "codex")
            deployment = load_manifest(result.manifest_path, "codex")
            deployment["managed_blocks"][0]["start_marker"] = 'model = "keep"'
            save_manifest(result.manifest_path, deployment)
            before = config.read_bytes()
            agent = paths.home / ".codex" / "agents" / "hamilton-cto.toml"

            with self.assertRaisesRegex(ManifestError, "marker"):
                undeploy_hamilton(paths, "codex")

            self.assertEqual(config.read_bytes(), before)
            self.assertTrue(agent.exists())

    def test_injected_deploy_failure_rolls_back_every_host_change(self):
        with tempfile.TemporaryDirectory(prefix="aph deploy rollback ") as directory:
            paths = isolated_paths(Path(directory))
            claude_home = paths.home / ".claude"
            claude_home.mkdir()
            personal = claude_home / "personal.txt"
            personal.write_bytes(b"keep")

            with self.assertRaisesRegex(DeploymentError, "injected"):
                deploy_hamilton(paths, "claude", fail_at="after_first_artifact")

            self.assertEqual(personal.read_bytes(), b"keep")
            self.assertFalse((claude_home / "skills" / "aph-hamilton").exists())
            self.assertFalse(manifest_path(paths.root, "claude").exists())

    def test_partial_generator_failure_never_reaches_host_directories(self):
        with tempfile.TemporaryDirectory(prefix="aph generator deploy failure ") as directory:
            paths = isolated_paths(Path(directory))

            with self.assertRaisesRegex(DeploymentError, "generator failed"):
                deploy_hamilton(paths, "codex", fail_at="during_generator")

            self.assertFalse((paths.home / ".codex").exists())
            self.assertFalse(manifest_path(paths.root, "codex").exists())

    def test_deploy_refuses_active_root_inside_custom_protected_legacy_path(self):
        with tempfile.TemporaryDirectory(prefix="aph protected root deploy ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            protected = base / "custom legacy"
            protected.mkdir()
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(protected),
                    "APHELOCOMA_HOME": str(protected),
                },
                tool_root=REPOSITORY,
            )

            with self.assertRaisesRegex(DeploymentError, "protected legacy"):
                deploy_hamilton(paths, "claude")

            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])

    def test_deploy_refuses_protected_data_nested_inside_owned_skill(self):
        with tempfile.TemporaryDirectory(prefix="aph reverse deploy overlap ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            protected = (
                home
                / ".claude"
                / "skills"
                / "aph-hamilton"
                / "legacy-data"
            )
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

            with self.assertRaisesRegex(DeploymentError, "protected legacy"):
                deploy_hamilton(paths, "claude")

            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])
            self.assertFalse(manifest_path(paths.root, "claude").exists())

    def test_codex_config_symlink_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory(prefix="aph codex config symlink ") as directory:
            paths = isolated_paths(Path(directory))
            external = Path(directory) / "external-config.toml"
            external.write_bytes(b'model = "external"\n')
            config = paths.home / ".codex" / "config.toml"
            config.parent.mkdir()
            config.symlink_to(external)

            with self.assertRaisesRegex(DeploymentError, "symlink"):
                deploy_hamilton(paths, "codex")

            self.assertTrue(config.is_symlink())
            self.assertEqual(external.read_bytes(), b'model = "external"\n')
            self.assertFalse(manifest_path(paths.root, "codex").exists())

    def test_doctor_rejects_manifest_missing_expected_agent_inventory(self):
        with tempfile.TemporaryDirectory(prefix="aph incomplete deployment ") as directory:
            paths = isolated_paths(Path(directory))
            result = deploy_hamilton(paths, "claude")
            deployment = load_manifest(result.manifest_path, "claude")
            deployment["artifacts"] = [
                artifact
                for artifact in deployment["artifacts"]
                if not artifact["path"].endswith("hamilton-cto.md")
            ]
            save_manifest(result.manifest_path, deployment)

            report = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )

            diagnostic = next(
                item for item in report.checks if item.id == "deployments"
            )
            self.assertEqual(diagnostic.status, "error")
            self.assertIn("inventory", diagnostic.message.lower())
            remaining = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            before = remaining.read_bytes()

            with self.assertRaisesRegex(ManifestError, "inventory"):
                undeploy_hamilton(paths, "claude")

            self.assertEqual(remaining.read_bytes(), before)

    def test_tampered_collision_backup_is_reported_and_refused_before_mutation(self):
        for tamper in ("digest", "missing"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory(
                prefix="aph collision backup tamper "
            ) as directory:
                paths = isolated_paths(Path(directory))
                collision = (
                    paths.home / ".claude" / "agents" / "hamilton-cto.md"
                )
                collision.parent.mkdir(parents=True)
                collision.write_bytes(b"preexisting")
                result = deploy_hamilton(paths, "claude")
                deployment = load_manifest(result.manifest_path, "claude")
                record = next(
                    item
                    for item in deployment["collisions"]
                    if item["path"] == str(collision)
                )
                backup = Path(record["backup"])
                if tamper == "digest":
                    backup.write_bytes(b"tampered")
                else:
                    backup.unlink()
                generated = collision.read_bytes()
                other = (
                    paths.home
                    / ".claude"
                    / "agents"
                    / "hamilton-backend-developer.md"
                )

                report = run_checks(
                    DoctorContext(paths=paths, cwd=Path(directory)),
                    deployment_registry(),
                )
                diagnostic = next(
                    item for item in report.checks if item.id == "deployments"
                )
                self.assertEqual(diagnostic.status, "error")
                self.assertIn("backup", diagnostic.message.lower())

                with self.assertRaisesRegex(ManifestError, "backup"):
                    undeploy_hamilton(paths, "claude")

                self.assertEqual(collision.read_bytes(), generated)
                self.assertTrue(other.exists())


class ManifestValidationTests(unittest.TestCase):
    def test_digest_path_changes_for_file_and_tree_drift(self):
        with tempfile.TemporaryDirectory(prefix="aph digest ") as directory:
            root = Path(directory)
            nested = root / "tree"
            nested.mkdir()
            file_path = nested / "file.txt"
            file_path.write_bytes(b"one")
            first_file = digest_path(file_path)
            first_tree = digest_path(nested)

            file_path.write_bytes(b"two")

            self.assertNotEqual(digest_path(file_path), first_file)
            self.assertNotEqual(digest_path(nested), first_tree)

    def test_collision_records_are_schema_validated(self):
        with tempfile.TemporaryDirectory(prefix="aph collision schema ") as directory:
            paths = isolated_paths(Path(directory))
            target = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preexisting")
            result = deploy_hamilton(paths, "claude")
            deployment = load_manifest(result.manifest_path, "claude")

            deployment["collisions"][0]["digest"] = "not-a-digest"

            with self.assertRaisesRegex(ManifestError, "collisions"):
                save_manifest(result.manifest_path, deployment)


class DeploymentDoctorTests(unittest.TestCase):
    def test_no_host_cli_reports_truthful_sequential_fallback_without_failure(self):
        with tempfile.TemporaryDirectory(prefix="aph doctor fallback ") as directory:
            paths = isolated_paths(Path(directory))
            with mock.patch("aphelocoma.doctor.shutil.which", return_value=None):
                report = run_checks(
                    DoctorContext(paths=paths, cwd=Path(directory)),
                    deployment_registry(),
                )

            hosts = next(item for item in report.checks if item.id == "host-tools")
            self.assertEqual(hosts.status, "ok")
            self.assertIn("sequential fallback", hosts.message.lower())

    def test_outdated_host_cli_is_actionable(self):
        with tempfile.TemporaryDirectory(prefix="aph old hosts ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            executables = base / "bin"
            executables.mkdir()
            for name, version in (("claude", "1.0.0"), ("codex", "0.1.0")):
                executable = executables / name
                executable.write_text(
                    "#!/bin/sh\nprintf '%s\\n' '" + version + "'\n",
                    encoding="utf-8",
                )
                executable.chmod(0o755)
            with mock.patch.dict(os.environ, {"PATH": str(executables)}):
                report = run_checks(
                    DoctorContext(paths=paths, cwd=base),
                    deployment_registry(),
                )

            hosts = next(item for item in report.checks if item.id == "host-tools")
            self.assertEqual(hosts.status, "error")
            self.assertIn("upgrade", hosts.remediation.lower())

    def test_deployment_doctor_detects_digest_drift_and_collision_backups(self):
        with tempfile.TemporaryDirectory(prefix="aph deployment doctor ") as directory:
            paths = isolated_paths(Path(directory))
            collision = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            collision.parent.mkdir(parents=True)
            collision.write_bytes(b"preexisting")
            deploy_hamilton(paths, "claude")
            healthy = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )
            deployments = next(
                item for item in healthy.checks if item.id == "deployments"
            )
            self.assertEqual(deployments.status, "ok")
            self.assertIn("collision backup", deployments.message.lower())

            collision.write_bytes(b"drift")
            unhealthy = run_checks(
                DoctorContext(paths=paths, cwd=Path(directory)),
                deployment_registry(),
            )
            deployments = next(
                item for item in unhealthy.checks if item.id == "deployments"
            )
            self.assertEqual(deployments.status, "error")
            self.assertIn("digest drift", deployments.message.lower())
