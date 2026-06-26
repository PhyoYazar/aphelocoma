# Hamilton Checkpoint Critique Passes & Craft Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent double-check reviewer before the three work-output checkpoints (CP1 brainstorm, CP2 plan, CP4 implementation), plus an always-on craft bar (simplicity, consistency, error handling) that guides how code is written and is enforced by the CP4 review.

**Architecture:** These are edits to Hamilton's **definition** (markdown under `skills/aph-hamilton/`), not application code. Two new read-only references carry the content (`references/CRITIQUE.md` = the per-gate rubric + operating rules; `references/CRAFT.md` = the always-on code-quality bar). The guarantee lives in the **flow**: PROTOCOL gains a critique pass before CP1/CP2/CP4, the CP4 critique *becomes* the Review/QA step (not a third layer), and one new ledger event (`critique`) + one reserved actor (`reviewer`) record that an independent review ran and at which independence **tier**. Roles get one-line pointers only.

**Tech Stack:** Plain Markdown + YAML. No build step, no runtime. "Tests" are **structural landing checks** (`grep`/file checks per task) plus **one executed seeded-defect catch-test** (Task 5) — the same way Hamilton Phases 1–2 and Foundations were verified (`docs/superpowers/notes/2026-06-*`). There is no unit-test framework for definition prose; do not invent one.

## Global Constraints

_Every task's requirements implicitly include this section. Values copied verbatim from the spec `docs/superpowers/specs/2026-06-26-hamilton-critique-passes.md`._

- **Critique runs at CP1, CP2, CP4 — never CP3** (CP3 picks a build style; no artifact to review).
- **Independence is tiered and logged:** fresh-context **subagent** on Claude Code; **persona pass** on platforms without subagents. The `critique` event records `tier: subagent | persona`.
- **Authority = advisory + one bounce-back:** serious findings return to the owning role once, then the work + findings surface to the advisor at the checkpoint. The advisor keeps the final call. One cycle only — it cannot loop.
- **CP4 critic IS the Review/QA step**, not a third layer after QA. The `review_passed` / `review_failed` lifecycle and the TDD-enforcement loop (from the foundations spec) are **unchanged**; the review is simply done independently and gains the craft + code lens.
- **Craft bar precedence (verbatim):** `correctness / error-handling  >  consistency-with-existing  >  simplicity (incl. YAGNI)`. It is a **floor, not a ceiling**. Always-on and universal, independent of the TDD toggle.
- **Fault-tolerance stays at CP1** (FOUNDATIONS topic) — the craft bar's "error handling" is its per-function code-level cousin, **not** a duplicate.
- **Exactly one new event type** (`critique`) and **one reserved actor** (`reviewer`). No new checkpoint. No new `state/` file — findings ride in the ledger + the checkpoint presentation.
- **`adapters/claude-code/agents/reviewer.md` is reused** as the CP4 code lens and is **NOT modified**.
- **Definition is read-only during project runs** (PROTOCOL §7). We may edit `references/` here only because we are working ON Hamilton, not running a project.
- Deploy of the edited skill (`/deploy claude`, `/deploy codex`) and `git push` are **user-owned** steps, not tasks here.

---

### Task 1: Reference content surfaces (CRITIQUE.md + CRAFT.md)

Create the two read-only references. These are the data surfaces every other task points at.

**Files:**
- Create: `skills/aph-hamilton/references/CRITIQUE.md`
- Create: `skills/aph-hamilton/references/CRAFT.md`

**Interfaces:**
- Produces: `references/CRITIQUE.md` (per-gate rubric + operating rules, referenced by PROTOCOL §1.5/§2 in Task 2, the roles in Task 3, and `skill.md` in Task 4); `references/CRAFT.md` (the craft bar, referenced by PROTOCOL §2 Phase 4/5 in Task 2 and the implementer roles in Task 3).

- [ ] **Step 1: Write the failing landing check**

Run: `ls skills/aph-hamilton/references/CRITIQUE.md skills/aph-hamilton/references/CRAFT.md`
Expected now: FAIL — `No such file or directory` for both.

- [ ] **Step 2: Create `references/CRITIQUE.md`**

Create the file with exactly this content:

```markdown
# CRITIQUE — the double-check rubric (read-only)

Before each of the three work-output checkpoints, an **independent reviewer** double-checks the crew's
work, so blind spots, plan holes, and quality defects are caught before they reach the advisor. This is
distinct from `adapters/claude-code/agents/reviewer.md` (a code-diff reviewer reused only as the CP4 code
lens below).

Run a critique before **CP1** (brainstorm), **CP2** (plan), and **CP4** (implementation). **Never CP3** —
it chooses a build style, with no artifact to review.

## Operating rules

- **Independent.** The reviewer must not be the agent that produced the work. Tier: a fresh-context
  **subagent** on Claude Code; on platforms without subagents, a **persona pass** (the running agent
  adopts the reviewer hat — roughly a checklist self-review). The achieved tier is logged on the
  `critique` event (PROTOCOL §5).
- **Floor, not ceiling.** Flag genuine *defects* against the rubric, not polish. Severity-tag each
  finding: **blocking** / **should-fix** / **nit**.
- **Authority = advisory + one bounce-back.** Serious (blocking) findings go back to the owning role
  **once** to fix; then the work + findings + fixes surface to the advisor at the checkpoint regardless.
  One cycle only — it cannot loop. The advisor always makes the final call.
- **Read-only on state.** The reviewer returns findings; the orchestrator logs the `critique` event and
  updates state (single-writer contract, `PARALLEL.md`).

## CP1 · Brainstorm  (read brief.md + Discovery notes)

- Blind spots **beyond** the six FOUNDATIONS topics (deploy, fault-tolerance, security, UX,
  observability, accessibility)?
- Unstated assumptions presented as fact? Any scope **fabricated** vs. advisor-confirmed?
- Are the proposed directions genuinely **distinct** (not three flavors of one)?
- Any defining question left unasked? Internal **contradictions** in goals/constraints/risks?

## CP2 · Plan  (read roadmap.md + tasks.json)   — the net-new gap; most attention

- Does **every roadmap item trace to a stated goal**? Does **every goal have at least one item**?
- Is each of the six foundations shown as **addressed or consciously deferred** (not silently dropped)?
- Are **dependencies sequenced** (nothing scheduled before its prerequisite)?
- Is **anything unowned**? Are milestones achievable / not missing an obvious step?

## CP4 · Implementation  (per in_review task) — this IS the Review/QA pass, done independently

- **Acceptance criteria** — every criterion in the task spec actually met? When **TDD is on**: tests
  written first, they pass, and they actually exercise the behavior.
- **Craft bar** (`CRAFT.md`) — error handling on plausible paths; consistency with existing patterns;
  simplicity/YAGNI — applying the precedence.
- **Code lens** (reuses `reviewer.md`) — logic / edge / off-by-one, contract or API breaks, security
  basics.

Pass → `review_passed` → `done`. Serious findings → `review_failed` → one bounce-back to the owner, then
surface at CP4.
```

- [ ] **Step 3: Create `references/CRAFT.md`**

Create the file with exactly this content:

```markdown
# CRAFT — the code-quality bar (read-only)

Hamilton's **always-on** standard for *how code is written*. It applies to every task's code on every
project, independent of the TDD toggle. Implementers write to it during Implementation (PROTOCOL §2
Phase 4); the CP4 critique enforces it (PROTOCOL §2 Phase 5; see `CRITIQUE.md`).

It is a **floor, not a ceiling** — the question is always *"is this below the bar?"* (a pass/fail
threshold), never *"could this be polished further?"*. Most code is already above the floor and passes
untouched.

## Precedence — when two principles pull against each other, the higher wins

> **correctness / error-handling  >  consistency-with-existing  >  simplicity (incl. YAGNI)**

The order is what keeps the bar from thrashing: a finding is only valid if a higher principle does not
already justify the code.

## The three principles

1. **Error handling** — handle every *plausible* failure path: validate inputs at boundaries, don't
   swallow errors, fail loudly or degrade deliberately, clean up resources. Do **not** handle
   *impossible* failures — that is the complexity simplicity catches. (This is the code-level cousin of
   the architectural **fault-tolerance** FOUNDATIONS topic, decided with the advisor at Discovery; this
   bar is per-function and always-on.)
2. **Consistency** — match the patterns and conventions that **already exist** in the codebase (naming,
   structure, error style, libraries); reuse what exists instead of duplicating. It is **never** a
   mandate to invent a new abstraction for hypothetical future reuse. _Escape hatch:_ when the prevailing
   pattern is clearly poor, or two existing patterns conflict, correctness/simplicity win and the
   divergence is noted — don't cement an anti-pattern.
3. **Simplicity (YAGNI)** — the simplest thing that works within the above: no premature abstraction, no
   dead code, no needless config or indirection, prefer the boring solution. "Might be reused later" is
   **not** a reason to abstract now.

## Why it converges (the conflict this resolves)

*Example:* an implementer writes a simple inline solution; could it be "made consistent / reusable"? One
question decides it — **does a shared pattern already exist?**
- **Yes** → reuse it (consistency says so, and reuse is also simpler — both agree).
- **No, it could only hypothetically be reused** → leave it inline (YAGNI; consistency is silent — there
  is nothing to match yet).

Deterministic, no oscillation. And because implementers and the reviewer read *this same file*, the
reviewer has nothing to re-litigate.
```

- [ ] **Step 4: Run the landing check (now passes)**

Run:
```bash
ls skills/aph-hamilton/references/CRITIQUE.md skills/aph-hamilton/references/CRAFT.md
grep -c -e "CP1 · Brainstorm" -e "CP2 · Plan" -e "CP4 · Implementation" skills/aph-hamilton/references/CRITIQUE.md
grep -c "correctness / error-handling  >  consistency-with-existing  >  simplicity" skills/aph-hamilton/references/CRAFT.md
```
Expected: both files listed; then `3`; then `1`.

- [ ] **Step 5: Verify the three gates and the floor-not-ceiling rule are present**

Run: `for t in "CP1" "CP2" "CP4" "Floor, not ceiling" "advisory + one bounce-back" "tier"; do grep -q "$t" skills/aph-hamilton/references/CRITIQUE.md && echo "ok: $t" || echo "MISSING: $t"; done`
Expected: six `ok` lines, no `MISSING`.

- [ ] **Step 6: Commit**

```bash
git add skills/aph-hamilton/references/CRITIQUE.md skills/aph-hamilton/references/CRAFT.md
git commit -m "Hamilton critique: add CRITIQUE.md rubric + CRAFT.md craft bar references"
```

---

### Task 2: PROTOCOL.md flow wiring (the guarantee)

Wire the critique passes into the protocol the crew executes: a critique before CP1/CP2, the CP4 critique as the Review/QA step, the craft bar at Implementation, and the new `critique` event + `reviewer` actor. This is the load-bearing task — it makes the double-check actually happen every run.

**Files:**
- Modify: `skills/aph-hamilton/references/PROTOCOL.md` (§1.5, §2 Phases 1/2/4/5, §5, §7)

**Interfaces:**
- Consumes: `references/CRITIQUE.md` + `references/CRAFT.md` (Task 1).
- Produces: the critique-pass steps + `critique` event + `reviewer` actor that `skill.md` (Task 4) and the roles (Task 3) point at.

- [ ] **Step 1: Write the failing landing check**

Run: `grep -c -e "CRITIQUE.md" -e "critique pass" -e "\`critique\`" -e "\`reviewer\`" skills/aph-hamilton/references/PROTOCOL.md`
Expected now: `0`.

- [ ] **Step 2: Note the critique passes in §1.5 (Advisor model)**

In `PROTOCOL.md` §1.5, find this line (the start of the paragraph after the four-checkpoint list):

```
Record each as a `decision` event: `actor: advisor`, `note` = the options offered + the choice (or
```

Insert this new paragraph immediately **before** it:

```
Before CP1, CP2, and CP4 an **independent reviewer** double-checks the crew's work against `CRITIQUE.md`
(blind spots at brainstorm, holes at plan, defects at implementation). The work is presented to the
advisor *with* the reviewer's findings and any fixes (see §2 Phases 1/2/5). CP3 has no artifact, so no
critique. The reviewer's authority is **advisory + one bounce-back**; the advisor still decides.

```

- [ ] **Step 3: Add the brainstorm critique to §2 Phase 1 (before CP1)**

In `PROTOCOL.md` §2 Phase `1. **Discovery / Brainstorm**`, find this sentence:

```
   End at **Checkpoint 1**: present 2–3 product
```

Insert immediately **before** it:

```
   **Brainstorm critique (before CP1):** an independent reviewer checks the captured direction, goals,
   and risks against `CRITIQUE.md`'s CP1 lens (blind spots beyond the six foundations, unstated
   assumptions, fabricated scope, whether the directions are distinct, unasked defining questions,
   contradictions). Serious findings bounce back **once** to leadership to address; then the work +
   findings are presented to the advisor. Log a `critique` event (§5).
```

- [ ] **Step 4: Add the plan critique to §2 Phase 2 (before CP2)**

In `PROTOCOL.md` §2 Phase `2. **Plan & Roadmap**`, find this sentence:

```
Log `plan_created` / `roadmap_updated`. End at **Checkpoint 2**: the advisor approves / reorders /
```

Insert immediately **before** `End at **Checkpoint 2**`, so the text reads:

```
Log `plan_created` / `roadmap_updated`. **Plan critique (before CP2):** an independent reviewer checks
the roadmap against `CRITIQUE.md`'s CP2 lens — every item traces to a goal, every goal has ≥1 item, each
of the six foundations is addressed or consciously deferred, dependencies are sequenced, nothing is
unowned. Serious findings bounce back **once** to leadership; then plan + findings are presented. Log a
`critique` event (§5). End at **Checkpoint 2**: the advisor approves / reorders /
```

- [ ] **Step 5: Add the craft bar to §2 Phase 4 (Implementation)**

In `PROTOCOL.md` §2 Phase `4. **Implementation**`, find this sentence:

```
   tasks, builds **in the project (at the repo root, beside `.aphelocoma/`)**, records artifacts, and moves the task to `in_review`.
```

Insert immediately **after** it:

```
   Implementers write code to the **craft bar** (`CRAFT.md`: error handling, consistency, simplicity —
   in that precedence) as a standing definition-of-done alongside the §4 acceptance criteria.
```

- [ ] **Step 6: Make §2 Phase 5 the independent critique (CP4)**

In `PROTOCOL.md` §2, replace the entire Phase 5 paragraph. Find:

```
5. **Review / QA** — qa-engineer (or covering role) checks each `in_review` task against its acceptance
   criteria. Pass → status `done`, log `review_passed`. Fail → status back to `assigned`/`in_progress`
   with notes, log `review_failed`. End at **Checkpoint 4**: the advisor accepts, or says what to fix /
   add (log a `decision`); fixes loop back as re-assigned tasks.
```

Replace it with:

```
5. **Review / QA (independent critique)** — the Review **is** an independent critique pass, not a layer
   after QA. qa-engineer (or covering role per §7) reviews each `in_review` task as a fresh-context
   reviewer — a subagent on Claude Code, else a persona pass — against `CRITIQUE.md`'s CP4 lens: **(a)**
   its acceptance criteria (incl. tests-first when TDD is on), **(b)** the craft bar (`CRAFT.md`), and
   **(c)** the code lens (logic/edge/contract/security, reusing `reviewer.md`). Log a `critique` event
   (§5; tier recorded). Pass → status `done`, log `review_passed`. Serious findings → status back to
   `assigned`/`in_progress` with notes, log `review_failed`, **one** bounce-back to the owner. End at
   **Checkpoint 4**: the advisor accepts, or says what to fix / add (log a `decision`); fixes loop back as
   re-assigned tasks.
```

- [ ] **Step 7: Add `critique` to the §5 event-type list**

In `PROTOCOL.md` §5, find:

```
  `phase_advanced`, `project_completed`, `decision`.
```

Replace it with:

```
  `phase_advanced`, `project_completed`, `decision`, `critique`.
```

- [ ] **Step 8: Define the `reviewer` actor in §5**

In `PROTOCOL.md` §5, find this bullet:

```
- The **`advisor`** actor is the human (the user) in the top seat; it appears on `decision` events
  (the options offered + the pick) and on any direction the human gives. Crew actors are role-ids.
```

Insert this new bullet immediately **after** it:

```
- The **`reviewer`** actor marks an independent critique pass (§1.5); `critique` events use it. The
  `note` records the gate (CP1/CP2/CP4), the verdict (`clear` / `findings`), severity, and the
  independence **tier** (`subagent` on Claude Code, else `persona`) — so a real second-pair-of-eyes
  review is distinguishable from a self-review. `task` is null at CP1/CP2 (phase-level) and set at CP4
  (per-task). At CP4 the `critique` event rides alongside the unchanged `review_passed` / `review_failed`.
```

- [ ] **Step 9: Add the reviewer dispatch + single-writer rule to §7**

In `PROTOCOL.md` §7, find this bullet:

```
- **Stay in lane** — role work builds the *product* in the project (beside `.aphelocoma/`). Do not
  modify Hamilton's own definition files (`references/`) while running a project unless explicitly asked.
```

Insert this new bullet immediately **before** it:

```
- **Independent review** — the CP1/CP2 critique is dispatched by leadership (the always-active `cto`
  runs it; covers per role-coverage above), the CP4 critique by `qa-engineer` (or nearest senior under
  coverage). On Claude Code the reviewer is a fresh subagent that is **read-only on state and returns
  findings** — the orchestrator logs the `critique` event and updates `tasks.json`/`events.jsonl`
  (single-writer contract, `PARALLEL.md`). On platforms without subagents it is a persona pass. The
  reviewer never writes state itself.
```

- [ ] **Step 10: Run the landing check (now passes)**

Run: `grep -c -e "CRITIQUE.md" -e "CRAFT.md" -e "critique" -e "reviewer" skills/aph-hamilton/references/PROTOCOL.md`
Expected: a count of `10` or more (the tokens appear across §1.5, §2 Phases 1/2/4/5, §5, §7).

- [ ] **Step 11: Verify each wiring point landed**

Run: `for t in "Brainstorm critique" "Plan critique" "Review / QA (independent critique)" "craft bar" "\`critique\`." "\`reviewer\`" "Independent review"; do grep -q "$t" skills/aph-hamilton/references/PROTOCOL.md && echo "ok: $t" || echo "MISSING: $t"; done`
Expected: seven `ok` lines, no `MISSING`.

- [ ] **Step 12: Commit**

```bash
git add skills/aph-hamilton/references/PROTOCOL.md
git commit -m "Hamilton critique: wire critique passes into PROTOCOL (CP1/CP2/CP4, craft bar, critique event + reviewer actor)"
```

---

### Task 3: Role pointers

Point the dispatching roles at the critique pass and the implementer/lead roles at the craft bar. One-line additions to `## Responsibilities` — no behavior beyond the pointer (the flow carries the guarantee).

**Files:**
- Modify: `skills/aph-hamilton/references/roles/cto.md`
- Modify: `skills/aph-hamilton/references/roles/software-architect.md`
- Modify: `skills/aph-hamilton/references/roles/product-manager.md`
- Modify: `skills/aph-hamilton/references/roles/qa-engineer.md`
- Modify: `skills/aph-hamilton/references/roles/fullstack-developer.md`
- Modify: `skills/aph-hamilton/references/roles/frontend-developer.md`
- Modify: `skills/aph-hamilton/references/roles/backend-developer.md`
- Modify: `skills/aph-hamilton/references/roles/frontend-lead.md`
- Modify: `skills/aph-hamilton/references/roles/backend-lead.md`

**Interfaces:**
- Consumes: `references/CRITIQUE.md` + `references/CRAFT.md` (Task 1), PROTOCOL §1.5/§2/§7 (Task 2).

- [ ] **Step 1: Write the failing landing check**

Run: `for f in cto software-architect product-manager qa-engineer fullstack-developer frontend-developer backend-developer frontend-lead backend-lead; do grep -qi -e critique -e craft skills/aph-hamilton/references/roles/$f.md && echo "ok $f" || echo "MISSING $f"; done`
Expected now: nine `MISSING` lines.

- [ ] **Step 2: Add the CP1/CP2 critique-runner pointer to `cto.md`**

In `roles/cto.md` `## Responsibilities`, find this bullet (the last one, added by the foundations work):

```
- Run the **Foundations pass** in Discovery (PROTOCOL §2 Phase 1): raise the six foundations from `FOUNDATIONS.md` with the advisor and confirm the TDD default before Checkpoint 1; cover any foundation whose owner role is not active (§7).
```

Insert this bullet immediately **after** it:

```
- Dispatch the **independent critique pass** before Checkpoint 1 (brainstorm) and Checkpoint 2 (plan) per `CRITIQUE.md`, and own the one bounce-back; in `solo`, also cover the Checkpoint 4 critique (§7).
```

- [ ] **Step 3: Add the critique pointer to `software-architect.md`**

In `roles/software-architect.md` `## Responsibilities`, append this bullet:

```
- The roadmap/specs you produce are independently critiqued at Checkpoint 2 before the advisor sees them (`CRITIQUE.md` CP2: every item traces to a goal, dependencies sequenced, nothing unowned); address findings on the bounce-back.
```

- [ ] **Step 4: Add the critique pointer to `product-manager.md`**

In `roles/product-manager.md` `## Responsibilities`, append this bullet:

```
- The directions/requirements you produce are independently critiqued at Checkpoint 1 before the advisor sees them (`CRITIQUE.md` CP1: blind spots, unstated assumptions, distinct directions); address findings on the bounce-back.
```

- [ ] **Step 5: Make the QA review the independent CP4 critique in `qa-engineer.md`**

In `roles/qa-engineer.md` `## Responsibilities`, find this bullet:

```
- Read each in-review task's spec and check the artifacts against every acceptance criterion.
```

Replace it with:

```
- Perform the **CP4 critique pass** (PROTOCOL §2 Phase 5; `CRITIQUE.md`) as an independent reviewer — a fresh subagent on Claude Code, else a persona pass — checking each in-review task against (a) every acceptance criterion, (b) the craft bar (`CRAFT.md`), and (c) the code lens (logic/edge/contract/security). Log a `critique` event (tier recorded).
```

- [ ] **Step 6: Add the craft-bar pointer to the three implementer roles**

In each of `roles/fullstack-developer.md`, `roles/frontend-developer.md`, and `roles/backend-developer.md`, in `## Responsibilities`, append this identical bullet:

```
- Write code to the **craft bar** (`CRAFT.md`: error handling > consistency-with-existing > simplicity/YAGNI); address CP4 critique findings on a bounce-back.
```

- [ ] **Step 7: Add the craft-bar pointer to the two lead roles**

In each of `roles/frontend-lead.md` and `roles/backend-lead.md`, in `## Responsibilities`, append this identical bullet:

```
- Hold work to the **craft bar** (`CRAFT.md`: error handling > consistency-with-existing > simplicity/YAGNI) in your lead review before it reaches the CP4 critique.
```

- [ ] **Step 8: Run the landing check (now passes)**

Run: `for f in cto software-architect product-manager qa-engineer fullstack-developer frontend-developer backend-developer frontend-lead backend-lead; do grep -qi -e critique -e craft skills/aph-hamilton/references/roles/$f.md && echo "ok $f" || echo "MISSING $f"; done`
Expected: nine `ok` lines, no `MISSING`.

- [ ] **Step 9: Commit**

```bash
git add skills/aph-hamilton/references/roles/cto.md skills/aph-hamilton/references/roles/software-architect.md skills/aph-hamilton/references/roles/product-manager.md skills/aph-hamilton/references/roles/qa-engineer.md skills/aph-hamilton/references/roles/fullstack-developer.md skills/aph-hamilton/references/roles/frontend-developer.md skills/aph-hamilton/references/roles/backend-developer.md skills/aph-hamilton/references/roles/frontend-lead.md skills/aph-hamilton/references/roles/backend-lead.md
git commit -m "Hamilton critique: role pointers (cto/architect/PM dispatch; QA review IS the CP4 critique; implementers/leads to the craft bar)"
```

---

### Task 4: skill.md entry wording

Make the entrypoint mention the critique passes + craft bar so an agent reading only `skill.md` knows CP1/CP2/CP4 are independently double-checked.

**Files:**
- Modify: `skills/aph-hamilton/skill.md`

**Interfaces:**
- Consumes: `references/CRITIQUE.md` + `references/CRAFT.md` (Task 1), PROTOCOL §1.5/§2 (Task 2).

- [ ] **Step 1: Write the failing landing check**

Run: `grep -c -e "CRITIQUE" -e "critique" -e "CRAFT" -e "craft bar" skills/aph-hamilton/skill.md`
Expected now: `0`.

- [ ] **Step 2: Mention the critique passes in the "What this is" section**

In `skill.md`, find this sentence in the `## What this is` section:

```
direction/plan/build-style at four checkpoints, and the crew builds it autonomously. Every action is
appended to a file ledger so you can review who did what. Full rules live in the definition's
`PROTOCOL.md` (located below).
```

Replace it with:

```
direction/plan/build-style at four checkpoints, and the crew builds it autonomously. Before you see the
work at Checkpoints 1, 2, and 4, an **independent reviewer** double-checks it (`references/CRITIQUE.md`) —
catching blind spots, plan holes, and code defects — and implementers write to a standing **craft bar**
(`references/CRAFT.md`: simplicity, consistency, error handling). Every action is appended to a file
ledger so you can review who did what. Full rules live in the definition's `PROTOCOL.md` (located below).
```

- [ ] **Step 3: Add CRITIQUE.md + CRAFT.md to the definition file list**

In `skill.md`, find this line in the `## Locating the Hamilton definition` section:

```
- **Definition (read-only):** `<skill>/references/` — `PROTOCOL.md`, `PARALLEL.md`, `roles/<id>.md`,
  `sizes.yaml`, `roles.index.md`, `settings.example.yaml`, `agent-template.md` are siblings inside it.
```

Replace it with:

```
- **Definition (read-only):** `<skill>/references/` — `PROTOCOL.md`, `PARALLEL.md`, `roles/<id>.md`,
  `sizes.yaml`, `roles.index.md`, `settings.example.yaml`, `agent-template.md`, `FOUNDATIONS.md`,
  `CRITIQUE.md`, `CRAFT.md` are siblings inside it.
```

- [ ] **Step 4: Run the landing check (now passes)**

Run: `grep -c -e "CRITIQUE" -e "craft bar" -e "CRAFT.md" -e "independent reviewer" skills/aph-hamilton/skill.md`
Expected: `4` or more.

- [ ] **Step 5: Commit**

```bash
git add skills/aph-hamilton/skill.md
git commit -m "Hamilton critique: skill.md mentions the independent critique passes + craft bar"
```

---

### Task 5: Executed seeded-defect catch-test verification

Prove the wiring **catches planted defects** — for a critic, "it ran" ≠ "it works" (the whole point is catching what the crew missed). This is the spec's verification gate. Authored artifacts don't count; the reviewer must flag the planted holes on its own. Mirror the foundations verdict-note pattern.

**Files:**
- Create: `docs/superpowers/notes/2026-06-26-hamilton-critique-verification.md` (the verdict)
- Scratch run dir (NOT committed): use a temp dir under the session scratchpad, e.g. `.../scratchpad/hamilton-critique-run/`

**Interfaces:**
- Consumes: all of Tasks 1–4 (the edited definition).

- [ ] **Step 1: Point the run at the edited definition**

`/deploy claude` is **user-owned** — don't block on it. Verify directly against the in-repo
`skills/aph-hamilton/references/` (`CRITIQUE.md`, `CRAFT.md`, `PROTOCOL.md`); that's the same definition a
deployed skill reads. Drive the reviewer by reading the definition directly (manual skills aren't
model-invocable — HANDOFF Phase-2 finding — so don't try to invoke `/aph-hamilton`).

- [ ] **Step 2: Plant a CP2 roadmap with two deliberate holes**

In the scratch dir, create `roadmap.md` with exactly this content (it has a goal with no task **and** an unowned task — both must be caught):

```markdown
# Roadmap — todo app

## Goals
- G1: users can add and list todos
- G2: users can mark a todo done   <!-- planted hole: no task implements G2 -->

## Milestones / tasks
- T1 (owner: fullstack-developer): add-todo form + POST handler  → traces to G1
- T2 (owner: fullstack-developer): list todos view              → traces to G1
- T3 (owner: ___): persistence layer                            <!-- planted hole: unowned -->

## Foundations
- Deploy: static host (addressed)
- Fault-tolerance: basic (deferred)
- Security: none-sensitive (deferred)
- UX: minimal (addressed)
- Observability: console logs (addressed)
- Accessibility: keyboard + labels (addressed)
```

- [ ] **Step 3: Run the CP2 critique against the planted roadmap and assert it catches both holes**

On Claude Code, **dispatch a fresh subagent** (the Agent tool) given the contents of
`skills/aph-hamilton/references/CRITIQUE.md` (CP2 lens + operating rules) and the planted `roadmap.md`,
instructed to return severity-tagged findings. (If subagents are unavailable, do the persona pass and
record `tier: persona`.)

Assert the returned findings explicitly name **both**:
- G2 has no task implementing it (a goal with no item), and
- T3 is unowned.

Both should be **blocking** or **should-fix**. If either planted hole is missed, the CP2 rubric is too
weak — FAIL the task and sharpen `CRITIQUE.md` CP2 before continuing.

- [ ] **Step 4: Spot-check CP1 and CP4 catch their planted defects**

- **CP1:** create `brief.md` containing the line `Direction: a realtime collaborative editor (assumes a
  websocket backend and multi-user auth)` with no such requirement captured elsewhere. Run the CP1
  critique (subagent or persona) with `CRITIQUE.md` CP1 lens; assert it flags the **unstated assumption**
  (websocket/multi-user-auth presented as fact).
- **CP4 (catches a defect):** create `bad.js` with `function save(x){ try { db.put(x) } catch(e){} }`
  (a swallowed error). Run the CP4 critique with `CRITIQUE.md` + `CRAFT.md`; assert it flags the
  **swallowed error** (craft-bar "error handling").
- **CP4 (no false positive — proves the precedence):** create `ok.js` with a single small inline helper
  used in exactly one place, with no pre-existing shared pattern. Assert the critique does **NOT** flag it
  as "should be extracted for consistency" (YAGNI/precedence holds — a clean simple-inline case passes).

- [ ] **Step 5: Assert the `critique` event shape is loggable and ledger stays monotonic**

Append a representative `critique` event to a scratch `events.jsonl` and confirm it parses and keeps the
gap-free `seq` invariant:

```bash
python3 -c "import json; e=json.loads('{\"ts\":\"2026-06-26T00:00:00Z\",\"seq\":1,\"event\":\"critique\",\"actor\":\"reviewer\",\"task\":null,\"note\":\"CP2 | verdict:findings | severity:blocking | tier:subagent | G2 uncovered; T3 unowned\"}'); assert e['event']=='critique' and e['actor']=='reviewer' and e['task'] is None; print('critique event ok')"
```
Expected: `critique event ok`. (Confirms the event uses the existing schema with `actor: reviewer`,
`task: null` at CP2, and tier/verdict/severity in `note`.)

- [ ] **Step 6: Write the verdict note**

Create `docs/superpowers/notes/2026-06-26-hamilton-critique-verification.md` recording: what ran, the
planted CP2 holes and that the critique flagged **both**, the CP1 unstated-assumption catch, the CP4
swallowed-error catch, the CP4 no-false-positive (precedence) result, the `critique` event-shape check,
and a PASS/FAIL verdict per assertion (Steps 3–5). Note the caveats: (1) the manual residual — a real
interactive `/aph-hamilton` confirming an independent reviewer actually runs before CP1/CP2/CP4 in a live
Claude session (the scripted run drives the reviewer directly); (2) on non-subagent platforms the tier is
`persona` (self-review strength), which the run should state explicitly if used.

- [ ] **Step 7: Commit the verdict (only the note — the scratch run stays out of the repo)**

```bash
git add docs/superpowers/notes/2026-06-26-hamilton-critique-verification.md
git commit -m "Hamilton critique: seeded-defect catch-test verdict (CP2 holes + CP1/CP4 catches flagged; precedence holds)"
```

---

## Self-Review

**1. Spec coverage** (spec `2026-06-26-hamilton-critique-passes.md`):
- Critique passes at CP1/CP2/CP4, not CP3 → Task 2 Steps 2–4, 6 (§1.5 + Phases 1/2/5) ✓
- Fresh-subagent reviewer + persona fallback, tier logged → Task 2 Step 8 (`reviewer` actor + tier) + Task 5 Steps 3–5 ✓
- Authority = advisory + one bounce-back → Task 2 Steps 2–4, 6; CRITIQUE.md operating rules (Task 1) ✓
- CP4 critic IS the Review/QA step (not a third layer); review_passed/failed + TDD loop unchanged → Task 2 Step 6 + Task 3 Step 5 (qa-engineer) ✓
- Craft bar always-on + precedence + floor-not-ceiling + escape hatch → Task 1 (CRAFT.md) + Task 2 Step 5 (Phase 4) ✓
- Fault-tolerance stays at CP1, not duplicated → CRAFT.md principle 1 text (Task 1) names it the "code-level cousin" ✓
- Conflict resolution (precedence, one-source-of-truth, backstop) → CRAFT.md "Why it converges" + Global Constraints ✓
- Exactly one new event (`critique`) + reserved actor (`reviewer`) → Task 2 Steps 7–8; asserted Task 5 Step 5 ✓
- Two read-only references; flow carries guarantee, roles get pointers → Task 1 (refs) + Task 2 (flow) + Task 3 (pointers) ✓
- reviewer.md reused, not modified → Global Constraints + not in any task's Files ✓
- Verification = seeded-defect catch-test (a) + manual (b) → Task 5 (catch-test) + Step 6 caveat (manual residual) ✓
- No gaps found. **Deviation from the spec's file list (noted):** the spec listed leadership pointers on cto/architect/PM and these are all included (Task 3 Steps 2–4); no role was dropped.

**2. Placeholder scan:** Every edit step shows the exact text to insert or replace. The `___` / `<!-- planted hole -->` strings in Task 5 Step 2 and the empty `catch(e){}` in Step 4 are **intentional seeded defects** the test must catch, not plan placeholders. No "TBD/TODO/handle edge cases" red flags.

**3. Type/name consistency:** File paths (`references/CRITIQUE.md`, `references/CRAFT.md`), the event name `critique`, the actor `reviewer`, the tier values `subagent`/`persona`, the gate labels `CP1`/`CP2`/`CP4`, and the precedence string `correctness / error-handling > consistency-with-existing > simplicity (incl. YAGNI)` are spelled identically across the spec, all four edit tasks, the grep checks, and the Task 5 assertions. The qa-engineer CP4 change (Task 3 Step 5) matches the PROTOCOL §2 Phase 5 rewrite (Task 2 Step 6): both say acceptance criteria + craft bar + code lens, independent, `critique` event logged.
