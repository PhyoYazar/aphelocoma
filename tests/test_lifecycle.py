import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.deploy import deploy_hamilton
from aphelocoma.lifecycle import (
    LifecycleError,
    PATH_BLOCK_END,
    PATH_BLOCK_START,
    activate_release,
    ensure_path_marker,
    install_manifest_path,
    remove_path_marker,
    uninstall_installation,
    update_installation,
)
from aphelocoma.manifest import digest_path
from aphelocoma.doctor import DoctorContext, deployment_registry, run_checks
from aphelocoma.paths import resolve_paths


def isolated_paths(base, custom_legacy=None):
    home = base / "user home"
    home.mkdir()
    environment = {
        "HOME": str(home),
        "APHELOCOMA_ROOT": str(base / "active root"),
    }
    if custom_legacy is not None:
        environment["APHELOCOMA_HOME"] = str(custom_legacy)
    return resolve_paths(environment, tool_root=REPOSITORY)


def make_release(base, version):
    release = base / ("release-" + version)
    release.mkdir()
    for name in ("bin", "src", "skills", "adapters"):
        source = REPOSITORY / name
        if source.exists():
            shutil.copytree(source, release / name)
    shutil.copy2(REPOSITORY / "install.sh", release / "install.sh")
    (release / "VERSION").write_text(version + "\n", encoding="utf-8")
    return release


class ActivationTests(unittest.TestCase):
    def test_default_root_can_mutate_owned_siblings_without_touching_legacy_data(self):
        with tempfile.TemporaryDirectory(prefix="aph normal default root ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            paths = resolve_paths(
                {"HOME": str(home)},
                tool_root=REPOSITORY,
            )
            paths.default_legacy_data.mkdir(parents=True)
            sentinel = paths.default_legacy_data / "sentinel"
            sentinel.write_bytes(b"keep")
            release = make_release(base, "0.3.0")

            result = activate_release(release, paths)

            self.assertTrue(result.ok)
            self.assertTrue((paths.root / "tool" / "bin" / "aph").is_file())
            self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_update_refuses_unexplained_active_tool_drift_before_replacement(self):
        with tempfile.TemporaryDirectory(prefix="aph update active drift ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            activate_release(old, paths)
            active = paths.root / "tool"
            manifest = install_manifest_path(paths.root)
            (active / "user-edit.txt").write_bytes(b"keep")
            before_digest = digest_path(active)
            before_manifest = manifest.read_bytes()

            with self.assertRaisesRegex(LifecycleError, "tool digest drift"):
                update_installation(paths, source=new)

            self.assertEqual(digest_path(active), before_digest)
            self.assertEqual(manifest.read_bytes(), before_manifest)
            self.assertEqual((active / "VERSION").read_text().strip(), "0.3.0")

    def test_resolved_root_and_backup_symlinks_cannot_escape_into_legacy_data(self):
        for protected_kind in ("default", "custom"):
            with self.subTest(protected=protected_kind), tempfile.TemporaryDirectory(
                prefix="aph lifecycle resolved legacy "
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
                parent = base / "root parent"
                parent.mkdir()
                (parent / "escape").symlink_to(
                    protected,
                    target_is_directory=True,
                )
                environment = {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(parent / "escape" / "nested"),
                }
                if protected_kind == "custom":
                    environment["APHELOCOMA_HOME"] = str(protected)
                paths = resolve_paths(environment, tool_root=REPOSITORY)
                release = make_release(base, "0.3.0")

                with self.assertRaisesRegex(LifecycleError, "protected legacy"):
                    activate_release(release, paths)

                self.assertEqual(sentinel.read_bytes(), b"keep")
                self.assertEqual(list(protected.iterdir()), [sentinel])

        with tempfile.TemporaryDirectory(
            prefix="aph lifecycle backup symlink "
        ) as directory:
            base = Path(directory)
            protected = base / "custom legacy"
            protected.mkdir()
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            activate_release(old, paths)
            (paths.root / "backups").symlink_to(
                protected,
                target_is_directory=True,
            )
            before = digest_path(paths.root / "tool")

            with self.assertRaisesRegex(LifecycleError, "symlink"):
                update_installation(paths, source=new)

            self.assertEqual(digest_path(paths.root / "tool"), before)
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])

    def test_interrupted_clean_install_leaves_no_partial_active_tool(self):
        with tempfile.TemporaryDirectory(prefix="aph install interrupted ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")

            with self.assertRaisesRegex(LifecycleError, "injected"):
                activate_release(release, paths, fail_at="after_activate")

            self.assertFalse((paths.root / "tool").exists())
            self.assertFalse(install_manifest_path(paths.root).exists())
            self.assertEqual(list(paths.root.glob(".stage-*")), [])

    def test_failed_update_restores_previous_tool_and_manifest_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="aph update rollback ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            activate_release(old, paths)
            active = paths.root / "tool"
            before_digest = digest_path(active)
            manifest = install_manifest_path(paths.root)
            before_manifest = manifest.read_bytes()

            with self.assertRaisesRegex(LifecycleError, "injected"):
                activate_release(new, paths, fail_at="after_activate")

            self.assertEqual(digest_path(active), before_digest)
            self.assertEqual(manifest.read_bytes(), before_manifest)
            self.assertEqual((active / "VERSION").read_text().strip(), "0.3.0")

    def test_successful_update_records_recoverable_previous_tool(self):
        with tempfile.TemporaryDirectory(prefix="aph update success ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            activate_release(old, paths)

            result = activate_release(new, paths)
            manifest = json.loads(
                install_manifest_path(paths.root).read_text(encoding="utf-8")
            )

            self.assertTrue(result.ok)
            self.assertEqual((paths.root / "tool" / "VERSION").read_text().strip(), "0.3.1")
            recovery = Path(manifest["recovery"])
            self.assertTrue(recovery.is_dir())
            self.assertEqual((recovery / "VERSION").read_text().strip(), "0.3.0")
            self.assertEqual(manifest["tool_digest"], digest_path(paths.root / "tool"))

    def test_manifest_owned_path_block_allows_repeated_update(self):
        with tempfile.TemporaryDirectory(prefix="aph owned path update ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            shell_rc = paths.home / ".zshrc"

            activate_release(old, paths, shell_rc=shell_rc)
            result = activate_release(new, paths, shell_rc=shell_rc)

            self.assertTrue(result.ok)
            self.assertEqual(
                (paths.root / "tool" / "VERSION").read_text().strip(),
                "0.3.1",
            )
            shell = shell_rc.read_text(encoding="utf-8")
            self.assertEqual(shell.count(PATH_BLOCK_START), 1)
            self.assertEqual(shell.count(PATH_BLOCK_END), 1)

    def test_update_rolls_back_when_owned_path_marker_has_drifted(self):
        with tempfile.TemporaryDirectory(prefix="aph update path drift ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            shell_rc = paths.home / ".zshrc"
            shell_rc.write_bytes(b"export KEEP=1\n")
            activate_release(old, paths, shell_rc=shell_rc)
            shell_rc.write_text(
                shell_rc.read_text().replace(
                    'export PATH=',
                    'export USER_EDIT=1\nexport PATH=',
                ),
                encoding="utf-8",
            )
            drifted = shell_rc.read_bytes()

            with self.assertRaisesRegex(LifecycleError, "PATH managed block drift"):
                activate_release(new, paths, shell_rc=shell_rc)

            self.assertEqual(
                (paths.root / "tool" / "VERSION").read_text().strip(),
                "0.3.0",
            )
            self.assertEqual(shell_rc.read_bytes(), drifted)

    def test_clean_activation_refuses_unowned_canonical_path_block(self):
        with tempfile.TemporaryDirectory(prefix="aph unowned path block ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")
            shell_rc = paths.home / ".zshrc"
            shell_rc.write_text(
                PATH_BLOCK_START
                + "\nexport USER_OWNED=1\n"
                + PATH_BLOCK_END
                + "\n",
                encoding="utf-8",
            )
            before = shell_rc.read_bytes()

            with self.assertRaisesRegex(LifecycleError, "unowned"):
                activate_release(release, paths, shell_rc=shell_rc)

            self.assertEqual(shell_rc.read_bytes(), before)
            self.assertFalse((paths.root / "tool").exists())
            self.assertFalse(install_manifest_path(paths.root).exists())
            report = run_checks(
                DoctorContext(paths=paths, cwd=base),
                deployment_registry(),
            )
            installation = next(
                item for item in report.checks if item.id == "installation"
            )
            self.assertEqual(installation.status, "error")
            self.assertIn("unowned", installation.message.lower())
            self.assertEqual(report.exit_code, 1)

    def test_clean_activation_preflights_unselected_supported_shell_files(self):
        for collision_name in (".bashrc", ".bash_profile"):
            with self.subTest(collision=collision_name), tempfile.TemporaryDirectory(
                prefix="aph cross shell path collision "
            ) as directory:
                base = Path(directory)
                paths = isolated_paths(base)
                release = make_release(base, "0.3.0")
                selected_shell = paths.home / ".zshrc"
                selected_shell.write_bytes(b"export KEEP_ZSH=1\n")
                collision_shell = paths.home / collision_name
                collision_shell.write_text(
                    PATH_BLOCK_START
                    + "\nexport USER_OWNED=1\n"
                    + PATH_BLOCK_END
                    + "\n",
                    encoding="utf-8",
                )
                untouched_shell = paths.home / (
                    ".bash_profile"
                    if collision_name == ".bashrc"
                    else ".bashrc"
                )
                untouched_shell.write_bytes(b"export KEEP_OTHER=1\n")
                shell_bytes = {
                    path: path.read_bytes()
                    for path in (selected_shell, collision_shell, untouched_shell)
                }

                with self.assertRaisesRegex(
                    LifecycleError,
                    rf"unowned.*{re.escape(collision_name)}",
                ):
                    activate_release(
                        release,
                        paths,
                        shell_rc=selected_shell,
                    )

                self.assertFalse(paths.root.exists())
                self.assertFalse((paths.root / "tool").exists())
                self.assertFalse(install_manifest_path(paths.root).exists())
                for path, before in shell_bytes.items():
                    self.assertEqual(path.read_bytes(), before)

    def test_activation_refuses_custom_protected_legacy_path_as_active_root(self):
        with tempfile.TemporaryDirectory(prefix="aph protected root lifecycle ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            protected = base / "custom legacy"
            protected.mkdir()
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            release = make_release(base, "0.3.0")
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(protected),
                    "APHELOCOMA_HOME": str(protected),
                },
                tool_root=REPOSITORY,
            )

            with self.assertRaisesRegex(LifecycleError, "protected legacy"):
                activate_release(release, paths)

            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(list(protected.iterdir()), [sentinel])

    def test_activation_refuses_protected_data_nested_inside_owned_tool(self):
        with tempfile.TemporaryDirectory(prefix="aph reverse lifecycle overlap ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            root = base / "active"
            protected = root / "tool" / "legacy-data"
            protected.mkdir(parents=True)
            sentinel = protected / "sentinel"
            sentinel.write_bytes(b"keep")
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(root),
                    "APHELOCOMA_HOME": str(protected),
                },
                tool_root=REPOSITORY,
            )
            release = make_release(base, "0.3.0")

            with self.assertRaisesRegex(LifecycleError, "protected legacy"):
                activate_release(release, paths)

            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(
                set(root.rglob("*")),
                {root / "tool", protected, sentinel},
            )
            self.assertFalse(install_manifest_path(root).exists())

    def test_activation_cleans_only_proven_legacy_skill_trees(self):
        with tempfile.TemporaryDirectory(prefix="aph activation legacy cleanup ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")
            exact = paths.home / ".claude" / "skills" / "adr"
            exact.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "skills" / "adr" / "skill.md",
                exact / "SKILL.md",
            )
            shutil.copytree(
                REPOSITORY / "skills" / "adr" / "templates",
                exact / "templates",
            )
            modified = paths.home / ".codex" / "skills" / "capture"
            modified.mkdir(parents=True)
            shutil.copyfile(
                REPOSITORY / "skills" / "capture" / "skill.md",
                modified / "SKILL.md",
            )
            (modified / "user-note").write_bytes(b"keep")

            result = activate_release(release, paths)

            self.assertTrue(result.ok)
            self.assertFalse(exact.exists())
            self.assertEqual((modified / "user-note").read_bytes(), b"keep")
            self.assertTrue(any("removed exact legacy" in item.lower() for item in result.messages))
            self.assertTrue(any("preserved" in item.lower() for item in result.messages))


class PathMarkerTests(unittest.TestCase):
    def test_path_marker_is_idempotent_and_preserves_shell_configuration(self):
        with tempfile.TemporaryDirectory(prefix="aph path marker ") as directory:
            base = Path(directory)
            shell_rc = base / ".zshrc"
            shell_rc.write_bytes(b"export USER_SETTING=keep\n")
            bin_dir = base / "Alex's tool" / "bin"

            first = ensure_path_marker(shell_rc, bin_dir)
            second = ensure_path_marker(shell_rc, bin_dir)

            self.assertEqual(first.digest, second.digest)
            content = shell_rc.read_text(encoding="utf-8")
            self.assertIn("export USER_SETTING=keep", content)
            self.assertEqual(content.count("# >>> aphelocoma path >>>"), 1)
            self.assertIn("'\"'\"'", content)

            removed = remove_path_marker(shell_rc, first.digest)
            self.assertTrue(removed.ok)
            self.assertEqual(shell_rc.read_bytes(), b"export USER_SETTING=keep\n")

    def test_drifted_path_marker_is_not_removed(self):
        with tempfile.TemporaryDirectory(prefix="aph path drift ") as directory:
            shell_rc = Path(directory) / ".zshrc"
            marker = ensure_path_marker(shell_rc, Path(directory) / "tool" / "bin")
            shell_rc.write_text(
                shell_rc.read_text().replace(
                    'export PATH=',
                    'export CUSTOM=1\nexport PATH=',
                ),
                encoding="utf-8",
            )

            result = remove_path_marker(shell_rc, marker.digest)

            self.assertFalse(result.ok)
            self.assertIn("CUSTOM=1", shell_rc.read_text())


class InstallationDoctorTests(unittest.TestCase):
    def test_doctor_reports_active_tool_digest_and_path_marker_drift(self):
        with tempfile.TemporaryDirectory(prefix="aph install doctor ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")
            shell_rc = paths.home / ".zshrc"
            activate_release(release, paths, shell_rc=shell_rc)

            healthy = run_checks(
                DoctorContext(paths=paths, cwd=base),
                deployment_registry(),
            )
            installation = next(
                item for item in healthy.checks if item.id == "installation"
            )
            self.assertEqual(installation.status, "ok")

            (paths.root / "tool" / "user-edit").write_bytes(b"drift")
            drifted_tool = run_checks(
                DoctorContext(paths=paths, cwd=base),
                deployment_registry(),
            )
            installation = next(
                item for item in drifted_tool.checks if item.id == "installation"
            )
            self.assertEqual(installation.status, "error")
            self.assertIn("tool digest", installation.message.lower())
            self.assertEqual(drifted_tool.exit_code, 1)

            (paths.root / "tool" / "user-edit").unlink()
            shell_rc.write_text(
                shell_rc.read_text().replace(
                    "export PATH=",
                    "export USER_EDIT=1\nexport PATH=",
                ),
                encoding="utf-8",
            )
            drifted_path = run_checks(
                DoctorContext(paths=paths, cwd=base),
                deployment_registry(),
            )
            installation = next(
                item for item in drifted_path.checks if item.id == "installation"
            )
            self.assertEqual(installation.status, "error")
            self.assertIn("path", installation.message.lower())
            self.assertEqual(drifted_path.exit_code, 1)


class UninstallTests(unittest.TestCase):
    def test_uninstall_removes_owned_tool_deployments_and_path_not_legacy_or_backups(self):
        with tempfile.TemporaryDirectory(prefix="aph uninstall ") as directory:
            base = Path(directory)
            custom = base / "custom legacy"
            paths = isolated_paths(base, custom)
            release = make_release(base, "0.3.0")
            activate_release(release, paths)
            deploy_hamilton(paths, "claude")
            shell_rc = paths.home / ".zshrc"
            marker = ensure_path_marker(shell_rc, paths.root / "tool" / "bin")
            manifest = json.loads(install_manifest_path(paths.root).read_text())
            manifest["path_marker"] = marker.as_dict()
            install_manifest_path(paths.root).write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )
            for legacy, payload in (
                (paths.default_legacy_data, b"default"),
                (custom, b"custom"),
            ):
                legacy.mkdir(parents=True)
                (legacy / "sentinel").write_bytes(payload)
            backup = paths.root / "backups" / "keep.txt"
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(b"recovery")

            result = uninstall_installation(paths)

            self.assertTrue(result.ok, result.messages)
            self.assertFalse((paths.root / "tool").exists())
            self.assertFalse(install_manifest_path(paths.root).exists())
            self.assertFalse((paths.root / "manifests" / "claude.json").exists())
            self.assertEqual(shell_rc.read_bytes(), b"")
            self.assertEqual(
                (paths.default_legacy_data / "sentinel").read_bytes(),
                b"default",
            )
            self.assertEqual((custom / "sentinel").read_bytes(), b"custom")
            self.assertEqual(backup.read_bytes(), b"recovery")

    def test_uninstall_stops_before_tool_removal_when_deployment_drift_remains(self):
        with tempfile.TemporaryDirectory(prefix="aph uninstall drift ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")
            activate_release(release, paths)
            deploy_hamilton(paths, "claude")
            drift = paths.home / ".claude" / "agents" / "hamilton-cto.md"
            drift.write_bytes(b"user edit")

            result = uninstall_installation(paths)

            self.assertFalse(result.ok)
            self.assertTrue((paths.root / "tool").exists())
            self.assertTrue(drift.exists())

    def test_installed_cli_can_uninstall_after_python_bytecode_cache_is_created(self):
        with tempfile.TemporaryDirectory(prefix="aph cli uninstall ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            release = make_release(base, "0.3.0")
            activate_release(release, paths)
            executable = paths.root / "tool" / "bin" / "aph"
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.update(
                {
                    "HOME": str(paths.home),
                    "APHELOCOMA_ROOT": str(paths.root),
                }
            )
            version = subprocess.run(
                [str(executable), "version"],
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(version.returncode, 0, version.stderr)
            self.assertTrue(
                any((paths.root / "tool" / "src").rglob("__pycache__"))
            )

            completed = subprocess.run(
                [str(executable), "uninstall"],
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((paths.root / "tool").exists())


class CliUpdateTests(unittest.TestCase):
    def test_installed_cli_update_activates_local_verified_release(self):
        with tempfile.TemporaryDirectory(prefix="aph cli update ") as directory:
            base = Path(directory)
            paths = isolated_paths(base)
            old = make_release(base, "0.3.0")
            new = make_release(base, "0.3.1")
            activate_release(old, paths)
            executable = paths.root / "tool" / "bin" / "aph"
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(paths.home),
                    "APHELOCOMA_ROOT": str(paths.root),
                    "APHELOCOMA_UPDATE_SOURCE": str(new),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )

            completed = subprocess.run(
                [str(executable), "update"],
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (paths.root / "tool" / "VERSION").read_text().strip(),
                "0.3.1",
            )


class InstallerEntrypointTests(unittest.TestCase):
    def run_installer(self, home, root, source, fail_at=None):
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "APHELOCOMA_ROOT": str(root),
                "APHELOCOMA_INSTALL_SOURCE": str(source),
                "NO_COLOR": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        if fail_at:
            env["APHELOCOMA_FAIL_AT"] = fail_at
        return subprocess.run(
            ["bash", str(REPOSITORY / "install.sh")],
            cwd=str(home),
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_installer_activates_verified_tool_without_context_setup(self):
        with tempfile.TemporaryDirectory(prefix="aph installer ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            (home / ".zshrc").write_bytes(b"export KEEP=1\n")
            root = base / "root with spaces"

            completed = self.run_installer(home, root, REPOSITORY)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((root / "tool" / "bin" / "aph").is_file())
            self.assertTrue((root / "install.json").is_file())
            self.assertFalse((root / "data").exists())
            self.assertNotIn("setup", completed.stdout.lower())
            self.assertIn("# >>> aphelocoma path >>>", (home / ".zshrc").read_text())

    def test_installer_failure_after_activation_rolls_back_old_tool(self):
        with tempfile.TemporaryDirectory(prefix="aph installer rollback ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            root = base / "root"
            old_tool = root / "tool"
            old_tool.mkdir(parents=True)
            (old_tool / "sentinel").write_bytes(b"old")

            completed = self.run_installer(
                home,
                root,
                REPOSITORY,
                fail_at="after_activate",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual((old_tool / "sentinel").read_bytes(), b"old")

    def test_installer_reports_unowned_path_block_without_traceback(self):
        with tempfile.TemporaryDirectory(prefix="aph installer path collision ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            shell_rc = home / ".zshrc"
            shell_rc.write_text(
                PATH_BLOCK_START
                + "\nexport USER_OWNED=1\n"
                + PATH_BLOCK_END
                + "\n",
                encoding="utf-8",
            )
            before = shell_rc.read_bytes()
            root = base / "root"

            completed = self.run_installer(home, root, REPOSITORY)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("unowned", completed.stderr.lower())
            self.assertNotIn("traceback", completed.stderr.lower())
            self.assertEqual(shell_rc.read_bytes(), before)
            self.assertFalse((root / "tool").exists())
            self.assertFalse(install_manifest_path(root).exists())

    def test_installer_preflights_unowned_path_block_in_unselected_shell(self):
        with tempfile.TemporaryDirectory(
            prefix="aph installer cross shell collision "
        ) as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            selected_shell = home / ".zshrc"
            selected_shell.write_bytes(b"export KEEP_ZSH=1\n")
            collision_shell = home / ".bashrc"
            collision_shell.write_text(
                PATH_BLOCK_START
                + "\nexport USER_OWNED=1\n"
                + PATH_BLOCK_END
                + "\n",
                encoding="utf-8",
            )
            other_shell = home / ".bash_profile"
            other_shell.write_bytes(b"export KEEP_BASH_PROFILE=1\n")
            shell_bytes = {
                path: path.read_bytes()
                for path in (selected_shell, collision_shell, other_shell)
            }
            root = base / "root"

            completed = self.run_installer(home, root, REPOSITORY)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("unowned", completed.stderr.lower())
            self.assertIn(".bashrc", completed.stderr)
            self.assertNotIn("traceback", completed.stderr.lower())
            self.assertFalse(root.exists())
            self.assertFalse((root / "tool").exists())
            self.assertFalse(install_manifest_path(root).exists())
            for path, before in shell_bytes.items():
                self.assertEqual(path.read_bytes(), before)

    def test_installer_refuses_symlinked_unselected_supported_shell_files(self):
        for collision_name in (".bashrc", ".bash_profile"):
            with self.subTest(collision=collision_name), tempfile.TemporaryDirectory(
                prefix="aph installer symlinked shell collision "
            ) as directory:
                base = Path(directory)
                home = base / "home"
                home.mkdir()
                selected_shell = home / ".zshrc"
                selected_shell.write_bytes(b"export KEEP_ZSH=1\n")
                target = base / f"{collision_name[1:]} target"
                target.write_text(
                    PATH_BLOCK_START
                    + "\nexport USER_OWNED=1\n"
                    + PATH_BLOCK_END
                    + "\n",
                    encoding="utf-8",
                )
                collision_shell = home / collision_name
                collision_shell.symlink_to(target)
                other_shell = home / (
                    ".bash_profile"
                    if collision_name == ".bashrc"
                    else ".bashrc"
                )
                other_shell.write_bytes(b"export KEEP_OTHER=1\n")
                shell_bytes = {
                    path: path.read_bytes()
                    for path in (selected_shell, target, other_shell)
                }
                collision_link = os.readlink(collision_shell)
                root = base / "root"

                completed = self.run_installer(home, root, REPOSITORY)

                self.assertEqual(completed.returncode, 1)
                self.assertIn("symlink", completed.stderr.lower())
                self.assertIn(collision_name, completed.stderr)
                self.assertNotIn("traceback", completed.stderr.lower())
                self.assertFalse(root.exists())
                self.assertFalse((root / "tool").exists())
                self.assertFalse(install_manifest_path(root).exists())
                self.assertTrue(collision_shell.is_symlink())
                self.assertEqual(os.readlink(collision_shell), collision_link)
                for path, before in shell_bytes.items():
                    self.assertEqual(path.read_bytes(), before)
