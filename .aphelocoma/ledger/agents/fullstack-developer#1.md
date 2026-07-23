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
- 2026-07-23T10:09:09Z — `role_activated` — Activated for T3 with ownership limited to lifecycle,
  deployment, legacy cleanup, doctor integration, Hamilton generators, scoped tests, and this ledger.
- 2026-07-23T10:09:09Z — `work_started` — Added and ran failing lifecycle, deployment, manifest,
  managed-block, legacy-path, and partial-generator regressions before implementing their fixes.
- 2026-07-23T10:09:09Z — `artifact_written` — Implemented transactional install/update/rollback,
  ownership-aware uninstall and PATH handling, manifest-backed Claude/Codex deployment, exact/proven
  legacy cleanup, all 27 generated roles, and deployment/host/legacy doctor checks.
- 2026-07-23T10:09:09Z — `task_completed` — T3 verification passed all 122 unittest cases, Bash
  syntax and diff checks, and an installed-binary smoke covering repeat deploy/undeploy, healthy
  doctor JSON, uninstall, user-config preservation, and default/custom legacy-data preservation.
- 2026-07-23T10:34:25Z — `work_started` — Resumed T3 after CP4 with failing adversarial regressions
  for host/root/backup symlinks, active-tool drift, legacy skill trees, managed-block markers, and
  collision-backup schema and digest tampering.
- 2026-07-23T10:34:25Z — `assumption_logged` — Because pre-v0.3 skills were AI-generated rather than
  produced by one deterministic script, proof uses exact tree inventory, embedded body/support
  digests, and strictly validated known Claude/Codex frontmatter variants; T4 can remove source skills
  without weakening cleanup proof.
- 2026-07-23T10:34:25Z — `artifact_written` — Added resolved containment and symlink preflights,
  active-install/PATH doctor ownership checks, activation-time proven legacy cleanup, canonical
  complete/partial manifests, and schema/digest/coherence validation for collision backups.
- 2026-07-23T10:34:25Z — `task_completed` — T3 CP4 verification passed all 134 unittest cases,
  installer Bash and diff checks, the 101-event Hamilton validator, and a fresh installed-binary
  lifecycle smoke with exact/modified legacy variants, collisions, repeat deploy/undeploy, and
  protected-data preservation.
- 2026-07-23T10:49:37Z — `work_started` — Resumed T3 after re-review with failing regressions for
  reverse protected-data containment, the released v0.2.0 Codex hooks signature, and exact legacy
  PATH-stanza doctor detection and cleanup.
- 2026-07-23T10:49:37Z — `artifact_written` — Scoped bidirectional containment checks to every
  lifecycle, deployment, backup, and legacy-cleanup mutation target while preserving the normal
  default-root layout; accepted the released hooks digest and added exact PATH-stanza reporting.
- 2026-07-23T10:49:37Z — `task_completed` — T3 re-review verification passed all 140 unittest
  cases, installer Bash and scoped diff checks, the 106-event Hamilton validator, and a fresh
  installed-binary lifecycle smoke with repeat deployment and protected default data preservation.
- 2026-07-23T12:03:46Z — `work_started` — Resumed T3 after final re-review with failing regressions
  proving no-manifest canonical Codex and shell PATH blocks were overwritten without ownership proof.
- 2026-07-23T12:03:46Z — `artifact_written` — Added pre-mutation refusal and doctor reporting for
  unowned or ambiguous canonical managed blocks, preserved manifest-owned repeated deploy/update,
  and made expected installer lifecycle refusals exit cleanly without a traceback.
- 2026-07-23T12:03:46Z — `task_completed` — Final T3 verification passed all 144 unittest cases,
  installer Bash and scoped diff checks, the 111-event Hamilton validator, and an installed-binary
  collision smoke proving byte preservation before a healthy repeated owned lifecycle.
- 2026-07-23T12:13:39Z — `work_started` — Resumed T3 for the final cross-shell PATH collision
  closure with red regressions proving a clean selected `.zshrc` did not prevent an unowned canonical
  marker in `.bashrc` or `.bash_profile` from being overwritten during activation.
- 2026-07-23T12:13:39Z — `artifact_written` — Preflighted every supported shell file before any
  lifecycle mutation while excluding only the manifest-owned marker path, preserving repeat updates
  and existing exact legacy PATH cleanup behavior.
- 2026-07-23T12:13:39Z — `task_completed` — T3 cross-shell closure passed all 146 unittest cases,
  the isolated real-installer `.bashrc` collision smoke, Bash syntax and diff checks, and the
  116-event Hamilton validator.
- 2026-07-23T12:19:48Z — `work_started` — Resumed T3 after sign-off exposed supported-shell
  symlinks as a cross-shell preflight bypass; red real-installer regressions covered unselected
  `.bashrc` and `.bash_profile` links whose targets contained canonical Aphelocoma markers.
- 2026-07-23T12:19:48Z — `artifact_written` — Refused every unowned supported-shell symlink before
  lifecycle mutation, while retaining the exact manifest-owned exclusion used by validated repeated
  updates and preserving the symlink and drift protections on selected and owned marker paths.
- 2026-07-23T12:19:48Z — `task_completed` — T3 symlink-bypass closure passed all 147 unittest cases,
  the isolated real-installer symlink collision smoke for both shell variants, Bash syntax and diff
  checks, and the 121-event Hamilton validator.
