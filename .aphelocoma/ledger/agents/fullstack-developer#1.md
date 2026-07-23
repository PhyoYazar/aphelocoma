# Full-stack Developer #1 Ledger

- 2026-07-23T08:03:00Z — `role_activated` — Activated for T1 with ownership limited to the CLI
  package, executable, T1 tests, and this ledger.
- 2026-07-23T08:04:00Z — `work_started` — Added subprocess and unit regressions first; the red run
  failed against the Bash CLI and absent Python package as expected.
- 2026-07-23T08:06:00Z — `artifact_written` — Replaced `bin/aph` with a thin Python entrypoint and
  added standard-library path, atomic I/O, doctor registry, CLI, and test modules.
- 2026-07-23T08:06:35Z — `task_completed` — T1 verification passed: 24 unittest cases, package
  compilation, direct executable smoke, isolated-home smoke, and ANSI-free output check.
- 2026-07-23T08:19:04Z — `artifact_written` — Made each T1 test module bootstrap the repository
  `src/` layout so top-level unittest discovery does not depend on package import order or PYTHONPATH.
- 2026-07-23T08:19:04Z — `task_completed` — Exact combined discovery command passed all 49 T1+T2
  tests with `PYTHONDONTWRITEBYTECODE=1`.
- 2026-07-23T08:28:23Z — `work_started` — Added and ran a failing CP4 regression proving a partial
  Hamilton definition with one role was incorrectly accepted.
- 2026-07-23T08:28:23Z — `artifact_written` — Replaced the loose definition probe with an exact
  inventory of 18 shipped reference files and all 27 canonical role files; missing paths are reported
  individually with reinstall remediation.
- 2026-07-23T08:28:23Z — `task_completed` — Exact full discovery passed 50 tests; inventory audit
  confirmed required and shipped references/roles match with no gaps.
