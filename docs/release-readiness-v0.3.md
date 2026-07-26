# Aphelocoma v0.3 release readiness

Status: READY FOR CI — NOT YET READY TO RELEASE

Release version: `0.3.0`

Assessment date: 2026-07-26 — a refresh of the 2026-07-24 T6 assessment below. T7–T14 shipped in
between (see "What changed since T6").

## Decision

**CI has never run on this code.** Every result in this document was produced locally, once, on macOS
with Python `3.14.4`. That is real evidence the code, its tests, and its packaging are internally
consistent — it is not evidence for Linux, and it is not evidence for the Python `3.9` floor this
project advertises. Neither has been exercised anywhere, on this machine or any other.

- **Verified:** macOS (Darwin), Python `3.14.4`, locally, as recorded below.
- **Pending, named explicitly:** Linux (the `ubuntu-latest` CI runner) and Python `3.9` (the advertised
  minimum). Both remain untested until the GitHub Actions matrix runs once.

Do not tag or publish `v0.3.0` until the hosted CI matrix — `ubuntu-latest` and `macos-latest`, each on
Python `3.9` and `3.x` — has run once and is green on all four legs. `docs/release-v0.3.0.md` carries
the exact push/CI/tag/publish sequence, including the second pass on this document once that happens.

## What changed since the T6 assessment

This document last spoke for the repository at T6 (2026-07-24), before T7–T14. Since then:

- **T7** made the deployed CLI locate the installed runtime correctly instead of assuming a checkout
  layout.
- **T8** migrated real, previously-unversioned v0.2 Hamilton project state through the explicit
  `migrate.py check`/`apply` flow, with a persistent backup.
- **T9–T14** added the Hamilton progress board: `aph status [path] [--json] [--write]`, and
  `.aphelocoma/STATUS.md` — the same board regenerated whole, atomically, and stamped with a UTC time
  and ledger `seq` at each of the four board moments. The Hamilton validator warns, and never errors,
  when `STATUS.md` is missing or behind the ledger, so a stale board never blocks `resume`.

None of this was assessed by the original T6 pass below. The current local verification section
covers the repository as it stands now, including all of it.

## Environment

Re-verified today, 2026-07-26:

- Local OS: Darwin
- Python: `3.14.4`
- Bash: GNU Bash `3.2.57(1)-release`
- Git: `2.48.1`
- Claude Code: `2.1.220`
- Codex: `0.145.0`

The installed Claude Code and Codex both meet the v0.3 minimum-version policy (Claude Code `2.1.0`,
Codex `0.145.0`); Claude Code here is newer than the last version this project explicitly tested
(`2.1.217`), which `aph doctor` treats as healthy since only the floor is enforced. Python `3.9` is not
installed on this machine — it has not been exercised locally at all. It is a separate CI matrix entry,
on both supported hosted operating systems, that has not yet run.

## Current local verification (2026-07-26)

All of the following were run just now, against the repository as it stands after T7–T14, on macOS
with Python `3.14.4`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -q
```

Result: PASS — 226 tests.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_cli tests.test_deploy tests.test_doctor tests.test_generators \
  tests.test_hamilton_state tests.test_legacy tests.test_lifecycle \
  tests.test_package_inventory tests.test_paths
```

Result: PASS — 210 tests (up from 156 at T6; the growth is almost entirely the T7–T14 progress-board
and staleness coverage in `test_hamilton_state` and `test_cli`).

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_release_smoke.ReleaseContractTests.test_release_matrix_matches_every_required_boundary \
  tests.test_release_smoke.ReleaseContractTests.test_release_matrix_rejects_tool_os_legacy_asset_and_scenario_omissions \
  tests.test_release_smoke.ReleaseContractTests.test_ci_runs_all_release_gates_on_current_ubuntu_and_macos \
  tests.test_release_smoke.DeploymentReleaseSmokeTests \
  tests.test_release_smoke.LifecycleReleaseSmokeTests \
  tests.test_release_smoke.HamiltonStateReleaseSmokeTests
```

Result: PASS — 11 tests, unchanged from T6.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_package_inventory
```

Result: PASS — 8 tests, unchanged from T6.

```bash
bash -n install.sh
python3 skills/aph-hamilton/references/validate.py .
git diff --check
```

Results:

- PASS — Bash accepted `install.sh` (the v0.3 transactional installer; its behavior is unchanged by
  this task).
- The Hamilton validator against this repository's own `.aphelocoma/` project state reported 0 errors
  and one non-blocking warning: `STATUS.md` was a few ledger events behind at the moment of this run —
  exactly the "warn, never block" staleness behavior T9–T14 built and tested, not a defect.
- PASS — no whitespace errors.

```bash
python3 bin/aph doctor
```

Result: `Aphelocoma doctor: healthy` — installation, both deployments, host tool versions, Hamilton
project state, and privacy all reported `[ok]` on this machine.

None of the above touched a Linux runner or Python `3.9`. That gap is exactly what CI is for.

## T6 audit record (2026-07-24, historical)

This is the original pre-bump/post-bump evidence gathered when `VERSION` was still being changed from
`0.2.0` to `0.3.0`. It predates T7–T14 and is preserved as a historical record of that specific
version-bump gate, not as current evidence — see "Current local verification" above for the repository
as it stands today.

### Test-first evidence

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

### Pre-bump local results

Release integration matrix: PASS — 11 tests in 3.054 seconds. This matrix exercised Claude and Codex
clean deployment, repeated deployment, repeated undeployment, collision restore, 27-role generator
inventories, sequential fallback, Darwin/Linux support policy, interrupted clean install, interrupted
update rollback, ownership-aware uninstall, default/custom legacy sentinels, v0.2 Hamilton migration,
validator ordering, durable-secret rejection, transient dispatch handling, package allowlisting, and
installed CLI version reporting.

Complete T1–T5 regression suite (`test_cli`, `test_deploy`, `test_doctor`, `test_generators`,
`test_hamilton_state`, `test_legacy`, `test_lifecycle`, `test_package_inventory`, `test_paths`): PASS —
156 tests in 20.011 seconds.

Validator, Bash, inventory, and patch checks (`bash -n install.sh`,
`python3 skills/aph-hamilton/references/validate.py .`, `test_package_inventory`, `git diff --check`):
all PASS — the validator reported 158 events, 6 tasks, 5 done, 0 errors, 0 warnings; 8 package-inventory
tests in 0.304 seconds; no whitespace errors.

### Final version gate

After the pre-bump evidence was written, `VERSION` changed from `0.2.0` to `0.3.0`. The release
integration command above was rerun against `0.3.0`: PASS — 11 tests in 3.299 seconds. The complete
T1–T5 regression command was rerun against `0.3.0`: PASS — 156 tests in 15.804 seconds. The checked-out
CLI and the isolated installer smoke both reported `aph 0.3.0`. The final CI-equivalent discovery run,
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`, was PASS — 168 tests in 18.018
seconds, including all release metadata assertions.

## CI inspection

`.github/workflows/ci.yml` configures four hosted combinations:

- `ubuntu-latest` with Python `3.9`;
- `ubuntu-latest` with the current available Python 3;
- `macos-latest` with Python `3.9`;
- `macos-latest` with the current available Python 3.

Every combination runs the full standard-library suite, the independent Hamilton validator, Bash
syntax validation, package/release inventory tests, and an isolated installed-version smoke test. The
workflow uses read-only repository permissions and does not publish artifacts or releases.

Hosted runner execution: pending first CI run

The workflow was inspected and its contract was exercised locally; GitHub-hosted Ubuntu and macOS
runners cannot be executed from this local task. All 23 commits that make up v0.3 are local — the last
push to `origin/develop` predates this work — so the workflow itself has never actually run on any
host. Publication must remain blocked until the first hosted matrix run passes on all four legs.

## What remains before release

1. Push `develop` and let the hosted CI matrix run for the first time.
2. If any leg is red, fix it there — do not weaken or skip that leg's checks to get green.
3. Once CI is green on all four legs, give this document its second pass: replace "pending first CI
   run" with the actual result, and only then can the status line honestly read as fully ready.
4. Merge, tag, and publish following `docs/release-v0.3.0.md`.
