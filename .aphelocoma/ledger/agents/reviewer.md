# Reviewer ledger

- 2026-07-23T07:46:24Z — CP1 critique found missing decisions around deployment ownership, Hamilton
  privacy, platform support, state compatibility, existing users, first-run UX, and test coverage.
  Leadership incorporated each finding into the selected direction and roadmap.
- 2026-07-23T08:01:00Z — CP2 critique failed the initial roadmap on dirty-worktree ownership,
  overlapping Codex responsibilities, incomplete lifecycle rollback, late test sequencing, incomplete
  doctor/support verification, and unprotected custom legacy data. Returned it for one bounce-back.
- 2026-07-23T08:07:00Z — Re-reviewed the revised CP2 roadmap after the bounce-back and returned PASS:
  all findings were addressed, contracts are dependency-safe, and no blocking contradiction remains.
- 2026-07-23T09:05:00Z — T1 CP4 failed because base doctor accepted a one-role partial Hamilton
  installation as complete.
- 2026-07-23T09:12:00Z — T2 CP4 failed on unenforced state/schema semantics, incomplete lifecycle
  reconciliation, trackable migration backups, contradictory result-schema outcomes, version and
  conventions regressions, and one declared-scope miss.
- 2026-07-23T09:25:00Z — Fresh T1 CP4 re-review passed after the exact 18-reference/27-role inventory
  and partial-install regression closed the blocker.
- 2026-07-23T10:40:00Z — T2 closure CP4 failed because malformed nested Git metadata can leave a
  repository-visible migration backup after rollback, and split-index support was not covered by an
  automated regression.
- 2026-07-23T11:05:00Z — Fresh T2 acceptance review failed three Git-boundary cases: fake gitdirs,
  symlink-escaped backup roots, and outer-repository tracking hidden by a nested repository.
- 2026-07-23T11:30:00Z — T2 re-review found one remaining rollback escape: an internal
  `.aphelocoma` symlink can route staged migration writes into external state.
- 2026-07-23T11:51:00Z — Final scoped T2 review found a protocol/replay mismatch: `review_failed`
  documented an optional direct `in_progress` state although the event model deterministically
  returns to `assigned` until `work_started`.
- 2026-07-23T12:05:00Z — Fresh T2 CP4 sign-off passed with all 85 tests and every prior
  schema, lifecycle, privacy, Git-boundary, migration, rollback, and protocol blocker closed.
- 2026-07-23T12:38:00Z — T3 CP4 failed five adversarial ownership cases: symlink path escapes,
  drifted-tool update replacement, unremovable exact legacy skills, arbitrary manifest block markers,
  and unverified collision backups.
- 2026-07-23T13:08:00Z — T3 re-review found three legacy gaps: nested protected data could be removed
  with an owned parent, the tagged v0.2 Codex hooks signature was missing, and doctor did not report
  the exact v0.2 PATH line.
- 2026-07-23T13:31:00Z — Final T3 review found first-run managed-block collisions could overwrite
  and later remove unowned Codex or PATH content that reused Aphelocoma's canonical markers.
- 2026-07-23T13:53:00Z — Restarted T3 sign-off found clean install scanned only its selected shell
  rc, allowing an unowned canonical PATH block in another supported shell file.
- 2026-07-23T14:13:00Z — T3 cross-shell sign-off found preflight skipped symlinked unselected
  `.bashrc`/`.bash_profile` candidates and allowed clean installation.
- 2026-07-23T14:28:00Z — Fresh T3 CP4 sign-off passed with all 147 tests and every lifecycle,
  ownership, rollback, legacy, manifest, backup, generator, and cross-shell blocker closed.
- 2026-07-23T14:56:00Z — T4 CP4 failed because root `CLAUDE.md` still activated the retired
  context/Cursor product, the Hamilton skill shipped a stale internal handoff, and package inventory
  did not cover either.
- 2026-07-23T15:17:00Z — T4 re-review found the lifecycle copier still installed the whole checkout,
  including retired brainstorms, historical docs, legacy fixtures, and root tool helpers.
- 2026-07-23T15:35:00Z — Fresh T4 CP4 sign-off passed with all 156 tests and the source plus
  activated installed package verified Hamilton-only.
- 2026-07-24T06:18:00Z — T5 CP4 found accurate prose but an incomplete mandatory evidence map for
  exit codes, install/upgrade rollback, and protocol-backed commit/branch/push behavior.
- 2026-07-24T06:35:00Z — T5 re-review found DOC-038 cited an existing schema test under the wrong
  unittest class name, invalidating the claimed citation audit.
- 2026-07-24T06:50:00Z — Fresh T5 CP4 sign-off passed with all 82 cited tests resolving and passing,
  plus a clean 156-test suite, validator, claim/policy/link/date audit, and retired-feature scan.
- 2026-07-24T07:05:00Z — Fresh T6 CP4 sign-off passed every T1–T6 acceptance criterion with 168 full
  and 20 focused tests, validator, actionlint, Bash syntax, diff, chronology, package/privacy, and
  non-publishing CI audits clean; hosted CI remains explicitly pending.
- 2026-07-24T07:05:00Z — A separate strict whole-reset release audit also returned PASS with no
  blocking findings across Hamilton-only scope, transactional lifecycle, protected legacy data,
  versioned/private state, supported hosts, release evidence, branch, tag, and worktree boundaries.
- 2026-07-24T09:30:00Z — T7 CP4 failed because standalone state tools preferred any global package
  or unowned host-adjacent `~/.claude/src` / `~/.codex/src` over the configured installation, allowing
  stale or shadow code to replace the matching runtime and potentially traceback in migration.
- 2026-07-24T09:40:00Z — T7 closure review failed because runtime discovery did not verify the
  install manifest's `tool_digest`, allowing an importable but incompatible installed module to
  traceback, and its four-file release check allowed a partial host-adjacent pseudo-release to
  outrank the healthy configured installation.
- 2026-07-24T09:50:00Z — Fresh T7 closure review passed with no findings after 4 focused and 172
  full tests plus exact digest, full runtime inventory, install precedence, required-API,
  source/default/custom root, both-host, read-only migration, validator, Bash, actionlint, diff, and
  Python 3.9 checks.
