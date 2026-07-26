# technical-writer

- 2026-07-24T07:56:53+07:00 — role_activated — Activated as T5 technical writer for the
  Hamilton-only v0.3 public documentation.
- 2026-07-24T07:56:53+07:00 — work_started — Read the T5 contract, project conventions, CLI,
  lifecycle, deployment, doctor, privacy, migration, and regression tests; wrote the behavioral
  assertion checklist before revising public prose.
- 2026-07-24T07:56:53+07:00 — artifact_written — Rewrote README.md and ABOUT.md; added CHANGELOG.md,
  docs/migration-v0.3.md, and docs/documentation-assertions-v0.3.md with test- or policy-backed claims.
- 2026-07-24T07:56:53+07:00 — handoff — Full 156-test suite and Hamilton validator passed; CLI help,
  doctor JSON, documentation links, cited test IDs, retired-claim grep, and diff whitespace were
  audited for independent T5 review.
- 2026-07-24T08:24:00+07:00 — work_started — Audited every published v0.3 behavioral claim after
  the T5 review identified missing evidence for exit statuses, installer rollback, and Git workflow
  boundaries.
- 2026-07-24T08:24:00+07:00 — artifact_written — Added exact automated-test and support-policy
  mappings for CLI exits, clean-install and upgrade rollback, Hamilton command/state semantics,
  migration/privacy fail-closed behavior, lifecycle/result contracts, and PROTOCOL §5.5 commit rules;
  corrected the verification date.
- 2026-07-24T08:24:00+07:00 — handoff — Evidence-map closure is ready for independent T5 re-review
  after cited-ID, link, retired-claim, full-suite, validator, and diff checks.
- 2026-07-24T13:22:00+07:00 — work_started — Corrected the DOC-038 test attribution after the
  prior text-based audit matched a class and method independently within one module.
- 2026-07-24T13:22:00+07:00 — artifact_written — Replaced the incorrect ValidationVersionTests
  citation with the exact MechanicalStateSchemaTests unittest ID and changed verification to invoke
  every cited fully qualified test.
- 2026-07-24T13:22:00+07:00 — handoff — Exact citation closure is ready for independent review
  after per-ID invocation, the full suite, validator, link, retired-claim, Bash, and diff checks.
- 2026-07-26T05:17:00+00:00 — work_started — T10: closed the T9/T11/T12 documentation drift three
  reviews found. Read `skill.md`, `PROTOCOL.md` §2 Phase 5/§5.5/§5.6, `README.md`, and
  `docs/documentation-assertions-v0.3.md` against `hamilton_state.py`'s ordered-lifecycle validator
  and `_validate_status_report`, and ran `aph status`/the validator to ground every changed claim.
- 2026-07-26T05:17:00+00:00 — artifact_written — `skill.md`: fixed the `resume` section's
  write-after-commit board wording to match §5.6 (regenerate after `task_completed`, before that
  task's commit; `blocked`/`review_failed` carry no commit). `PROTOCOL.md`: added the missing
  `task_completed` + board-regenerate step to §2 Phase 5 (the same defect as skill.md, one level up —
  Phase 5 previously jumped straight from `review_passed` to commit); tightened §5.6 trigger 1 to name
  the ordering explicitly; resolved the §5.5/§5.6 SHA contradiction by dropping the impossible
  "record the commit SHA in `review_passed`" instruction — no event a task needs to reach `done` is
  ever written after that task's commit exists, so none can carry its SHA — and codified the
  orchestrator's actual practice instead: the `hamilton(<task-id>): ...` subject is the two-way
  cross-reference. `README.md`: expanded the staleness paragraph to name all six validator conditions
  (missing, unreadable, unstamped, stamp naming no seq, behind, ahead) and to state plainly that every
  one is a warning that never blocks resume. `docs/documentation-assertions-v0.3.md`: added `status`
  to DOC-002's command list; added the missing status-command test IDs and named `status` in DOC-006's
  exit-code prose; fixed DOC-007's `SKILL.md`→`skill.md` casing and its now-ambiguous
  "validates and reports without writing" line; added DOC-040 for the progress board / `STATUS.md`
  (new — T9/T11/T12 shipped the feature but never indexed it here), citing every test that proves a
  staleness clause and explicitly flagging the one clause — an unreadable-but-present `STATUS.md` —
  that the code implements but no test exercises, rather than citing a test that doesn't prove it;
  extended DOC-037 to state the same SHA resolution; bumped the header to 2026-07-26 / 225 tests /
  "validator run against the repository bundle".
- 2026-07-26T05:17:00+00:00 — handoff — Full sweep of `docs/documentation-assertions-v0.3.md`: all 105
  unique cited test IDs (87 before this task, 105 after) verified to exist via `unittest discover -s
  tests -t .` output — none missing, none typo'd. Read the full cited test body for every T9/T11/T12-
  touched item (DOC-002, 006, 007, 008, 017, 030, 037, 038) plus the new DOC-040; spot-verified
  DOC-001 (27 role files on disk match the generator test), DOC-004/005/009 (installer tests), and
  DOC-035 (doctor.py's `2.1.217`/`0.145.0` constants match). Every other item was name-verified only
  (test ID exists and its title matches the claim) — not individually re-read. Found and reported, not
  fixed (non-scope: code is right, or the gap is a missing test, not wrong docs): (1) `task_completed`
  is gated by `hamilton_state.py` to require `state == "done"` already, so it can only be logged after
  `review_passed` — but several implementer role files (e.g. `fullstack-developer.md`,
  `backend-developer.md`) list `task_completed` in the *builder's own* Ledger rule, which reads as if
  the builder logs it at handoff/in_review, before any review has run; role files are outside this
  task's file scope. (2) `_validate_status_report`'s `unreadable_status_report` branch (STATUS.md
  exists but fails to read) has no covering test — flagged inline in DOC-040 rather than cited as
  tested. (3) The repo-bundle validator run (`APHELOCOMA_ROOT` pointed at a nonexistent directory)
  reports one pre-existing `stale_status_report` warning — `STATUS.md` is 1 event behind the ledger's
  seq 268 — from the orchestrator's own uncommitted T10 dispatch events already in the working tree
  before this turn started; left untouched per the hard rule against regenerating `STATUS.md`.
  Verified: `python3 -m unittest discover -s tests -t .` (225 passed), `aph doctor` (healthy),
  `APHELOCOMA_ROOT=<nonexistent> python3 skills/aph-hamilton/references/validate.py .` (0 errors, the
  1 pre-existing warning above) against the repository bundle. Ready for qa-engineer review.
- 2026-07-26T06:38:07Z — work_started — T13: closed the seven residual imprecisions the T10 review
  passed but flagged. Read `hamilton_state.py`'s ordered-lifecycle validator directly (line ~1592:
  `task_completed` is rejected with `invalid_transition` unless `state == "done"` already, so it
  follows `done`, gated only by `critique` + `review_passed`) and `write_status_report`/
  `_last_ledger_seq` (writer and `_validate_status_report` share one reader). Checked the SHA claim
  against this project's own ledger: `grep`/`git log -S` on `.aphelocoma/ledger/events.jsonl` found ten
  `task_completed` notes (T1–T9, T11) and one advisor `decision` (seq 245) naming a commit SHA, and
  `git log -S` proved each was appended in a commit *after* the SHA'd commit already existed (e.g. T9's
  `task_completed`, seq 241, naming `32500ec`, was added in the later commit `fdff9ae`, not `32500ec`
  itself) — while T12 and T10's own `task_completed` notes (post-T12's fix) name no SHA at all, since
  logging before the commit exists is exactly when a SHA can't be known.
- 2026-07-26T06:38:07Z — artifact_written — `PROTOCOL.md`: §2 Phase 5's `review_failed` branch now
  refreshes the progress board (§5.6), matching the pass branch and §5.6 trigger 3. §5.5's commit-point
  bullet now sequences `critique` → `review_passed` → `task_completed` → board → commit explicitly,
  states the gate to `done` is `critique` + `review_passed` (§8) with `task_completed` following it
  rather than producing it, and narrows the SHA claim to "no event a task needs before its own commit —
  critique, review_passed, or task_completed — can carry that commit's SHA," noting a later event may
  legitimately name it once the commit exists (matches the ledger evidence above). §5.6's bold paragraph
  no longer restates the ordering (that stays stated once, in trigger 1, above it); retitled
  "Why the board rides in the task's commit" and left holding only the rationale. `README.md` and
  `ABOUT.md`: added `STATUS.md` to both `.aphelocoma/` trees and marked README's non-exhaustive
  (dispatch/ omitted); ABOUT.md now names `aph status`/`aph status --write` and calls `STATUS.md` a
  derived view where it describes the two durable records. `docs/documentation-assertions-v0.3.md`:
  DOC-037 carries the same narrowed SHA claim as §5.5, byte-identical §5.5 heading citation preserved.
  13 implementer role files (automation-test-engineer, backend-developer, cloud-engineer, data-engineer,
  data-scientist, dba, devops-engineer, frontend-developer, fullstack-developer, ml-engineer,
  mobile-developer, sre, technical-writer): dropped `task_completed` from each "Log these events" line
  and added a pointer bullet ("`task_completed` is the orchestrator's own event... a builder does not
  log it") citing PROTOCOL §2 Phase 5 / §8 instead of restating the board/commit ordering in 13 places.
- 2026-07-26T06:38:07Z — handoff — Per-document ordering check (acceptance criterion 8), read cold
  after editing: **skill.md** (verify-only, not edited) — lines 118–122 already state the precise order
  (board after `task_completed`, before the commit) and separately name `blocked`/`review_failed` as
  no-commit refreshes; consistent with the fixed PROTOCOL, no edit needed. **PROTOCOL §2 Phase 5** — a
  reader following only this step now sees both branches name the board (write+commit on pass, refresh
  on fail), symmetric with §5.6's four triggers. **PROTOCOL §5.5** — a reader following only this
  section now derives the full order (critique → review_passed → task_completed → board → commit) and
  the correct SHA fact, without needing §5.6. **PROTOCOL §5.6** — the ordering is stated exactly once,
  in trigger 1; the bold paragraph lower down no longer competes with a partial version. **Role file**
  (checked technical-writer.md as representative of the 13) — a reader following only the role file
  learns not to log `task_completed` itself and where the real rule lives, without asserting a
  conflicting ordering. Verified: `python3 -m unittest discover -s tests -q` — 225 passed, 0 failed.
  `aph doctor` — healthy, all checks `[ok]`. Validator forced onto the repository bundle
  (`APHELOCOMA_ROOT` pointed at a nonexistent directory, confirmed via `_load_package` that
  `src/aphelocoma/hamilton_state.py` in this checkout was the loaded module) —
  `{"status": "ok", "errors": [], "warnings": []}`. Re-swept every backticked test ID in
  `docs/documentation-assertions-v0.3.md`: 105 unique `module.Class.test_method` citations (unchanged
  by the DOC-037 edit, which cites none), all 105 resolve against `unittest discover`; the one extra
  backtick match before filtering was the file's own placeholder sentence ("Test IDs use
  `module.Class.test_method`."), not a citation. DOC-040's `unreadable_status_report` coverage gap
  stays flagged, not closed (non-scope, tests/ untouched). `.aphelocoma/STATUS.md`'s working-tree diff
  (timestamp only, same seq 280) was not made by this turn — no Write/Edit touched it — and is left
  alone.
- 2026-07-26T06:52:00Z — artifact_written — Second pass after independent review: PROTOCOL.md's §5.5
  SHA sentence cited this project's own ledger counts ("ten `task_completed` notes and one advisor
  `decision`") — wrong for a portable, installed-read-only definition file a user reads for *their*
  project; cut to a general "a follow-up note, or an advisor `decision` recorded after the commit" with
  no project-specific numbers (DOC-037 in `docs/` keeps the general form it already had, untouched).
  ABOUT.md's new board sentence said `aph status` renders from "those two records" (resolving to
  `tasks.json` + `events.jsonl`); corrected to the two files `render_status_markdown`/
  `write_status_report` actually read — `hamilton.json` and `state/tasks.json` — since `events.jsonl`
  only contributes the stamp's `seq` via `_last_ledger_seq`. DOC-037's opening clause named critique,
  review pass, and board but not `task_completed` even though the next sentence relies on it preceding
  the commit; added it for self-consistency (pre-existing gap, not introduced this task).
- 2026-07-26T06:52:00Z — handoff — Swept the rest of the shared definition for the two claims this task
  touches, not just skill.md: `grep -rln task_completed skills/aph-hamilton/references/` outside
  `roles/` hits only `state.schema.json` (a bare event-type enum, no instruction about who logs it —
  benign) and `PROTOCOL.md` (fixed here); `agent-template.md`, `PARALLEL.md`, and
  `result.reviewer.schema.json` don't mention it at all. `result.implementer.schema.json`'s `events`
  enum for in-review results is `["work_started", "artifact_written", "handoff", "blocked",
  "assumption_logged"]` — `task_completed` was never a legal implementer-result event even
  mechanically, independent evidence for the 13-role-file fix. `grep -rn "commit SHA"` across
  `skills/aph-hamilton/`, `README.md`, `docs/` now hits only the two narrowed statements (PROTOCOL.md
  §5.5, DOC-037) plus this ledger's own prose. Re-verified after the second pass: `python3 -m unittest
  discover -s tests -q` (225 passed), `aph doctor` (healthy), forced-bundle validator (`status: ok`, 0
  errors, 0 warnings), 105/105 cited test IDs still resolve. Ready for qa-engineer review.
- 2026-07-26T06:55:13Z — artifact_written — Third pass: fixed the three CP4 findings on the T13 pass
  verdict. (1) DOC-037's opening clause had re-added `task_completed` as done-relative ("after its
  critique, review pass, `task_completed`, and regenerated progress board... are in place"), disagreeing
  with §5.5's own "the gate to `done` itself is `critique` + `review_passed` (§8); `task_completed`
  follows `done` rather than producing it" — the one point T13 was opened to settle. Rewrote it
  commit-relative: "commits each task after it reaches `done` (`critique` + review pass) and after its
  `task_completed` and regenerated progress board (§5.6) are in place" — `done` is now parenthetically
  defined by the gate alone, and `task_completed`/board sit only as commit preconditions, matching
  PROTOCOL §5.5's own structure exactly. (2) Widened the SHA escape clause in both PROTOCOL.md §5.5 and
  DOC-037 from an enumerated "a follow-up note, or an advisor `decision`" to "any event appended after
  the commit exists" — the narrow enumeration didn't cover this project's own ten `task_completed`
  events (seq 54, 95, 126, 142, 158, 168, 196, 225, 241, 257) that do name their own task's SHA (each
  verified earlier via `git log -S` to land in a strictly later commit than the SHA it names), which a
  reader grepping the ledger — the original T10 discovery method — would hit as apparent
  counterexamples. `PROTOCOL.md` still names no project or seq numbers, staying portable. (3) Rewrapped
  DOC-037's reflow artifact (orphaned "This is an explicit" line) to the file's convention.
  Re-verified: `python3 -m unittest discover -s tests -q` — 225 passed. `aph doctor` — healthy.
  Validator forced onto the repository bundle — `status: ok`, 0 errors; 1 pre-existing
  `stale_status_report` warning (ledger seq climbed from 280 to 284 between passes from the
  orchestrator's own concurrent activity outside this task's scope — `.aphelocoma/STATUS.md`,
  `events.jsonl`, and `tasks.json` were not touched by this turn). 105/105 cited test IDs still resolve.
  Ordering re-checked across `skill.md` (unedited, still consistent), §2 Phase 5, §5.5, §5.6, and a role
  file: all four agree on critique → review_passed (`done`) → `task_completed` → board → commit, with
  `done` now stated only via the gate, never via `task_completed`. Ready for qa-engineer re-review.
