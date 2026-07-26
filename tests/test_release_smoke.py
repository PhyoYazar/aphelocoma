"""End-to-end v0.3 release-readiness smoke tests.

These tests intentionally cross module boundaries. Unit tests own the detailed
edge cases; this module proves the release package preserves those guarantees
when its install, deploy, state, and uninstall paths are composed.
"""

from __future__ import annotations

import copy
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

from aphelocoma import doctor
from aphelocoma.deploy import deploy_hamilton, undeploy_hamilton
from aphelocoma.doctor import DEFINITION_FILES, HAMILTON_ROLE_IDS
from aphelocoma.hamilton_state import migrate_project, validate_project
from aphelocoma.lifecycle import (
    LifecycleError,
    RELEASE_COPY_PATHS,
    activate_release,
    install_manifest_path,
    uninstall_installation,
)
from aphelocoma.manifest import digest_path, load_manifest, manifest_path
from aphelocoma.paths import resolve_paths


RELEASE_FIXTURE = (
    REPOSITORY / "tests" / "fixtures" / "release" / "readiness-matrix.json"
)
CI_WORKFLOW = REPOSITORY / ".github" / "workflows" / "ci.yml"
READINESS_REPORT = REPOSITORY / "docs" / "release-readiness-v0.3.md"
CURRENT_FIXTURE = REPOSITORY / "tests" / "fixtures" / "hamilton" / "current"
V02_FIXTURE = REPOSITORY / "tests" / "fixtures" / "hamilton" / "unversioned-v02"

REQUIRED_SCENARIOS = {
    "clean_deploy",
    "repeated_deploy",
    "repeated_undeploy",
    "collision_restore",
    "sequential_fallback",
    "interrupted_install_rollback",
    "interrupted_update_rollback",
    "ownership_aware_uninstall",
    "migration",
    "validator_order",
    "privacy_transient_and_secret",
    "generator_inventory",
    "package_inventory",
}


def _matrix_issues(matrix):
    issues = []
    expectations = (
        ("supported_os", {"ubuntu-latest", "macos-latest"}),
        ("host_tools", {"claude", "codex"}),
        ("protected_legacy_paths", {"default", "custom"}),
        ("scenarios", REQUIRED_SCENARIOS),
        ("required_hamilton_assets", set(DEFINITION_FILES)),
        ("required_role_ids", set(HAMILTON_ROLE_IDS)),
    )
    for field, expected in expectations:
        actual = set(matrix.get(field, []))
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        if missing:
            issues.append("%s missing %s" % (field, ", ".join(missing)))
        if unexpected:
            issues.append("%s has unsupported %s" % (field, ", ".join(unexpected)))
    if matrix.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    return issues


def _protected_snapshot(paths):
    snapshot = {}
    for protected in paths.protected_legacy_paths:
        if not protected.exists():
            continue
        snapshot[str(protected)] = {
            path.relative_to(protected).as_posix(): path.read_bytes()
            for path in protected.rglob("*")
            if path.is_file()
        }
    return snapshot


def _isolated_paths(base):
    home = base / "home"
    home.mkdir()
    custom = base / "custom legacy"
    paths = resolve_paths(
        {
            "HOME": str(home),
            "APHELOCOMA_ROOT": str(base / "active"),
            "APHELOCOMA_HOME": str(custom),
        },
        tool_root=REPOSITORY,
    )
    for protected, payload in (
        (paths.default_legacy_data, b"default legacy"),
        (custom, b"custom legacy"),
    ):
        protected.mkdir(parents=True)
        (protected / "sentinel.bin").write_bytes(payload)
    return paths


def _copy_release(source, destination, version):
    destination.mkdir()
    for relative in RELEASE_COPY_PATHS:
        origin = source / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if origin.is_dir():
            shutil.copytree(origin, target)
        else:
            shutil.copy2(origin, target)
    (destination / "VERSION").write_text(version + "\n", encoding="utf-8")
    return destination


def _run(*arguments, cwd=None, environment=None):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if environment:
        env.update(environment)
    return subprocess.run(
        list(map(str, arguments)),
        cwd=str(cwd or REPOSITORY),
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


class ReleaseContractTests(unittest.TestCase):
    def test_release_matrix_matches_every_required_boundary(self):
        matrix = json.loads(RELEASE_FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(_matrix_issues(matrix), [])

    def test_release_matrix_rejects_tool_os_legacy_asset_and_scenario_omissions(self):
        matrix = json.loads(RELEASE_FIXTURE.read_text(encoding="utf-8"))
        omissions = (
            ("supported_os", "ubuntu-latest"),
            ("host_tools", "claude"),
            ("protected_legacy_paths", "custom"),
            ("required_hamilton_assets", DEFINITION_FILES[0]),
            ("required_role_ids", HAMILTON_ROLE_IDS[0]),
            ("scenarios", sorted(REQUIRED_SCENARIOS)[0]),
        )
        for field, value in omissions:
            with self.subTest(field=field, value=value):
                incomplete = copy.deepcopy(matrix)
                incomplete[field].remove(value)
                self.assertTrue(
                    any(issue.startswith(field + " missing") for issue in _matrix_issues(incomplete))
                )

    def test_ci_runs_all_release_gates_on_current_ubuntu_and_macos(self):
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        for required in (
            "ubuntu-latest",
            "macos-latest",
            "python -m unittest discover -s tests -v",
            "python skills/aph-hamilton/references/validate.py .",
            "bash -n install.sh",
            "tests.test_package_inventory",
            "tests.test_release_smoke",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)

    def test_release_metadata_and_report_are_final(self):
        report = READINESS_REPORT.read_text(encoding="utf-8")

        self.assertEqual(
            (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip(),
            "0.3.0",
        )
        self.assertIn("Status: READY TO RELEASE", report)
        self.assertIn("Release version: `0.3.0`", report)

        # The report must name the actual hosted CI run that verified this
        # release (run reference, commit, and every matrix job) rather than
        # merely not saying "pending". Each literal below is evidence a
        # reader could use to go check the run themselves; removing or
        # emptying that evidence from the report must fail this test.
        # The last two literals pin the run's *outcome*, not just its
        # identity: a report could name the right run/commit/jobs and still
        # lie about what happened, so passing/success wording is asserted
        # explicitly and must fail if the report describes that run as
        # anything other than green.
        for evidence in (
            "Hosted runner execution: CI #1",
            "https://github.com/PhyoYazar/aphelocoma/actions/runs/30197582782",
            "e8d87de15ef793d4ebe02f0d86b4bf0b34cdde2c",
            "ubuntu-latest / Python 3.9",
            "ubuntu-latest / Python 3.x",
            "macos-latest / Python 3.9",
            "macos-latest / Python 3.x",
            "Result: success, all four matrix jobs",
            "success on all four matrix",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, report)

        # Guard against the claim drifting back to "pending" while some of
        # the literals above happen to still be present elsewhere. Targets
        # the claim itself ("execution: pending"), not a longer phrase that
        # a paragraph could legitimately quote historically (e.g. "What
        # remains before release" names the retired wording it replaced).
        # Checked against whitespace-normalized text (runs of spaces/
        # newlines collapsed to one space) so a markdown line wrap inserted
        # between "execution:" and "pending" can't slip the phrase past a
        # literal substring check.
        normalized_report = re.sub(r"\s+", " ", report)
        self.assertNotIn("Hosted runner execution: pending", normalized_report)


class DeploymentReleaseSmokeTests(unittest.TestCase):
    def test_both_hosts_clean_and_repeated_deploy_and_undeploy(self):
        for tool in ("claude", "codex"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory(
                prefix="aph release deploy %s " % tool
            ) as directory:
                paths = _isolated_paths(Path(directory))
                protected_before = _protected_snapshot(paths)
                host = paths.home / (".claude" if tool == "claude" else ".codex")
                host.mkdir()
                user_config = host / ("CLAUDE.md" if tool == "claude" else "config.toml")
                original = (
                    b"# user Claude instructions\n"
                    if tool == "claude"
                    else b'model = "user-choice"\n'
                )
                user_config.write_bytes(original)

                first = deploy_hamilton(paths, tool)
                second = deploy_hamilton(paths, tool)
                manifest = load_manifest(manifest_path(paths.root, tool), tool)

                self.assertTrue(first.ok)
                self.assertTrue(second.ok)
                self.assertEqual(len(manifest["artifacts"]), 28)
                skill = host / "skills" / "aph-hamilton"
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertEqual(
                    len(list((host / "agents").glob("hamilton-*"))),
                    len(HAMILTON_ROLE_IDS),
                )
                self.assertEqual(
                    {
                        path.stem.replace("hamilton-", "")
                        for path in (host / "agents").glob("hamilton-*")
                    },
                    set(HAMILTON_ROLE_IDS),
                )
                if tool == "claude":
                    self.assertEqual(user_config.read_bytes(), original)
                else:
                    self.assertIn(original.decode("utf-8"), user_config.read_text())

                first_remove = undeploy_hamilton(paths, tool)
                second_remove = undeploy_hamilton(paths, tool)

                self.assertTrue(first_remove.ok)
                self.assertTrue(second_remove.ok)
                self.assertEqual(user_config.read_bytes(), original)
                self.assertEqual(_protected_snapshot(paths), protected_before)

    def test_both_hosts_restore_collisions_without_touching_protected_paths(self):
        for tool, suffix in (("claude", ".md"), ("codex", ".toml")):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory(
                prefix="aph release collision %s " % tool
            ) as directory:
                paths = _isolated_paths(Path(directory))
                protected_before = _protected_snapshot(paths)
                host = paths.home / (".claude" if tool == "claude" else ".codex")
                agent = host / "agents" / ("hamilton-cto" + suffix)
                agent.parent.mkdir(parents=True)
                agent.write_bytes(b"user-owned cto\n")
                config = host / ("CLAUDE.md" if tool == "claude" else "config.toml")
                config.write_bytes(b"# user configuration\n")

                deploy_hamilton(paths, tool)
                manifest = load_manifest(manifest_path(paths.root, tool), tool)
                collision_targets = {record["path"] for record in manifest["collisions"]}

                self.assertIn(str(agent), collision_targets)
                self.assertTrue(undeploy_hamilton(paths, tool).ok)
                self.assertEqual(agent.read_bytes(), b"user-owned cto\n")
                self.assertEqual(config.read_bytes(), b"# user configuration\n")
                self.assertEqual(_protected_snapshot(paths), protected_before)

    def test_supported_os_policy_and_sequential_fallback_are_explicit(self):
        os_check = dict(doctor.base_registry().callbacks())["os"]
        host_check = dict(doctor.deployment_registry().callbacks())["host-tools"]
        with tempfile.TemporaryDirectory(prefix="aph release policy ") as directory:
            paths = _isolated_paths(Path(directory))
            context = doctor.DoctorContext(paths=paths, cwd=Path(directory))
            for system in ("Darwin", "Linux"):
                with self.subTest(system=system), mock.patch.object(
                    doctor.platform, "system", return_value=system
                ):
                    self.assertEqual(os_check(context).status, "ok")
            with mock.patch.object(doctor.shutil, "which", return_value=None):
                diagnostic = host_check(context)
            self.assertEqual(diagnostic.status, "ok")
            self.assertIn("sequential fallback", diagnostic.message.lower())


class LifecycleReleaseSmokeTests(unittest.TestCase):
    def test_interrupted_install_and_update_restore_the_previous_state(self):
        with tempfile.TemporaryDirectory(prefix="aph release rollback ") as directory:
            base = Path(directory)
            paths = _isolated_paths(base)
            protected_before = _protected_snapshot(paths)

            with self.assertRaisesRegex(LifecycleError, "injected"):
                activate_release(REPOSITORY, paths, fail_at="after_activate")
            self.assertFalse((paths.root / "tool").exists())
            self.assertFalse(install_manifest_path(paths.root).exists())

            activate_release(REPOSITORY, paths)
            active = paths.root / "tool"
            manifest = install_manifest_path(paths.root)
            before_digest = digest_path(active)
            before_manifest = manifest.read_bytes()
            update_source = _copy_release(REPOSITORY, base / "update", "0.3.1")

            with self.assertRaisesRegex(LifecycleError, "injected"):
                activate_release(update_source, paths, fail_at="after_activate")

            self.assertEqual(digest_path(active), before_digest)
            self.assertEqual(manifest.read_bytes(), before_manifest)
            self.assertEqual(_protected_snapshot(paths), protected_before)

    def test_ownership_aware_uninstall_restores_users_and_retains_backups(self):
        with tempfile.TemporaryDirectory(prefix="aph release uninstall ") as directory:
            paths = _isolated_paths(Path(directory))
            protected_before = _protected_snapshot(paths)
            shell_rc = paths.home / ".zshrc"
            shell_rc.write_bytes(b"export USER_SETTING=1\n")
            collisions = {}
            for tool, suffix in (("claude", ".md"), ("codex", ".toml")):
                host = paths.home / (".claude" if tool == "claude" else ".codex")
                agent = host / "agents" / ("hamilton-cto" + suffix)
                agent.parent.mkdir(parents=True, exist_ok=True)
                payload = ("%s user cto\n" % tool).encode("utf-8")
                agent.write_bytes(payload)
                collisions[agent] = payload
                if tool == "codex":
                    (host / "config.toml").write_bytes(b'model = "keep"\n')

            activate_release(REPOSITORY, paths, shell_rc=shell_rc)
            for tool in ("claude", "codex"):
                deploy_hamilton(paths, tool)

            result = uninstall_installation(paths)

            self.assertTrue(result.ok, result.messages)
            self.assertFalse((paths.root / "tool").exists())
            self.assertFalse(install_manifest_path(paths.root).exists())
            for tool in ("claude", "codex"):
                self.assertFalse(manifest_path(paths.root, tool).exists())
                self.assertTrue((paths.root / "backups" / tool).is_dir())
            for path, payload in collisions.items():
                self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(
                (paths.home / ".codex" / "config.toml").read_bytes(),
                b'model = "keep"\n',
            )
            self.assertEqual(shell_rc.read_bytes(), b"export USER_SETTING=1\n")
            self.assertEqual(_protected_snapshot(paths), protected_before)

    def test_installer_package_and_installed_version_match_the_release(self):
        with tempfile.TemporaryDirectory(prefix="aph release installer ") as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            root = base / "active"
            completed = _run(
                "bash",
                REPOSITORY / "install.sh",
                environment={
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(root),
                    "APHELOCOMA_INSTALL_SOURCE": str(REPOSITORY),
                },
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            installed = _run(
                sys.executable,
                root / "tool" / "bin" / "aph",
                "version",
                cwd=base,
                environment={"HOME": str(home), "APHELOCOMA_ROOT": str(root)},
            )
            expected = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertEqual(installed.stdout, "aph %s\n" % expected)
            self.assertEqual(
                {path.name for path in (root / "tool").iterdir()},
                {"VERSION", "install.sh", "bin", "src", "skills", "adapters"},
            )


class HamiltonStateReleaseSmokeTests(unittest.TestCase):
    def test_migration_validator_order_and_privacy_integrate(self):
        with tempfile.TemporaryDirectory(prefix="aph release state ") as directory:
            base = Path(directory)
            legacy_project = base / "legacy"
            shutil.copytree(V02_FIXTURE, legacy_project)

            check = migrate_project(legacy_project, apply=False)
            self.assertEqual(check.status, "migration_required")
            migrated = migrate_project(legacy_project, apply=True)
            self.assertEqual(migrated.status, "migrated")
            self.assertIsNotNone(migrated.backup)
            self.assertTrue(migrated.backup.is_dir())
            self.assertTrue(validate_project(legacy_project, tracked_files=[]).ok)

            ordered = base / "ordered"
            shutil.copytree(CURRENT_FIXTURE, ordered)
            events_path = ordered / ".aphelocoma" / "ledger" / "events.jsonl"
            events = [json.loads(line) for line in events_path.read_text().splitlines()]
            events[1]["seq"] = 4
            events_path.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            order_report = validate_project(ordered, tracked_files=[])
            self.assertIn(
                "invalid_event_sequence",
                {issue.code for issue in order_report.errors},
            )

            private = base / "private"
            shutil.copytree(CURRENT_FIXTURE, private)
            dispatch = private / ".aphelocoma" / "dispatch" / "T1"
            dispatch.mkdir(parents=True)
            (dispatch / "prompt.md").write_text(
                "access_token=transient-not-a-real-token\n",
                encoding="utf-8",
            )
            self.assertTrue(validate_project(private, tracked_files=[]).ok)
            private_events = private / ".aphelocoma" / "ledger" / "events.jsonl"
            durable = json.loads(private_events.read_text().splitlines()[-1])
            durable.update(
                {
                    "ts": "2026-07-24T00:00:00Z",
                    "seq": 10,
                    "event": "assumption_logged",
                    "actor": "cto",
                    "task": None,
                    "to": None,
                    "note": "credential AKIAIOSFODNN7EXAMPLE",
                }
            )
            private_events.write_text(
                private_events.read_text() + json.dumps(durable) + "\n",
                encoding="utf-8",
            )
            privacy_report = validate_project(private, tracked_files=[])
            self.assertIn(
                "secret_material",
                {issue.code for issue in privacy_report.errors},
            )

    def test_validator_is_independently_runnable_for_repo_and_fixture(self):
        validator = (
            REPOSITORY
            / "skills"
            / "aph-hamilton"
            / "references"
            / "validate.py"
        )
        for project in (REPOSITORY, CURRENT_FIXTURE):
            with self.subTest(project=project):
                completed = _run(sys.executable, validator, project)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)


class DeployedStateToolRuntimeTests(unittest.TestCase):
    def _installation(self, base, custom_root):
        home = base / "home"
        home.mkdir()
        environment = os.environ.copy()
        for name in ("APHELOCOMA_HOME", "APHELOCOMA_ROOT", "PYTHONPATH"):
            environment.pop(name, None)
        environment["HOME"] = str(home)
        if custom_root:
            environment["APHELOCOMA_ROOT"] = str(
                base / "custom active root's directory"
            )
        paths = resolve_paths(environment, tool_root=REPOSITORY)
        activate_release(REPOSITORY, paths)
        return paths, environment

    def _run_state_tool(
        self, script, arguments, caller, environment, pythonpath=""
    ):
        isolated = environment.copy()
        isolated["PYTHONPATH"] = str(pythonpath)
        return subprocess.run(
            [sys.executable, str(script), *map(str, arguments)],
            cwd=str(caller),
            env=isolated,
            check=False,
            text=True,
            capture_output=True,
        )

    def _write_shadow_runtime(self, source):
        package = source / "aphelocoma"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "hamilton_state.py").write_text(
            'raise RuntimeError("UNTRUSTED SHADOW RUNTIME EXECUTED")\n',
            encoding="utf-8",
        )

    def _write_partial_release(self, root, execution_marker=None):
        self._write_shadow_runtime(root / "src")
        if execution_marker is not None:
            (
                root / "src" / "aphelocoma" / "hamilton_state.py"
            ).write_text(
                "from pathlib import Path\n"
                f"Path({str(execution_marker)!r}).write_text('executed')\n"
                'raise RuntimeError("UNTRUSTED SHADOW RUNTIME EXECUTED")\n',
                encoding="utf-8",
            )
        (root / "VERSION").write_text("0.3.0\n", encoding="utf-8")
        (root / "install.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        binary = root / "bin" / "aph"
        binary.parent.mkdir()
        binary.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    def test_deployed_validator_and_migrator_find_default_and_custom_runtime(self):
        for custom_root in (False, True):
            with self.subTest(custom_root=custom_root), tempfile.TemporaryDirectory(
                prefix="aph deployed state tools "
            ) as directory:
                base = Path(directory)
                paths, environment = self._installation(base, custom_root)
                caller = base / "unrelated caller"
                caller.mkdir()
                current = base / "current project"
                legacy = base / "legacy project"
                global_shadow = base / "global shadow"
                shutil.copytree(CURRENT_FIXTURE, current)
                shutil.copytree(V02_FIXTURE, legacy)
                self._write_shadow_runtime(global_shadow)

                for tool in ("claude", "codex"):
                    deploy_hamilton(paths, tool)
                    host = paths.home / (
                        ".claude" if tool == "claude" else ".codex"
                    )
                    self._write_partial_release(host)
                    skill = (
                        host
                        / "skills"
                        / "aph-hamilton"
                        / "references"
                    )
                    with self.subTest(custom_root=custom_root, tool=tool):
                        validated = self._run_state_tool(
                            skill / "validate.py",
                            (current,),
                            caller,
                            environment,
                        )
                        shadowed = self._run_state_tool(
                            skill / "validate.py",
                            (current,),
                            caller,
                            environment,
                            pythonpath=global_shadow,
                        )
                        checked = self._run_state_tool(
                            skill / "migrate.py",
                            ("check", legacy),
                            caller,
                            environment,
                        )

                        self.assertEqual(
                            validated.returncode,
                            0,
                            validated.stderr + validated.stdout,
                        )
                        self.assertIn("OK", validated.stdout)
                        self.assertEqual(
                            shadowed.returncode,
                            0,
                            shadowed.stderr + shadowed.stdout,
                        )
                        self.assertIn("OK", shadowed.stdout)
                        self.assertEqual(
                            checked.returncode,
                            1,
                            checked.stderr + checked.stdout,
                        )
                        self.assertIn("migrate.py apply", checked.stdout)
                        self.assertNotIn(
                            "Traceback",
                            validated.stderr
                            + validated.stdout
                            + shadowed.stderr
                            + shadowed.stdout
                            + checked.stderr
                            + checked.stdout,
                        )

    def test_detached_state_tools_report_missing_runtime_without_traceback(self):
        with tempfile.TemporaryDirectory(
            prefix="aph detached state tools "
        ) as directory:
            base = Path(directory)
            caller = base / "caller"
            caller.mkdir()
            detached = base / "detached" / "skills" / "aph-hamilton" / "references"
            detached.mkdir(parents=True)
            execution_marker = base / "partial release executed"
            self._write_partial_release(
                base / "detached",
                execution_marker=execution_marker,
            )
            project = base / "project"
            shutil.copytree(CURRENT_FIXTURE, project)
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(base / "home"),
                    "APHELOCOMA_ROOT": str(base / "missing active root"),
                    "PYTHONPATH": "",
                }
            )

            for script_name, arguments in (
                ("validate.py", (project,)),
                ("migrate.py", ("check", project)),
            ):
                shutil.copy2(
                    REPOSITORY
                    / "skills"
                    / "aph-hamilton"
                    / "references"
                    / script_name,
                    detached / script_name,
                )
                with self.subTest(script=script_name):
                    completed = self._run_state_tool(
                        detached / script_name,
                        arguments,
                        caller,
                        environment,
                    )
                    output = completed.stderr + completed.stdout
                    self.assertEqual(completed.returncode, 2, output)
                    self.assertIn("Reinstall Aphelocoma", output)
                    self.assertIn("aph deploy", output)
                    self.assertNotIn("Traceback", output)
                    self.assertFalse(execution_marker.exists(), output)

    def test_deployed_tools_reject_corrupt_manifest_owned_runtime(self):
        with tempfile.TemporaryDirectory(
            prefix="aph corrupt installed runtime "
        ) as directory:
            base = Path(directory)
            paths, environment = self._installation(base, custom_root=True)
            caller = base / "unrelated caller"
            caller.mkdir()
            project = base / "current project"
            shutil.copytree(CURRENT_FIXTURE, project)
            deployed = []

            for tool in ("claude", "codex"):
                deploy_hamilton(paths, tool)
                host = paths.home / (
                    ".claude" if tool == "claude" else ".codex"
                )
                deployed.append(
                    host / "skills" / "aph-hamilton" / "references"
                )

            (paths.root / "tool" / "src" / "aphelocoma" / "hamilton_state.py").write_text(
                "BROKEN_RUNTIME = True\n",
                encoding="utf-8",
            )

            for skill in deployed:
                for script_name, arguments in (
                    ("validate.py", (project,)),
                    ("migrate.py", ("check", project)),
                ):
                    with self.subTest(host=skill.parents[2].name, script=script_name):
                        completed = self._run_state_tool(
                            skill / script_name,
                            arguments,
                            caller,
                            environment,
                        )
                        output = completed.stderr + completed.stdout
                        self.assertEqual(completed.returncode, 2, output)
                        self.assertIn("Reinstall Aphelocoma", output)
                        self.assertIn("aph deploy", output)
                        self.assertNotIn("Traceback", output)

    def test_source_checkout_tools_work_without_an_installation(self):
        with tempfile.TemporaryDirectory(
            prefix="aph source checkout state tools "
        ) as directory:
            base = Path(directory)
            caller = base / "unrelated caller"
            caller.mkdir()
            project = base / "current project"
            shutil.copytree(CURRENT_FIXTURE, project)
            global_shadow = base / "global shadow"
            self._write_shadow_runtime(global_shadow)
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(base / "home"),
                    "APHELOCOMA_ROOT": str(base / "missing active root"),
                    "PYTHONPATH": str(global_shadow),
                }
            )
            before = digest_path(project)

            for script_name, arguments in (
                ("validate.py", (project,)),
                ("migrate.py", ("check", project)),
            ):
                with self.subTest(script=script_name):
                    completed = self._run_state_tool(
                        REPOSITORY
                        / "skills"
                        / "aph-hamilton"
                        / "references"
                        / script_name,
                        arguments,
                        caller,
                        environment,
                    )
                    output = completed.stderr + completed.stdout
                    self.assertEqual(completed.returncode, 0, output)
                    self.assertNotIn("UNTRUSTED SHADOW", output)
                    self.assertNotIn("Traceback", output)

            self.assertEqual(digest_path(project), before)


if __name__ == "__main__":
    unittest.main()
