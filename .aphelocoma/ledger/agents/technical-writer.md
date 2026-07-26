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
- 2026-07-26T09:19:51Z — role_activated — Picked up T15: prepare v0.3.0 release paperwork
  (`CHANGELOG.md`, `docs/release-readiness-v0.3.md`, `docs/migration-v0.3.md`, new
  `docs/release-v0.3.0.md`) without pushing, merging, or tagging.
- 2026-07-26T09:19:51Z — work_started — Read `.aphelocoma/specs/T15.md` and re-verified its factual
  claims against the repo rather than trusting them: `git log origin/develop..develop` — 23 unpushed
  commits, last push `2026-07-04`; `.github/workflows/ci.yml` — ubuntu-latest/macos-latest ×
  Python 3.9/3.x, confirmed via `python3 -m unittest discover` (226 tests, macOS, Python 3.14.4 —
  matches); `docs/release-readiness-v0.3.md` git-blamed to `88d0e92` (2026-07-24, T6), confirmed it
  predates T7–T14 and never mentions the board or `STATUS.md`.
- 2026-07-26T09:19:51Z — work_started — Verified the old-install-command claim by running it, not
  reading it: built an isolated fake origin repo (v0.2.0 tag with a stub `bin/aph`, v0.3.0 tag with
  this repo's real `bin/aph`/`src`), copied `v0.2.0`'s actual published `install.sh` text, and ran it
  against three simulated machine states. Found the spec's single-outcome claim ("clones whatever main
  points at ... runs `aph setup`, fails") was incomplete: (1) fresh machine — clone, `checkout_latest_tag`
  lands on `v0.3.0` (not "main" — the script checks out the newest Git *tag*, confirmed separately by
  cloning a repo whose `main` had unmerged and merged-but-untagged v0.3-like commits: the old script
  still resolved to the last tag both times), no `data/core`, runs `aph setup` → `Error: Unknown
  command 'setup'`, exit 1 — this is the one case the spec actually verified; (2) v0.3 already
  installed (`~/.aphelocoma/tool` exists, confirmed on this machine to have no `.git`) → `git fetch
  --tags` fails outright → `Error: git fetch failed...`, exit 1; (3) a returning v0.2 user with a real
  git-cloned `tool/` and existing `data/core` (also confirmed present on this machine) → the script
  silently checks out `v0.3.0`, prints "Existing data found — preserved" and "Installation complete!",
  exits 0 — no error at all — leaving an unmanaged tool tree that `aph doctor` then catches as
  `[error] Installed tool exists without an ownership manifest`. Also confirmed merging to `main` is
  *not* the breaking moment: pushing the `v0.3.0` tag is — `checkout_latest_tag` still resolves to
  `v0.2.0` after a merge until that tag exists.
- 2026-07-26T09:19:51Z — artifact_written — `CHANGELOG.md`: `## [0.3.0] — Unreleased` → `## [0.3.0]`,
  matching the dateless `## [0.2.0]` heading style; no release date invented.
- 2026-07-26T09:19:51Z — artifact_written — `docs/migration-v0.3.md`: added "If you have the old
  install command saved" describing all three verified machine states above (who hits each, the exact
  output, exit code, and the doctor remediation for the silent case), and a closing note that the tag
  push — not the merge — is what triggers the change, correcting the framing in the outer task brief.
- 2026-07-26T09:19:51Z — artifact_written — `docs/release-readiness-v0.3.md`: refreshed rather than
  rewritten. Kept the T6 (2026-07-24) pre-bump/post-bump evidence as a labeled historical record; added
  "What changed since the T6 assessment" naming T7 (deployed-runtime fix), T8 (real-world v0.2
  migration), and T9–T14 (progress board, `.aphelocoma/STATUS.md`, non-blocking staleness warnings);
  added "Current local verification (2026-07-26)" with today's actual numbers (226 full-suite,
  210 T1–T5-style regression, 11 release-matrix, 8 package-inventory, validator/doctor/`git diff
  --check` output). Changed `Status: READY` to `Status: READY FOR CI — NOT YET READY TO RELEASE` and
  named Linux and Python 3.9 explicitly as pending CI everywhere the doc discusses status — while
  keeping `Status: READY`, `` Release version: `0.3.0` ``, and the unwrapped
  `Hosted runner execution: pending first CI run` as literal, unbroken substrings, because
  `tests.test_release_smoke.ReleaseContractTests.test_release_metadata_and_report_are_final` asserts
  all three with `assertIn`; reran that test by name and the full suite after editing to confirm both
  still pass (226 total, no test or code file touched).
- 2026-07-26T09:19:51Z — artifact_written — `docs/release-v0.3.0.md` (new): draft user-facing GitHub
  release notes, plus the advisor's 8-step checklist (push `develop` → watch CI → fix red legs on
  `develop`, never route around them → second pass on the readiness doc as its own numbered step, with
  an explicit warning that rewording the three asserted substrings above requires updating
  `test_release_metadata_and_report_are_final` as a separate deliberate task, not a silent edit →
  merge to `main` (verified not yet breaking) → tag `v0.3.0` (verified this is the actual breaking
  moment) → publish the release → end-to-end verify from a clean `$HOME`). No push/merge/tag/publish
  command was run by this task.
- 2026-07-26T09:19:51Z — handoff — Verified before returning: `python3 -m unittest discover -s tests
  -q` — 226 passed. `python3 bin/aph doctor` — healthy, exit 0. `python3
  skills/aph-hamilton/references/validate.py .` — 311 events, 15 tasks (14 done), 0 errors, 1
  pre-existing `stale_status_report` warning (STATUS.md 4 events behind ledger seq 311 — the designed
  non-blocking behavior; `.aphelocoma/STATUS.md` is not this task's file and was left alone).
  `git status --porcelain` shows only `CHANGELOG.md`, `docs/migration-v0.3.md`,
  `docs/release-readiness-v0.3.md` modified and `docs/release-v0.3.0.md` untracked from this turn;
  `.aphelocoma/hamilton.json`, `.aphelocoma/ledger/events.jsonl`, `.aphelocoma/state/tasks.json`
  (modified) and `.aphelocoma/specs/T15.md` (untracked) are pre-existing orchestrator-owned dirt from
  before this task started, not touched here. No spec claim was propagated uncorrected — the two
  corrections above (the old-install failure has three outcomes, not one; the tag push, not the merge,
  is the breaking moment) are written into the shipped docs themselves, not just this ledger. Ready for
  qa-engineer review.
- 2026-07-26T09:34:13Z — artifact_written — CP4 correction pass on three review findings, all closed.
  (1, should-fix) `docs/migration-v0.3.md`: the "git fetch failed" case's remediation sentence claimed
  re-running the old script "only reproduces the first case above" — wrong on a machine with v0.3
  installed *and* surviving `~/.aphelocoma/data/core` (a properly-upgraded v0.2 user), which lands in
  the silent third case instead. Reworded to "reproduces the first case above, or the third if you
  still have `~/.aphelocoma/data/core`", matching the reviewer's suggested fix; the advice that follows
  (use the current install command) needed no change since it holds either way. (2, nit)
  `docs/migration-v0.3.md`: softened "this command always ends up running v0.3 code" — confirmed via
  `git show v0.2.0:install.sh` that a fourth branch, `if [ -L "$TOOL_DIR" ]` (the local-dev symlink
  case), skips clone/fetch/checkout entirely; scoped the claim to "an ordinary install" and named the
  symlink exception explicitly, noting no ordinary v0.2 user is in that state. (3, nit)
  `docs/release-v0.3.0.md` step 2: added the workflow's fifth CI action, "smoke-tests an isolated
  installation," which the checklist omitted while `docs/release-readiness-v0.3.md`'s CI-inspection
  section already listed it — the two documents now agree. Left `docs/documentation-assertions-v0.3.md`
  untouched per the coordinator's note; it's outside T15's file scope. Re-verified after all three
  edits: `python3 -m unittest discover -s tests -q` — 226 passed. `tests.test_release_smoke
  .ReleaseContractTests.test_release_metadata_and_report_are_final` run individually — passed. `aph
  doctor` — healthy, exit 0. Hamilton validator against the repository — 0 errors, 1 pre-existing
  non-blocking `stale_status_report` warning (STATUS.md now 7 events behind ledger seq 314, up from 4
  behind seq 311 earlier in this task — the gap widened only because the orchestrator's ledger kept
  advancing concurrently; `.aphelocoma/STATUS.md` was not touched by this task). `git status
  --porcelain` — only `CHANGELOG.md`, `docs/migration-v0.3.md`, `docs/release-readiness-v0.3.md`
  modified, `docs/release-v0.3.0.md` untracked, plus this ledger; pre-existing orchestrator-owned dirt
  in `.aphelocoma/` untouched. No new command touched state-changing git.
- 2026-07-26T10:45:00Z — role_activated — Picked up T16: record CI #1's green hosted run (all four
  matrix jobs, ~1 minute, four harmless Node.js deprecation warnings) in
  `docs/release-readiness-v0.3.md`, written at T15 while CI was still pending.
- 2026-07-26T10:45:00Z — work_started — Read `.aphelocoma/specs/T16.md` and conventions. Verified the
  cited commit `e8d87de15ef793d4ebe02f0d86b4bf0b34cdde2c` is real and is `develop`'s current tip
  (`git log`, `git merge-base --is-ancestor` — confirmed ancestor of HEAD). Cross-checked the run's four
  job names and five CI steps against `.github/workflows/ci.yml` directly rather than trusting the spec.
  Grepped the whole report for `pending|not yet|untested|unverified|never|gap|blocked|remain|3\.9|linux
  |ubuntu|hosted` before and after editing (not just the two lines the spec named) to find every stale
  claim, including two the first narrow grep missed: line 21's "do not tag or publish... until" gate and
  line 119's "that gap is exactly what CI is for" close-out line.
- 2026-07-26T10:45:00Z — artifact_written — `docs/release-readiness-v0.3.md`: status line now
  `READY TO RELEASE — CI GREEN ON ALL FOUR LEGS, NOT YET TAGGED OR PUBLISHED` (still forecloses
  overclaiming merge/tag/publish, which stay the advisor's). Decision section names the run, commit,
  and four jobs and drops the "CI has never run" framing. Environment section's Python-3.9 sentence
  changed from "has not yet run" to "exercised... in CI #1... where it passed." Current-local-
  verification's closing line changed from "that gap is exactly what CI is for" to naming CI #1 as the
  coverage source. CI inspection section replaces the `Hosted runner execution: pending first CI run`
  placeholder with the run reference, commit, and four job names, plus a paragraph recording the four
  Node.js deprecation warnings (`actions/checkout@v4`/`actions/setup-python@v5` on Node 20, GitHub
  migrating to Node 24) as non-failing and explicitly out of scope to fix here. "What remains before
  release" marks steps 1–3 done/N-A with pointers to the new evidence, leaving only step 4
  (merge/tag/publish, still non-scope). Did not touch `CHANGELOG.md`, `docs/release-v0.3.0.md`,
  `docs/migration-v0.3.md`, or `VERSION`, and did not bump the two Actions versions (real fix, but
  would invalidate the run being recorded).
- 2026-07-26T10:45:00Z — artifact_written — `tests/test_release_smoke.py`:
  `test_release_metadata_and_report_are_final`'s single `Hosted runner execution: pending first CI run`
  literal replaced with a 7-item `subTest` loop asserting the run reference, commit SHA, and all four
  bare job strings (`ubuntu-latest / Python 3.9`, `ubuntu-latest / Python 3.x`, `macos-latest / Python
  3.9`, `macos-latest / Python 3.x`) individually — strictly more assertions than before, each pinned to
  content that only exists because CI actually ran — plus a status-line tightening
  (`assertIn("Status: READY TO RELEASE", ...)`, not just the old prefix-matching `"Status: READY"`) and
  an `assertNotIn` drift guard.
- 2026-07-26T10:45:00Z — artifact_written — Second pass on the same test after self-review found two
  weaknesses in the first cut: (1) the drift guard originally targeted the literal
  `"pending first CI run"`, which the report's own "What remains before release" section legitimately
  quotes when recording that step 3 is done — a future reflow of that paragraph could wrap the phrase
  across a line and produce a false failure pointing at correct prose; retargeted to
  `assertNotIn("Hosted runner execution: pending", report)`, which still catches the retired claim but
  can't collide with a historical quote or a line-wrap accident. (2) `assertIn("Status: READY", ...)`
  is a prefix of the retired `Status: READY FOR CI — NOT YET READY TO RELEASE`, so it would have passed
  against a reverted status line as long as the run evidence stayed; tightened to the full
  `"Status: READY TO RELEASE"`.
- 2026-07-26T10:45:00Z — handoff — Proved the stronger assertion both directions against the final test
  text above, not just reasoned about it, using a scratchpad backup + `cp` restore (never `git
  checkout`, since the edits were uncommitted; md5 `17b59bd3...` confirmed identical before and after
  every restore). Break A (evidence removed): deleted *both* copies of the CI evidence — the Decision
  section's Run/Commit/Result/Jobs bullets and the CI-inspection paragraph — and reran: FAILED, all 7
  `subTest`s (`Hosted runner execution: CI #1`, the run URL, the commit SHA, and all four job strings)
  reported `not found in ...`; restored, reran clean. Break B (claim reverted): with the real evidence
  left in place, re-inserted the exact retired line `Hosted runner execution: pending first CI run`
  alongside it — FAILED, `AssertionError: 'Hosted runner execution: pending' unexpectedly found in ...`;
  restored, reran clean. Then ran, and report here: `python3 -m unittest tests.test_release_smoke -v` —
  16 passed. `python3 -m unittest discover -s tests -q` — 226 passed. `aph doctor` and `python3 bin/aph
  doctor` — both `Aphelocoma doctor: healthy`, exit 0. `bash -n install.sh` — exit 0. `git diff --check`
  — clean, no whitespace errors (the report's own claim to that effect still holds after ~40 added
  lines). `python3 skills/aph-hamilton/references/validate.py .` — 323 events, 16 tasks (15 done), 0
  errors, 1 non-blocking `stale_status_report` warning (STATUS.md 4 events behind the orchestrator's own
  concurrently-advancing ledger; not this task's file, left untouched). `git status --porcelain` — only
  `docs/release-readiness-v0.3.md` and `tests/test_release_smoke.py` modified from this turn (plus this
  ledger); `.aphelocoma/hamilton.json`/`ledger/events.jsonl`/`state/tasks.json` (modified, T16 already
  "assigned" in them) and `.aphelocoma/specs/T16.md` (untracked) are pre-existing orchestrator-owned
  dirt from before this task started, confirmed untouched by any command run here. No state-changing
  git command was run. `docs/release-v0.3.0.md`'s own step 4 already describes this task per the spec's
  non-scope note and was intentionally left alone. Ready for qa-engineer review.
- 2026-07-26T11:15:00Z — artifact_written — CP4 pass closed both findings from the independent review
  (which re-proved the break/restore work — 8/8 literals load-bearing under individual mutation, whole-
  paragraph deletion fails, full pre-T16 revert fails — and confirmed CI #1 against the GitHub API:
  run_number 1, head_sha `e8d87de`, branch `develop`, conclusion success, four jobs named exactly as the
  report says, four Node 20 annotations one per job). (1, should-fix) The 7-literal evidence loop pinned
  the run's identity but not its outcome — the reviewer demonstrated a report that names the right
  run/commit/jobs while its surrounding prose claims every leg was red still passed. Added two more
  literals to the same loop, taken verbatim from the report's own wording: `"Result: success, all four
  matrix jobs"` (Decision section) and `"success on all four matrix"` (CI inspection section) — two
  locations rather than one, so flipping either independently is caught. (2, nit) The drift guard
  compared the literal `"Hosted runner execution: pending"` against the raw file text, so a markdown
  line wrap between "runner" and "execution:" slipped past it (reviewer's exact defeat). Added
  `import re` and normalize the report's whitespace (`re.sub(r"\s+", " ", report)`, collapsing any run
  of spaces/newlines to one) before that specific check, so a wrap can no longer split the phrase; every
  other assertion in the test still runs against the raw, unnormalized text, so this doesn't loosen
  anything else or make the guard tolerant of near-misses — it only tolerates whitespace shape.
- 2026-07-26T11:15:00Z — handoff — Proved both fixes live, both directions, using the same scratchpad-
  backup + `cp`-restore discipline as before (md5 `17b59bd3...` confirmed identical before and after
  every restore; never `git checkout`). Outcome assertion: flipped the report's wording to match the
  reviewer's exact exploit — `"CI has now run, once, on hosted runners, and every leg was red."` and
  `"FAILED on every one of the four matrix jobs"` in both the Decision bullet and the CI-inspection
  paragraph — reran: FAILED, exactly the two new `subTest`s (`'Result: success, all four matrix jobs'`,
  `'success on all four matrix'`), all 7 identity literals still passed unaffected; restored
  (md5-confirmed), reran clean. Whitespace guard: reproduced the reviewer's defeat verbatim — inserted
  `Hosted runner\nexecution: pending first CI run` (the exact wrap point that beat the pre-fix guard) —
  reran: FAILED, `AssertionError: 'Hosted runner execution: pending' unexpectedly found in ...` against
  the whitespace-normalized text, confirming the hole is closed; restored (md5-confirmed), reran clean.
  Then, and report here: `python3 -m unittest tests.test_release_smoke -v` — 16 passed. `python3 -m
  unittest discover -s tests -q` — 226 passed. `aph doctor` — healthy, exit 0. `bash -n install.sh` —
  exit 0. `git status --porcelain` — still only `docs/release-readiness-v0.3.md` and
  `tests/test_release_smoke.py` modified from this task (plus this ledger); the same pre-existing
  orchestrator-owned `.aphelocoma/` dirt as before, untouched. No state-changing git command was run.
  Not touched, per the coordinator's note: `docs/release-v0.3.0.md` step 4 (being handled separately)
  and no new test on the Node.js-warning paragraph (out of T16 scope). Ready for qa-engineer review.
