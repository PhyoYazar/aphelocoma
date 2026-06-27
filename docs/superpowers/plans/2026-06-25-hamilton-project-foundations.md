# Hamilton Project Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Hamilton's leadership core always raise six cross-cutting *foundation* topics (deploy, fault-tolerance, security, UX, observability, accessibility) with the advisor at the start of every project, and apply TDD by default with a per-project opt-out.

**Architecture:** These are edits to Hamilton's **definition** (markdown under `skills/aph-hamilton/`), not application code. The guarantee lives in the **flow**: a new read-only checklist (`references/FOUNDATIONS.md`) + a Discovery "Foundations pass" in `PROTOCOL.md` + recording surfaces in the per-project `brief.md`/`roadmap.md`. Roles get one-line pointers only. The six foundations are **advisory** (they shape direction at Checkpoint 1 and the roadmap at Checkpoint 2; they never block a task from `done`). TDD is the **one enforced standard** when on (tests-first in §4 acceptance criteria, QA-verified at Review).

**Tech Stack:** Plain Markdown + YAML. No build step, no runtime. "Tests" are **structural landing checks** (`grep`/file checks per task) plus **one executed cold-start run** (Task 5) — the same way Hamilton Phases 1–2 were verified (`docs/superpowers/notes/2026-06-*`). There is no unit-test framework for definition prose; do not invent one.

## Global Constraints

_Every task's requirements implicitly include this section. Values copied from the spec `docs/superpowers/specs/2026-06-25-hamilton-project-foundations.md`._

- **The six foundation topics, exact names/order:** deploy, fault-tolerance, security, UX, observability, accessibility.
- **Advisory, not gates:** the six shape direction (CP1) + roadmap (CP2); they are NOT `done`-blocking acceptance criteria.
- **Anti-theater mechanism:** each foundation must appear in `roadmap.md` as *addressed* or *consciously deferred*.
- **TDD:** on by default; advisor may disable per-project at kickoff (e.g. PoC). When on → tests-first in PROTOCOL §4 acceptance criteria, QA-verified at Review. `brief.md` is the source of truth for the toggle.
- **No new checkpoint. No new ledger event type** — foundation/TDD choices ride existing `decision` + `brainstorm_note` events.
- **Definition is read-only during project runs** (PROTOCOL §7). We may edit `references/` here only because we are working ON Hamilton, not running a project.
- **Fault-tolerance = broad:** graceful degradation, retries/timeouts, error handling, no single point of failure.
- **No `settings.yaml` TDD pin** in this plan (YAGNI — `brief.md` is the source of truth). Deploy of the edited skill (`/deploy claude`, `/deploy codex`) is a user-owned step, not a task here.

---

### Task 1: Foundations content surfaces

Create the read-only Discovery checklist and add the recording sections to the per-project brief template. These are the data surfaces every other task references.

**Files:**
- Create: `skills/aph-hamilton/references/FOUNDATIONS.md`
- Modify: `skills/aph-hamilton/templates/aphelocoma/state/brief.md`

**Interfaces:**
- Produces: `references/FOUNDATIONS.md` (the canonical six-topic checklist, referenced by PROTOCOL §2 in Task 2 and `skill.md` in Task 4); `brief.md` `## Foundations` + `## TDD` sections (written at runtime by the Discovery pass).

- [ ] **Step 1: Write the failing landing check**

Run: `grep -ci -e deploy -e fault-tolerance -e security -e observability -e accessibility skills/aph-hamilton/references/FOUNDATIONS.md`
Expected now: FAIL — `grep: skills/aph-hamilton/references/FOUNDATIONS.md: No such file or directory`

- [ ] **Step 2: Create `references/FOUNDATIONS.md`**

Create the file with exactly this content:

```markdown
# FOUNDATIONS — the Discovery checklist (read-only)

The leadership core walks these **six foundation topics** with the advisor during Discovery
(PROTOCOL §2, Phase 1), *before* Checkpoint 1. They are **advisory**: they shape the product
**direction** (CP1) and the **roadmap** (CP2) — they are *not* acceptance criteria that block a task
from `done`. Record the advisor's decisions in `.aphelocoma/state/brief.md` (`## Foundations`) and
reflect each one in `.aphelocoma/state/roadmap.md` as **addressed** (how) or **consciously deferred** (why).

- **New project:** ask the advisor where each foundation should land for v1.
- **Existing project:** run this *after* the codebase survey and assess the **current state** of each
  (how does it deploy today? is it observable? accessible?), surfacing gaps as roadmap candidates.

Unknowns become questions to the advisor — never fabricated scope.

## The six topics

1. **Deploy** — Where and how does this ship? Target platform/host, the tech/runtime, and the path to
   production (manual, script, CI/CD). _Owner when active: `devops-engineer` / `cloud-engineer`._
2. **Fault-tolerance** — How does it behave when things fail? Graceful degradation, retries/timeouts,
   error handling, no single point of failure. _Owner when active: `sre`._
3. **Security** — What's the threat model? Authn/authz, secrets handling, input validation, data
   protection. _Owner when active: `security-engineer` / `appsec-engineer`._
4. **UX** — What's the experience bar? Key user flows, empty/error/loading states, overall feel.
   _Owner when active: `uiux-designer`._
5. **Observability** — How will we see what it's doing in production? Logging, metrics, tracing,
   alerting. _Owner when active: `sre`._
6. **Accessibility** — Who must be able to use it? WCAG target, keyboard navigation, screen-reader
   support, color contrast. _Owner when active: `uiux-designer`._

When a foundation's owner role is not active at the chosen crew size, the `cto` covers it (PROTOCOL §7).

## TDD (a default, not a foresight topic)

TDD is **on by default** for every project. The advisor may turn it **off** at kickoff for a throwaway
(e.g. a PoC) by saying so. Record the choice in `brief.md` (`## TDD`). When **on**, every task's spec
acceptance criteria (PROTOCOL §4) require tests written first, and QA verifies them at Review before
the task is `done`. When **off**, that requirement is skipped.
```

- [ ] **Step 3: Add `## Foundations` and `## TDD` to the brief template**

In `skills/aph-hamilton/templates/aphelocoma/state/brief.md`, replace this block:

```
## Crew size
_(picked at Checkpoint 1, after Discovery)_

## Activated roles
_(leadership core first; implementers after Checkpoint 1)_
```

with:

```
## Crew size
_(picked at Checkpoint 1, after Discovery)_

## Foundations
_(raised at Discovery from references/FOUNDATIONS.md; advisory — they shape direction + roadmap, not done-gates)_
- Deploy: _(target platform / tech / how we ship)_
- Fault-tolerance: _(graceful degradation, retries/timeouts, error handling, no SPOF)_
- Security: _(threat model, authn/authz, secrets, data protection)_
- UX: _(experience bar, key flows, empty/error states)_
- Observability: _(logging, metrics, tracing, alerting)_
- Accessibility: _(WCAG target, keyboard nav, screen-reader, contrast)_

## TDD
_(on by default; advisor may set this off for a PoC at kickoff)_
TDD: on

## Activated roles
_(leadership core first; implementers after Checkpoint 1)_
```

- [ ] **Step 4: Run the landing check (now passes)**

Run: `grep -ci -e deploy -e fault-tolerance -e security -e observability -e accessibility skills/aph-hamilton/references/FOUNDATIONS.md && grep -c "## Foundations" skills/aph-hamilton/templates/aphelocoma/state/brief.md && grep -c "TDD: on" skills/aph-hamilton/templates/aphelocoma/state/brief.md`
Expected: a non-zero count, then `1`, then `1`.

- [ ] **Step 5: Verify the six topics are all present in the checklist**

Run: `for t in Deploy Fault-tolerance Security UX Observability Accessibility; do grep -q "$t" skills/aph-hamilton/references/FOUNDATIONS.md && echo "ok $t" || echo "MISSING $t"; done`
Expected: six `ok` lines, no `MISSING`.

- [ ] **Step 6: Commit**

```bash
git add skills/aph-hamilton/references/FOUNDATIONS.md skills/aph-hamilton/templates/aphelocoma/state/brief.md
git commit -m "Hamilton foundations: add FOUNDATIONS.md checklist + brief.md Foundations/TDD sections"
```

---

### Task 2: PROTOCOL.md flow wiring (the guarantee)

Wire the Foundations pass and the TDD default into the protocol the crew executes. This is the load-bearing task — it's what makes "always discuss these" actually happen every run.

**Files:**
- Modify: `skills/aph-hamilton/references/PROTOCOL.md` (§1.5, §2 Phase 0/1/2, §4)

**Interfaces:**
- Consumes: `references/FOUNDATIONS.md` (Task 1).
- Produces: the Discovery Foundations-pass step + CP1 wording + roadmap requirement + TDD default + §4 tests-first rule that `skill.md` (Task 4) and the roles (Task 3) point at.

- [ ] **Step 1: Write the failing landing check**

Run: `grep -c -e "Foundations pass" -e "FOUNDATIONS.md" -e "addressed or consciously deferred" skills/aph-hamilton/references/PROTOCOL.md`
Expected now: `0`.

- [ ] **Step 2: Add the TDD default to §2 Phase 0 (Kickoff)**

In `PROTOCOL.md` §2, find the Phase `0. **Kickoff**` paragraph ending "Log `role_activated` per leadership role." and append this sentence to it:

```
   Set the **TDD default**: write `TDD: on` in `.aphelocoma/state/brief.md` (the advisor may flip it off during Discovery for a throwaway/PoC — §1.5).
```

- [ ] **Step 3: Add the Foundations pass to §2 Phase 1 (Discovery)**

In `PROTOCOL.md` §2 Phase `1. **Discovery / Brainstorm**`, find the sentence "Capture goals, constraints, risks (`brainstorm_note`)." and insert immediately after it:

```
   **Foundations pass (always):** before Checkpoint 1, walk `FOUNDATIONS.md`'s six topics (deploy,
   fault-tolerance, security, UX, observability, accessibility) WITH the advisor — for a new project
   ask where each lands for v1; for an existing project assess each topic's current state after the
   survey. Record decisions in `brief.md` `## Foundations` (log `brainstorm_note`s). These are
   **advisory**: they shape the direction options and the crew-size recommendation (a foundation that
   matters may add a specialist owner, e.g. security → `appsec`, UX/accessibility → `uiux-designer`).
   Also confirm the **TDD** default (on unless the advisor opts out for a PoC); record it in `brief.md`
   `## TDD` and log a `decision`.
```

- [ ] **Step 4: Require foundations in the roadmap (§2 Phase 2)**

In `PROTOCOL.md` §2 Phase `2. **Plan & Roadmap**`, find the sentence "Leadership produces `.aphelocoma/state/roadmap.md`: milestones and sequence." and replace it with:

```
   Leadership produces `.aphelocoma/state/roadmap.md`: milestones and sequence. The roadmap MUST show
   each of the six foundations (§1 Foundations pass) as **addressed** (how/when) or **consciously
   deferred** (why) — this is how they stay visible instead of forgotten.
```

- [ ] **Step 5: Note foundations + TDD in §1.5 Checkpoint 1**

In `PROTOCOL.md` §1.5, find checkpoint item `1. **After Discovery** — the advisor picks the product **direction** AND the **crew size** (leadership recommends a size from what Discovery revealed; see §2).` and replace it with:

```
1. **After Discovery** — the advisor picks the product **direction** AND the **crew size** (leadership
   recommends a size from what Discovery revealed; see §2). The directions are presented *with their
   foundation implications* (from the §2 Foundations pass), and the TDD default is confirmed here.
```

- [ ] **Step 6: Add the TDD tests-first rule to §4 (Handoff contract)**

In `PROTOCOL.md` §4, find the `- **Acceptance criteria**` bullet and insert this new bullet immediately after it:

```
- **Tests-first (when TDD is on)** — if `brief.md` `## TDD` is `on`, the acceptance criteria MUST
  include that tests for the task's behavior were written first and pass; QA verifies this at Review
  (§2 Phase 5). When TDD is `off` (e.g. a PoC), this requirement is skipped.
```

- [ ] **Step 7: Run the landing check (now passes)**

Run: `grep -c -e "Foundations pass" -e "FOUNDATIONS.md" -e "addressed or consciously deferred" -e "Tests-first" -e "TDD: on" skills/aph-hamilton/references/PROTOCOL.md`
Expected: `5` or more (each token present at least once).

- [ ] **Step 8: Commit**

```bash
git add skills/aph-hamilton/references/PROTOCOL.md
git commit -m "Hamilton foundations: wire Foundations pass + TDD default into PROTOCOL (Discovery/CP1/roadmap/§4)"
```

---

### Task 3: Role pointers

Give the always-active leadership role the job of running the pass, and make each specialist the owner of its foundation when active. One-line additions to `## Responsibilities` — no behavior beyond the pointer.

**Files:**
- Modify: `skills/aph-hamilton/references/roles/cto.md`
- Modify: `skills/aph-hamilton/references/roles/security-engineer.md`
- Modify: `skills/aph-hamilton/references/roles/appsec-engineer.md`
- Modify: `skills/aph-hamilton/references/roles/uiux-designer.md`
- Modify: `skills/aph-hamilton/references/roles/devops-engineer.md`
- Modify: `skills/aph-hamilton/references/roles/cloud-engineer.md`
- Modify: `skills/aph-hamilton/references/roles/sre.md`

**Interfaces:**
- Consumes: `references/FOUNDATIONS.md` (Task 1), PROTOCOL §2 Phase 1 (Task 2).

- [ ] **Step 1: Write the failing landing check**

Run: `for f in cto security-engineer appsec-engineer uiux-designer devops-engineer cloud-engineer sre; do grep -qi foundation skills/aph-hamilton/references/roles/$f.md && echo "ok $f" || echo "MISSING $f"; done`
Expected now: seven `MISSING` lines.

- [ ] **Step 2: Add the pass-runner pointer to `cto.md`**

In `roles/cto.md` `## Responsibilities`, find the bullet `- In Discovery, **brainstorm with the advisor**: present 2–3 technical directions with trade-offs (don't decide alone), and after the advisor picks, **recommend a crew size/shape** for them to choose (PROTOCOL §1.5).` and insert this bullet immediately after it:

```
- Run the **Foundations pass** in Discovery (PROTOCOL §2 Phase 1): raise the six foundations from `FOUNDATIONS.md` with the advisor and confirm the TDD default before Checkpoint 1; cover any foundation whose owner role is not active (§7).
```

- [ ] **Step 3: Add the owner pointer to `security-engineer.md`**

In `roles/security-engineer.md` `## Responsibilities`, append this bullet:

```
- Own the **security** foundation when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 4: Add the owner pointer to `appsec-engineer.md`**

In `roles/appsec-engineer.md` `## Responsibilities`, append this bullet:

```
- Own the application-level **security** foundation when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 5: Add the owner pointer to `uiux-designer.md`**

In `roles/uiux-designer.md` `## Responsibilities`, append this bullet:

```
- Own the **UX** and **accessibility** foundations when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 6: Add the owner pointer to `devops-engineer.md`**

In `roles/devops-engineer.md` `## Responsibilities`, append this bullet:

```
- Own the **deploy** foundation when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 7: Add the owner pointer to `cloud-engineer.md`**

In `roles/cloud-engineer.md` `## Responsibilities`, append this bullet:

```
- Own the infrastructure side of the **deploy** foundation when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 8: Add the owner pointer to `sre.md`**

In `roles/sre.md` `## Responsibilities`, append this bullet:

```
- Own the **fault-tolerance** and **observability** foundations when active (PROTOCOL §2 Phase 1 Foundations pass; see `FOUNDATIONS.md`).
```

- [ ] **Step 9: Run the landing check (now passes)**

Run: `for f in cto security-engineer appsec-engineer uiux-designer devops-engineer cloud-engineer sre; do grep -qi foundation skills/aph-hamilton/references/roles/$f.md && echo "ok $f" || echo "MISSING $f"; done`
Expected: seven `ok` lines, no `MISSING`.

- [ ] **Step 10: Commit**

```bash
git add skills/aph-hamilton/references/roles/cto.md skills/aph-hamilton/references/roles/security-engineer.md skills/aph-hamilton/references/roles/appsec-engineer.md skills/aph-hamilton/references/roles/uiux-designer.md skills/aph-hamilton/references/roles/devops-engineer.md skills/aph-hamilton/references/roles/cloud-engineer.md skills/aph-hamilton/references/roles/sre.md
git commit -m "Hamilton foundations: role pointers (cto runs pass; specialists own their foundation when active)"
```

---

### Task 4: skill.md entry wording

Make the entrypoint mention the Foundations pass and TDD default so an agent reading only `skill.md` knows the Discovery step includes them.

**Files:**
- Modify: `skills/aph-hamilton/skill.md`

**Interfaces:**
- Consumes: PROTOCOL §2 Phase 1 (Task 2), `references/FOUNDATIONS.md` (Task 1).

- [ ] **Step 1: Write the failing landing check**

Run: `grep -c -e "FOUNDATIONS" -e "foundations" -e "TDD" skills/aph-hamilton/skill.md`
Expected now: `0`.

- [ ] **Step 2: Mention foundations + TDD in the guided-start step (no-arguments mode)**

In `skill.md`, in the `### (no arguments) — guided start` section, find step `3. Bootstrap ./.aphelocoma/ and begin the **advisor flow** (start steps 3–4): the leadership core activates and discussion begins. **Crew size is chosen after Discovery (Checkpoint 1) — not here.**` and replace it with:

```
3. Bootstrap `./.aphelocoma/` and begin the **advisor flow** (`start` steps 3–4): the leadership core
   activates and discussion begins, including the **Foundations pass** — the six cross-cutting topics
   from `<skill>/references/FOUNDATIONS.md` (deploy, fault-tolerance, security, UX, observability,
   accessibility) and the **TDD default** (on unless you opt out for a PoC). **Crew size is chosen
   after Discovery (Checkpoint 1) — not here.**
```

- [ ] **Step 3: Mention foundations in the `start` fast-path Checkpoint 1 bullet**

In `skill.md`, in the `### start "<brief>" <size>` section, find the Checkpoint 1 bullet beginning `- **Checkpoint 1 (after Discovery):** present directions + a recommended crew size;` and replace its first sentence so the bullet reads:

```
   - **Checkpoint 1 (after Discovery):** run the **Foundations pass** (the six topics in
     `<skill>/references/FOUNDATIONS.md` + confirm the TDD default), then present directions + a
     recommended crew size; the advisor picks both; then activate the chosen implementer/specialist
     roles and record the size + foundations + TDD choice in `brief.md` + `tasks.json`. (If `<size>`
     was given on the command line, propose it as the recommendation; the advisor still confirms.)
```

- [ ] **Step 4: Run the landing check (now passes)**

Run: `grep -c -e "FOUNDATIONS" -e "Foundations pass" -e "TDD" skills/aph-hamilton/skill.md`
Expected: `3` or more.

- [ ] **Step 5: Commit**

```bash
git add skills/aph-hamilton/skill.md
git commit -m "Hamilton foundations: skill.md entry mentions Foundations pass + TDD default at Discovery/CP1"
```

---

### Task 5: Executed cold-start verification

Prove the wiring works end-to-end with a real run, the way Phases 1–2 were gated. Authored artifacts don't count — the run must produce the foundations + TDD evidence on its own. Stub the human picks (the run is interactive); assert the autonomous outputs.

**Files:**
- Create: `docs/superpowers/notes/2026-06-25-hamilton-foundations-verification.md` (the verdict)
- Scratch run dir (NOT committed): use a temp dir, e.g. `/private/tmp/claude-501/.../scratchpad/hamilton-foundations-run/`

**Interfaces:**
- Consumes: all of Tasks 1–4 (the edited definition).

- [ ] **Step 1: Point the run at the edited definition**

`/deploy claude` is **user-owned** — don't block on it. For verification, run directly against the in-repo `skills/aph-hamilton/references/`; that's the same definition a deployed skill reads.

- [ ] **Step 2: Run a scripted solo kickoff in the scratch dir**

Drive the run **by reading the definition directly** — `references/PROTOCOL.md` + `references/roles/<id>.md` + `references/FOUNDATIONS.md` + the `.aphelocoma/` you bootstrap in the scratch dir. (Manual skills aren't model-invocable — HANDOFF Phase-2 finding — so the prior cold-starts ran this way; don't try to invoke `/aph-hamilton`.) Use brief *"a simple todo list app"* at `solo`, stub the human picks (pick direction #1; accept the recommended size; for the Foundations pass answer each of the six briefly — e.g. deploy=static host, fault-tolerance=basic, security=none-sensitive, UX=minimal, observability=console logs, accessibility=keyboard+labels; leave TDD on), and let the crew build to `done`.

- [ ] **Step 3: Assert the Foundations + TDD landed in state**

Run (from the scratch run dir):
```bash
grep -A8 "## Foundations" .aphelocoma/state/brief.md
grep "TDD:" .aphelocoma/state/brief.md
for t in Deploy Fault Security UX Observability Accessibility; do grep -qi "$t" .aphelocoma/state/roadmap.md && echo "roadmap ok $t" || echo "roadmap MISSING $t"; done
```
Expected: a populated `## Foundations` block (no `_(…)_` stubs left); `TDD: on`; and each of the six foundations referenced in `roadmap.md` (addressed or deferred) — no `MISSING`.

- [ ] **Step 4: Assert TDD enforcement reached a task spec + the product**

Run (from the scratch run dir):
```bash
grep -ril -e "test" -e "acceptance" .aphelocoma/specs/ | head
ls .aphelocoma/specs/
```
Confirm by reading at least one `.aphelocoma/specs/<task>.md`: its **Acceptance criteria** include tests-first, AND a real test file exists in the product (beside `.aphelocoma/`) AND was run. Confirm the QA `review_passed` for that task depended on the tests.

- [ ] **Step 5: Assert ledger integrity (unchanged invariant)**

Run (from the scratch run dir):
```bash
python3 -c "import json,sys; seqs=[json.loads(l)['seq'] for l in open('.aphelocoma/ledger/events.jsonl') if l.strip()]; print('monotonic+gapfree' if seqs==list(range(1,len(seqs)+1)) else 'BAD '+str(seqs))"
```
Expected: `monotonic+gapfree`. (No new event type was added — only `decision`/`brainstorm_note` carry the foundation/TDD choices.)

- [ ] **Step 6: Write the verdict note**

Create `docs/superpowers/notes/2026-06-25-hamilton-foundations-verification.md` recording: what ran, the brief.md Foundations block + TDD line produced, the six roadmap references, the TDD-on spec + product test evidence, the ledger-integrity result, and a PASS/FAIL verdict per assertion (Steps 3–5). Note two caveats: (1) the manual residual — a real interactive `/aph-hamilton` confirming the six topics are *spoken* before CP1 (the scripted run stubs the human turn); (2) the verdict may state tests exist, pass, and that tests-first is an acceptance criterion, but NOT that test *authoring order* was verified (not auditable from final artifacts).

- [ ] **Step 7: Commit the verdict (only the note — the scratch run stays out of the repo)**

```bash
git add docs/superpowers/notes/2026-06-25-hamilton-foundations-verification.md
git commit -m "Hamilton foundations: cold-start verification verdict (foundations in brief/roadmap, TDD enforced, ledger intact)"
```

---

## Self-Review

**1. Spec coverage** (spec `2026-06-25-hamilton-project-foundations.md`):
- Two mechanisms → Task 2 (advisory pass + TDD default) ✓
- Six foresight topics → Task 1 (`FOUNDATIONS.md`, brief.md), asserted Task 5 ✓
- Flow-not-roles placement → Task 2 (PROTOCOL guarantee) + Task 3 (one-line pointers) ✓
- Three artifacts (FOUNDATIONS.md / brief.md / roadmap.md) → Task 1 (first two) + Task 2 Step 4 (roadmap requirement) ✓
- TDD enforced when on (§4 acceptance criteria + QA at Review; QA already verifies acceptance criteria, so no QA-role edit) → Task 2 Step 6 (§4), asserted Task 5 Step 4 ✓
- New + existing project handling → Task 1 (FOUNDATIONS.md text) + Task 2 Step 3 ✓
- Role-owner mapping → Task 3 ✓
- No new checkpoint / no new event → Global Constraints + Task 5 Step 5 assertion ✓
- Verification (a) autonomous + (b) manual → Task 5 ✓
- No gaps found.

**2. Placeholder scan:** Each edit step shows the exact text to insert. The `_(…)_` strings inside the brief.md template (Task 1 Step 3) are intentional runtime stubs, not plan placeholders. Task 5 uses concrete stub answers, not "fill in details." No red-flag placeholders.

**3. Type/name consistency:** Foundation names are identical across FOUNDATIONS.md, brief.md, PROTOCOL, roles, and the Task 5 checks (deploy, fault-tolerance, security, UX, observability, accessibility). The file path `references/FOUNDATIONS.md`, the section names `## Foundations` / `## TDD`, and the token `TDD: on` are spelled the same in every task and every grep check. Owner-role mapping in `FOUNDATIONS.md` (Task 1) matches the pointers added in Task 3.
