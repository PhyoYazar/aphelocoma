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
