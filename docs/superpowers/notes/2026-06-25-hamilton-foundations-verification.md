# Hamilton "project foundations" — cold-start verification verdict

- **Date:** 2026-06-25
- **Feature under test:** Hamilton leadership core walks a six-topic Foundations pass with the advisor
  at Discovery (deploy, fault-tolerance, security, UX, observability, accessibility) and confirms a TDD
  default (on unless the advisor opts out). Definition (committed, Tasks 1–4):
  `skills/aph-hamilton/references/PROTOCOL.md` (§1.5, §2 Phase 0/1/2, §4),
  `skills/aph-hamilton/references/FOUNDATIONS.md`, `references/roles/*.md`, `templates/aphelocoma/`.
- **Verdict:** **PASS** — all four autonomous assertions pass on real run artifacts.
  A1 PASS · A2 PASS · A3 PASS · A4 PASS.

## What ran

A scripted **solo** cold-start run, driven by reading the definition directly (manual skills are not
model-invocable — HANDOFF Phase-2 finding — so `/aph-hamilton` was *not* invoked). I followed
`PROTOCOL.md` myself: adopted `cto` (covers software-architect / product-manager / QA / foundation-owners
in solo per §7) and `fullstack-developer` (builds), and played a **scripted advisor** at the four
checkpoints.

- **Scratch run dir (NOT committed):**
  `/private/tmp/claude-501/-Users-phyoyarzar-Personal-codes-aphelocoma/281b7da9-1f9c-4c1a-85c3-4a312575755f/scratchpad/hamilton-foundations-run/`
  — its own `git init`, with `.aphelocoma/` copied from `templates/aphelocoma/` and the product built at
  the repo root beside it.
- **Brief:** "a simple todo list app", size **solo**.
- **Scripted advisor picks (logged as `decision`, actor: `advisor`):** Checkpoint 1 — Direction #1
  (minimal self-contained todo core) + accept recommended solo size; Foundations pass — deploy=static
  file host, fault-tolerance=basic input validation, security=no sensitive data, UX=minimal clean,
  observability=console logging, accessibility=keyboard nav + labels; **TDD left on**; Checkpoint 2 —
  approve roadmap; Checkpoint 3 — one session (sequential); Checkpoint 4 — accept.
- **Product (in-memory, single process — documented non-scope: no cross-invocation persistence):**
  `todo/core.py` (`TodoStore`: add / list / complete + input validation + console logging),
  `todo/cli.py` + `todo/__main__.py` (text CLI: `[ ]`/`[x]` markers, friendly empty message, clear errors),
  `tests/test_core.py` (5 tests), `tests/test_cli.py` (4 tests).
- **Phases traversed (each `phase_advanced` logged):** kickoff → discovery → planning → breakdown →
  implementation → review → integration → done; `project_completed` logged.
- **TDD discipline observed (the "what ran" narrative):** for each task I wrote the test file first and
  ran it against a `NotImplementedError` stub → it failed (T1: `FAILED (errors=5)`; T2: `FAILED (errors=4)`)
  → implemented → re-ran → green (T1: `Ran 5 ... OK`; full suite: `Ran 9 ... OK`). See caveat 2 on how this
  narrative relates to the A3 PASS rationale.
- **Ledger:** 38 events, single writer, seq 1–38. Actors: cto 26, fullstack-developer 7, advisor 5.

## Assertion 1 — brief.md Foundations populated + TDD on → **PASS**

`grep -A8 "## Foundations" .aphelocoma/state/brief.md`:

```
## Foundations
_(raised at Discovery from references/FOUNDATIONS.md; advisory — they shape direction + roadmap, not done-gates)_
- Deploy: Static file host / single self-contained module — ship by copying files; no server infra for v1. (cto covers; devops/cloud not active)
- Fault-tolerance: Basic input validation — reject empty/whitespace titles, guard unknown todo ids; no external deps so no retries/timeouts needed for v1. (cto covers; sre not active)
- Security: No sensitive data — local single-user, no PII, no secrets, no network; no authn/authz for v1; input validation prevents bad state. (cto covers; appsec not active)
- UX: Minimal clean experience — clear list with `[ ]`/`[x]` markers, sensible empty-list and error messages. (cto covers; uiux-designer not active)
- Observability: Console logging of actions (add / list / complete) and errors; no metrics/tracing/alerting for v1. (cto covers; sre not active)
- Accessibility: Keyboard navigation + clear text labels — a text/CLI interface is inherently keyboard- and screen-reader-friendly; WCAG-minded labels. (cto covers; uiux-designer not active)
```

`grep "TDD:" .aphelocoma/state/brief.md` → `TDD: on`.

**Stub-caption nuance (disclosed):** `grep '_('` over `brief.md` returns three lines — lines 27, 36, 40.
These are the template **section captions** (the Foundations section's explanatory caption, the TDD
caption, the Activated-roles caption), **not** the six foundation *value* stubs. A targeted check of the
six value lines confirms none retains a stub:

```
grep -E '^- (Deploy|Fault-tolerance|Security|UX|Observability|Accessibility):' brief.md | grep '_('
→ (no match)  →  ">>> No _(...)_ stub in any of the six foundation items (PASS)"
```

The captions are left in place intentionally — that is what a real run produces (the template captions are
not runtime stubs to fill). All six foundation values are populated; the TDD line is `on`. **PASS.**

## Assertion 2 — roadmap references all six foundations → **PASS**

`for t in Deploy Fault Security UX Observability Accessibility; do grep -qi "$t" .aphelocoma/state/roadmap.md ...`:

```
roadmap ok Deploy
roadmap ok Fault
roadmap ok Security
roadmap ok UX
roadmap ok Observability
roadmap ok Accessibility
```

`roadmap.md` carries a "Foundations status" block mapping each of the six to a milestone as **addressed**
(how/when) or **consciously deferred** (why) — e.g. Deploy addressed at M3, fault-tolerance addressed at
M1 with retries/SPOF deferred, security addressed-by-scope with authn deferred, observability addressed
with metrics/tracing deferred, accessibility addressed with formal WCAG audit deferred. No `MISSING`. **PASS.**

## Assertion 3 — TDD enforcement reached a task spec + the product → **PASS**

A3 PASS rests on three checkable facts from the final artifacts (see caveat 2 for the scope limit):

(a) **The TDD-on spec has a tests-first acceptance criterion.** `.aphelocoma/specs/T1-core-todo.md`
Acceptance criteria include:

```
- [ ] **Tests-first (TDD is `on`):** unit tests covering the above behaviors were written **before** the
  implementation, fail against the empty/stub implementation, then pass once `core.py` is implemented.
  The test file is `tests/test_core.py` and must pass under `python3 -m unittest`.
```

(The T2 spec carries the same criterion. `grep -ril -e test -e acceptance .aphelocoma/specs/` matches both
specs; `ls .aphelocoma/specs/` → `T1-core-todo.md`, `T2-cli-surface.md`.)

(b) **Real test files exist in the product and pass when run.** `tests/test_core.py` (5 tests),
`tests/test_cli.py` (4 tests). `python3 -m unittest discover -s tests` → `Ran 9 tests ... OK` (exit 0).
Re-run per task at review: `tests.test_core` exit 0, `tests.test_cli` exit 0.

(c) **The QA `review_passed` for the TDD-on task depends on the tests.** From `events.jsonl`:

```
seq=32 task=T1-core-todo actor=cto: QA (cto covering qa-engineer, §7) verified T1 against spec acceptance
  criteria. Tests-first criterion: re-ran 'python3 -m unittest tests.test_core' at review -> Ran 5 OK
  (exit 0); ... PASS depends on tests.test_core passing.
seq=33 task=T2-cli-surface actor=cto: ... re-ran 'python3 -m unittest tests.test_cli' at review -> Ran 4 OK
  (exit 0); ... PASS depends on tests.test_cli passing.
```

The pass was gated on a test suite the QA actually re-ran at review time, not merely asserted. **PASS.**

## Assertion 4 — ledger integrity (seq monotonic + gap-free from 1) → **PASS**

```
python3 -c "import json; s=[json.loads(l)['seq'] for l in open('.aphelocoma/ledger/events.jsonl') if l.strip()]; \
  print('monotonic+gapfree' if s==list(range(1,len(s)+1)) else 'BAD '+str(s))"
→ monotonic+gapfree
```

38 events, first seq 1, last seq 38, single writer. Event types observed: role_activated×2,
assumption_logged×1, brainstorm_note×8, decision×5 (the four checkpoints + the TDD-confirm),
phase_advanced×6, plan_created×1, roadmap_updated×2, task_created×2, task_assigned×2, work_started×2,
artifact_written×2, task_completed×2, review_passed×2, project_completed×1. No new event type was
introduced — the foundation/TDD choices ride on `decision` / `brainstorm_note`, as specified. **PASS.**

## Caveats

1. **Manual residual (out of scope for an autonomous run).** A real interactive `/aph-hamilton` session
   confirming the six foundation topics are *spoken with the human advisor before Checkpoint 1* is not
   exercised here — this run **stubs the human turn** (the advisor's picks are scripted). The autonomous
   wiring (the six landing in `brief.md` + `roadmap.md`, the TDD default, the checkpoint `decision` events)
   is what these assertions verify; the human-conversation step remains a manual check.

2. **Tests-first authoring order is not independently auditable from the final artifacts.** This verdict
   asserts only that (a) the spec carries a tests-first acceptance criterion, (b) the test files exist and
   pass, and (c) `review_passed` depends on the tests. It does **not** assert as a verified property that the
   tests were authored before the implementation: final artifacts do not record authoring order. (The
   "What ran" section narrates a genuine RED→GREEN sequence I performed during this run, but that narrative
   is a description of the run, not an audit derivable from the committed/produced state — so A3's PASS
   rationale deliberately excludes it.)
```
