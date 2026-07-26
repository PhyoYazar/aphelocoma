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
- 2026-07-26T04:10:00Z — `work_started` — Picked up T9 (progress board). Read the spec, the binding
  conventions, `hamilton_state.py`'s loaders and Git helpers, and the `aph doctor --json` contract,
  then wrote the red tests first per TDD: 26 focused cases across `tests/test_hamilton_state.py`
  (`StatusBoardTests`, `UnversionedStatusBoardTests`) and `tests/test_cli.py`
  (`CliStatusBoardTests`), all failing with `ImportError: cannot import name 'StatusError'` and
  `Unknown command 'status'`.
- 2026-07-26T04:10:00Z — `assumption_logged` — Three scope decisions recorded rather than guessed:
  (1) the board emits no ANSI at all, matching the existing colour-free CLI, so `NO_COLOR` and a
  non-TTY stdout are satisfied by construction instead of by a disable path; (2) only
  `VERSION_CODES` findings refuse the board — privacy findings such as `redact_sensitive` remain
  `aph doctor`'s business, because looking must keep working; (3) `docs/documentation-assertions-v0.3.md`
  is outside the spec's declared files, so DOC-002's command list and DOC-006's test-ID list are
  left for a technical-writer pass and flagged at handoff.
- 2026-07-26T04:10:00Z — `artifact_written` — Added `summarize_project()` plus `StatusError`,
  `TaskSummary`, `RepoSummary`, and `ProjectSummary` to `src/aphelocoma/hamilton_state.py`, reusing
  `_load_json`, `_validate_versions`, `_parse_settings`, and `_git_contexts` rather than adding a
  runtime module that would have to be registered in `lifecycle.py`, `validate.py`, and
  `migrate.py`. Commits since kickoff are counted from every reachable commit's `%cI` against
  `hamilton.json.created`, not Git's walk-stopping `--since`, and a single unreadable timestamp
  makes the count `unknown` instead of a number the board cannot stand behind. Non-Git, detached
  HEAD, and unreadable-worktree cases each degrade the repo line to a plain statement.
- 2026-07-26T04:10:00Z — `artifact_written` — Added the `status` subcommand, help topic, and
  colour-free renderer to `src/aphelocoma/cli.py` (exit `0`/`1`/`2` per conventions, artifact named
  and remediation printed on failure, `--json` following the doctor report shape). Documented the
  board in `PROTOCOL.md` §5.6 (required content, the four trigger points, the orchestrator-rendered
  fallback for version skew), pointed `skill.md`'s `status` and `resume` modes at `aph status`, and
  recorded the command in `README.md` and the unreleased 0.3.0 `CHANGELOG.md` entry. Removed the
  empty untracked leftover directory `skills/aph-status/`.
- 2026-07-26T04:10:00Z — `handoff` — T9 ready for independent CP4 review. The 26 new tests fail
  before the implementation and pass after; the full standard-library suite is 203 passing;
  `validate.py .` reports OK on 234 events / 9 tasks; `aph doctor` is healthy; and `aph status .`
  renders a real board for this repository in both human and JSON form.
- 2026-07-26T04:35:00Z — `artifact_written` — Pre-handoff review caught a wrong-claim defect: both
  Git reads inherited ambient user configuration. With `status.showUntrackedFiles=no` a repository
  full of untracked work reported "working tree clean", and `log.showSignature=true` could
  interleave verification output that turned a readable commit count into a false unknown. Pinned
  `git status --porcelain --untracked-files=normal` and `git log --no-show-signature --format=%cI`,
  matching the existing house precedent of passing explicit untracked-file flags rather than
  trusting config. Added `test_ambient_git_configuration_cannot_hide_uncommitted_work`, verified red
  against the unpinned flag and green with it. Suite now 205 passing.

- 2026-07-26T03:35:00Z — Correction to the entry above: the task added 28 new tests, not 26. The suite
  total of 205 was reported correctly. Recorded as an appended correction rather than an edit, per
  PROTOCOL §5.

- 2026-07-26T04:05:00Z — `work_started` — T11: narrow the §5.6 board to the stage and the task list,
  and keep the same board in `.aphelocoma/STATUS.md`. Read the spec, `conventions.md`, `CRAFT.md`, and
  my own T9 code before touching anything. Confirmed the deliberate reduction: the repo line, the
  blocked section, the next-actionable line, and the schema/protocol/visibility line leave the human
  view but stay in `--json`, so `RepoSummary` and `_next_actionable()` keep earning their place.
- 2026-07-26T04:15:00Z — `artifact_written` — TDD, tests first: 14 new tests (11 in
  `tests/test_hamilton_state.py`, 3 in `tests/test_cli.py`) plus 3 rewritten T9 tests, all verified
  failing before the implementation. `src/aphelocoma/hamilton_state.py` gained
  `render_status_markdown()`, `write_status_report()` (temporary file + atomic replace, `StatusError`
  with a named artifact when the write fails), `_last_ledger_seq()`, and `_validate_status_report()`
  wired into `validate_project()`. `src/aphelocoma/cli.py` narrowed `render_status_board()` to project,
  phase, done/total, and one row per task carrying its status as a word, and added `--write`; the
  confirmation goes to stderr so stdout stays exactly the board, or exactly one JSON document.
- 2026-07-26T04:15:30Z — `assumption_logged` — Three judgement calls the spec left open. (1) The task
  row drops `owner`: the acceptance criterion enumerates "id, status as a word, and title" and says
  "exactly"; `owner` stays in `--json`. (2) `--json --write` is allowed and leaves the JSON
  byte-identical — the file is written, and nothing is added to the report, because `--json` must stay
  unchanged. (3) The `/aph-hamilton status` skill command stays read-only (print, no write): the four
  §5.6 trigger points are out of scope for this task and an explicit look should not mutate a file.
- 2026-07-26T04:16:00Z — `artifact_written` — The staleness warning needed one shim line:
  `references/validate.py` printed remediation for errors but dropped it for warnings, so the human
  output could not have named `aph status --write` as the fix. It now prints warning remediation the
  same way it prints error remediation. Documented the narrowed board, the four print-and-write
  moments, `tasks.json` as authoritative on disagreement, whole-file regeneration, the stamp, and the
  warns-never-errors rule in `PROTOCOL.md` §5.6 (and §6's resume line), `skill.md`, `README.md`, and
  the unreleased 0.3.0 `CHANGELOG.md` entry. Recorded that under `visibility: local` `STATUS.md` stays
  untracked with the rest of `.aphelocoma/`, so the tracked-state privacy rule keeps holding.
- 2026-07-26T04:16:30Z — `handoff` — T11 ready for independent CP4 review. Full standard-library suite:
  219 passing (was 205). Validator on this project: 0 errors, 0 warnings when `STATUS.md` is current;
  `missing_status_report` when absent and `stale_status_report` naming the exact gap when its stamped
  `seq` is behind, both exit `0` and never an error. `aph doctor` healthy. Real runs of `aph status .`,
  `aph status . --json`, and `aph status . --write` against this repository; the written
  `.aphelocoma/STATUS.md` task list matches `state/tasks.json` row for row (11 of 11) and
  `git check-ignore` confirms it is committable.
