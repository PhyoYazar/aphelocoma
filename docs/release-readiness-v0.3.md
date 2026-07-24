# Aphelocoma v0.3 release readiness

Status: READY

Release version: `0.3.0`

Assessment date: 2026-07-24

## Decision

All locally executable functional, safety, package, state-integrity, and installed-version gates
passed. The version changed only after the pre-bump results below were recorded. No tag, release,
push, or publication was performed.

## Environment

- Local OS: Darwin
- Python: `3.14.4`
- Bash: GNU Bash `3.2.57(1)-release`
- Git: `2.48.1`
- Claude Code: `2.1.217`
- Codex: `0.145.0`

The installed Claude Code and Codex versions match the v0.3 tested-version policy. Python 3.9 was not
installed locally; Python 3.9 and the current available Python 3 are configured as separate CI matrix
entries on both supported hosted operating systems.

## Test-first evidence

The first release-smoke run was:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_release_smoke
```

Result: expected RED, 12 tests run with 5 errors. The missing readiness matrix, CI workflow, and
readiness report/version gate were detected before those artifacts were added. The same run exposed
one test-only assertion that read sequential-fallback text from the remediation field instead of the
diagnostic message; that assertion was corrected before the green run.

The fixture omission test then proved that removing any representative required tool, OS, protected
legacy path, Hamilton definition asset, role, or release scenario makes the release contract fail.

## Pre-bump local results

### Release integration matrix

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_release_smoke.ReleaseContractTests.test_release_matrix_matches_every_required_boundary \
  tests.test_release_smoke.ReleaseContractTests.test_release_matrix_rejects_tool_os_legacy_asset_and_scenario_omissions \
  tests.test_release_smoke.ReleaseContractTests.test_ci_runs_all_release_gates_on_current_ubuntu_and_macos \
  tests.test_release_smoke.DeploymentReleaseSmokeTests \
  tests.test_release_smoke.LifecycleReleaseSmokeTests \
  tests.test_release_smoke.HamiltonStateReleaseSmokeTests
```

Result: PASS — 11 tests in 3.054 seconds.

This matrix exercised Claude and Codex clean deployment, repeated deployment, repeated undeployment,
collision restore, 27-role generator inventories, sequential fallback, Darwin/Linux support policy,
interrupted clean install, interrupted update rollback, ownership-aware uninstall, default/custom
legacy sentinels, v0.2 Hamilton migration, validator ordering, durable-secret rejection, transient
dispatch handling, package allowlisting, and installed CLI version reporting.

### Complete T1–T5 regression suite

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_cli \
  tests.test_deploy \
  tests.test_doctor \
  tests.test_generators \
  tests.test_hamilton_state \
  tests.test_legacy \
  tests.test_lifecycle \
  tests.test_package_inventory \
  tests.test_paths
```

Result: PASS — 156 tests in 20.011 seconds.

### Validator, Bash, inventory, and patch checks

```bash
bash -n install.sh
python3 skills/aph-hamilton/references/validate.py .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_package_inventory
git diff --check
```

Results:

- PASS — Bash accepted `install.sh`.
- PASS — validator reported 158 events, 6 tasks, 5 done, 0 errors, 0 warnings.
- PASS — 8 package-inventory tests in 0.304 seconds.
- PASS — no whitespace errors.

## CI inspection

`.github/workflows/ci.yml` configures four hosted combinations:

- `ubuntu-latest` with Python `3.9`;
- `ubuntu-latest` with the current available Python 3;
- `macos-latest` with Python `3.9`;
- `macos-latest` with the current available Python 3.

Every combination runs the full standard-library suite, the independent Hamilton validator, Bash
syntax validation, package/release inventory tests, and an isolated installed-version smoke test.
The workflow uses read-only repository permissions and does not publish artifacts or releases.

Hosted runner execution: pending first CI run

The workflow was inspected and its contract was exercised locally; GitHub-hosted Ubuntu and macOS
runners cannot be executed from this local task. Publication should remain blocked until the first
hosted matrix run passes.

## Final version gate

After the pre-bump evidence was written, `VERSION` changed from `0.2.0` to `0.3.0`.

The release integration command above was rerun against `0.3.0`.

Result: PASS — 11 tests in 3.299 seconds.

The complete T1–T5 regression command above was rerun against `0.3.0`.

Result: PASS — 156 tests in 15.804 seconds.

The checked-out CLI and the isolated installer smoke both reported the release version:

```text
aph 0.3.0
```

The final CI-equivalent discovery run was:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Result: PASS — 168 tests in 18.018 seconds, including all release metadata assertions.
