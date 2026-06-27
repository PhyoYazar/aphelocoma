# Hamilton — Checkpoint Critique Passes & Craft Bar Design Spec

_Date: 2026-06-26_

> Adds an independent **double-check reviewer** before the three human checkpoints that judge work
> output (CP1 brainstorm, CP2 plan, CP4 implementation), plus an always-on **craft bar** that guides how
> code gets written and is enforced by the CP4 review. Branch `hamilton-phase-1`. Builds on the
> advisor-collaboration design (`2026-06-25-hamilton-advisor-collaboration.md`) and the project-foundations
> design (`2026-06-25-hamilton-project-foundations.md`): the 4-checkpoint human-in-the-loop flow, the six
> foresight topics, and the TDD toggle are all **kept**. This spec inserts a *second pair of eyes* between
> "the crew finished the work" and "the advisor sees it," so blind spots, plan holes, and quality defects
> are caught before they reach the advisor — and gives the implementation phase a written quality floor.

## Context — the problem

Today, between the crew producing a work product and the human advisor reviewing it at a checkpoint,
there is **no independent second pass**:

- **CP1 (brainstorm):** the FOUNDATIONS pass guards the *six* cross-cutting topics, but nothing checks
  for blind spots *beyond* those six, unstated assumptions, or fabricated scope.
- **CP2 (plan):** **nothing critiques the roadmap at all.** A goal with no task, an unowned item, a
  mis-sequenced dependency, or a silently-dropped foundation reaches the advisor unflagged. This is the
  real gap.
- **CP4 (implementation):** QA checks each task against its acceptance criteria, but that is the *same
  agent* grading work to a functional checklist — no independent craft/code lens (simplicity,
  consistency, error handling, logic/edge defects).

Separately, the user wants the *coding flow itself* guarded: code should be written **simply**,
**consistently**, and with **good error handling** — not just reviewed after the fact. (Fault-tolerance,
the architectural cousin, already lives in the FOUNDATIONS pass at CP1 and is **not** duplicated here.)

The existing `adapters/claude-code/agents/reviewer.md` is a code-*diff* reviewer with no knowledge of
Hamilton's phases, ledger, or roadmap; it is reused as a *lens* at CP4 but is not the mechanism.

## Two parts (the core of this design)

The feature is two intertwined mechanisms, wired differently — mirroring how the foundations spec split
*foresight topics* from *TDD*:

### A. Critique passes (review-after) — at CP1, CP2, CP4

Before each of the three work-output checkpoints, an **independent reviewer** reads the phase output
against a per-gate rubric (`CRITIQUE.md`) and returns severity-tagged findings. The orchestrator logs the
result and decides the bounce-back. CP3 (build-style choice) judges no artifact and gets **no** critique.

- **Independence is the spine** — the reviewer must not be the agent that wrote the work, or it is
  rubber-stamping. Independence is **tier-dependent** (see *Independence tiers* below) and the tier is
  recorded in the ledger so a real review is distinguishable from a self-review at a glance.
- **Authority = advisory + one bounce-back.** On a serious finding the work goes back to the owning role
  **once** to fix; then everything (the work + findings + what was fixed) surfaces to the advisor at the
  checkpoint regardless. Bounded to one cycle → it is *structurally* incapable of looping. The advisor
  always makes the final checkpoint call (unchanged `decision` event).
- **Extend, don't duplicate.** CP1 extends FOUNDATIONS (checks *beyond* the six); CP4 **is** the
  Review/QA step done independently (not a third layer — see decision below); CP2 is net-new.

### B. The craft bar (guide-during) — always-on at implementation

A short, standing code-quality standard (`CRAFT.md`) that **guides implementers as they write** and is
**enforced by the CP4 critique**. The same one document drives writing and review, so the reviewer can
never demand something the writer was not already told to do. It is **always-on and universal** (you do
not opt out of "write it simply"), independent of the TDD toggle. Three principles, **lexically ordered**
so conflicts resolve deterministically instead of thrashing (this is the user's key concern — see below).

## Conflict resolution — why the craft bar converges (the user's key concern)

A naïve list of co-equal principles thrashes: the reviewer flags "too complex" and "not consistent" on
the same line and bounces forever. Three properties make it converge **by construction**:

1. **Floor, not ceiling.** The reviewer asks *"is this below the bar?"* (a pass/fail threshold), never
   *"could this be better?"* (an endless polish target). Most code is already above the floor and passes
   untouched. This is what prevents the critique from *"always triggering an enhancement."*
2. **Lexical precedence with non-overlapping scopes.** When two principles pull against each other, the
   higher one wins:

   > **correctness / error-handling  >  consistency-with-*existing*-code  >  simplicity (incl. YAGNI)**

   - **Error handling** — handle every *plausible* failure path. (An *impossible* failure is not worth
     handling — that is the complexity simplicity catches. Boundary = "is this failure real?")
   - **Consistency** — match a pattern that **already exists**. It is *never* a mandate to invent a new
     abstraction for hypothetical future reuse.
   - **Simplicity (YAGNI)** — simplest option within the above; "might be reused later" is **not** a
     reason to abstract now.

   *Worked example (the user's):* agent writes a simple inline thing; reviewer wonders "make it
   consistent / reusable?" → one question: *does a shared pattern already exist?* **Yes** → reuse it
   (consistency says so, and reuse is also simpler — both agree). **No, it could only hypothetically be
   reused** → leave it inline (YAGNI; consistency is silent — nothing to match yet). Deterministic; no
   oscillation.
3. **One source of truth.** Writer and reviewer read the same `CRAFT.md`, so the writer already applied
   this precedence — the reviewer has nothing to re-litigate.

**Escape hatch** (prevents cementing bad patterns): when the prevailing pattern is clearly poor or two
existing patterns conflict, correctness/simplicity win and the divergence is noted — "consistency" does
not propagate an anti-pattern.

**Backstop:** even if a residual tension survives all of the above, the one-bounce-back cap means it
surfaces to the advisor after a single pass. It cannot loop regardless of rule quality.

## Independence tiers (state the limitation plainly)

PROTOCOL §1 is emphatic: the system **MUST remain fully runnable sequentially; never require
parallelism.** So independence degrades gracefully, and the achieved tier is honest and logged:

| Platform | Reviewer tier | Strength |
|---|---|---|
| **Claude Code** | A fresh-context **subagent** — one `Agent` dispatch (NOT the parallel-build machinery), reads the artifact + `CRITIQUE.md`, returns findings. | Genuine second pair of eyes. |
| **Codex / others (no subagents)** | A **persona pass** — the running agent adopts the reviewer hat and walks `CRITIQUE.md`. | ≈ FOUNDATIONS-checklist strength (self-review, but still catches a lot). |

The single one-shot critic subagent is fine in *sequential* Claude Code runs — it is one dispatch, not
the orchestrator-owned-state parallel build. The `critique` event records `tier: subagent | persona`.

## Where it lives — flow + references + roles

Mirrors the foundations rollout (the flow carries the guarantee; references hold the rubric; roles get
one-line pointers):

**New references (read-only, with the definition):**
1. `references/CRITIQUE.md` — the per-gate rubric (CP1 / CP2 / CP4 lenses) + the reviewer's operating
   rules (independent, severity-tag findings, floor-not-ceiling, one bounce-back).
2. `references/CRAFT.md` — the always-on craft bar (the three lexically-ordered principles + the
   precedence rule + the escape hatch).

**Per-project state (read/write):** the `critique` ledger event (below). No new `state/` file — findings
ride in the ledger and are surfaced in the checkpoint presentation.

**Role pointers (one line each):**
- Leadership core (`cto`, `software-architect`, `product-manager`; `cto` covers all in `solo`) — dispatch
  the reviewer at CP1/CP2 and own the bounce-back.
- `qa-engineer` (when active; else nearest senior per §7) — at CP4, dispatches/owns the independent
  review (it *is* the QA step) and the bounce-back.
- Implementer roles (`fullstack-developer`, `frontend-developer`, `backend-developer`, plus leads) —
  write to the `CRAFT.md` bar; address findings on a bounce-back.

## Flow changes (PROTOCOL.md)

- **§1.5 (Advisor model):** each of CP1/CP2/CP4 is now preceded by an independent **critique pass**; the
  advisor is presented the work *plus* the reviewer's findings + any fixes. CP3 is unchanged (no
  artifact, no critique).
- **§2 Phase 1 (Discovery) → CP1:** after the FOUNDATIONS pass, run the brainstorm critique
  (`CRITIQUE.md` CP1 lens) — blind spots beyond the six, unstated assumptions, fabricated scope, are the
  directions distinct, unasked defining questions, contradictions. Bounce-back once, then present.
- **§2 Phase 2 (Plan & Roadmap) → CP2:** *(the net-new gap)* run the plan critique — every roadmap item
  traces to a goal; every goal has ≥1 item; each foundation shown addressed/deferred; dependencies
  sequenced; nothing unowned; milestones achievable. Bounce-back once, then present.
- **§2 Phase 4 (Implementation):** implementers write to the `CRAFT.md` bar (a standing definition-of-done
  alongside the §4 acceptance criteria).
- **§2 Phase 5 (Review / QA) → CP4 — CHANGED:** the Review step **is performed as the independent
  critique pass**, not a separate layer after QA. The reviewer checks each `in_review` task against
  **(a)** its acceptance criteria (the existing QA check, incl. tests-first when TDD is on), **(b)** the
  `CRAFT.md` bar, and **(c)** the code lens (logic/edge/off-by-one, contract/API breaks, security basics —
  reusing `reviewer.md`). Pass → `review_passed` → `done`; serious findings → `review_failed` → one
  bounce-back to the owner, then surface at CP4. The lifecycle and the TDD-enforcement loop are
  **unchanged**; the review is simply done independently and with the craft/code lens added.
- **§5 (State vs history):** add `critique` to the event-type list; define `reviewer` as a reserved actor
  (sibling to `advisor`) used on `critique` events.
- **§7 (Coverage):** the reviewer is dispatched by leadership (CP1/CP2) or QA (CP4); under coverage the
  nearest active senior dispatches it. The reviewer (subagent tier) is **read-only** on state and
  *returns* findings — the orchestrator logs them, preserving the single-writer contract (PARALLEL.md).

## `CRAFT.md` — the craft bar (content)

```
# CRAFT — the code-quality bar (read-only)

Always-on for every task's code, regardless of the TDD toggle. It is a FLOOR (is the code below it?),
not a polish target. Implementers write to it; the CP4 critique enforces it.

Precedence — when two pull against each other, the higher wins:
  correctness / error-handling  >  consistency-with-existing  >  simplicity (incl. YAGNI)

1. Error handling — handle every PLAUSIBLE failure path: validate inputs at boundaries, don't swallow
   errors, fail loudly or degrade deliberately, clean up resources. Do NOT handle impossible failures
   (that is complexity). [Code-level cousin of the architectural fault-tolerance FOUNDATIONS topic.]
2. Consistency — match the patterns/conventions ALREADY in the codebase (naming, structure, error style,
   libraries); reuse what exists instead of duplicating. Never a mandate to invent an abstraction for
   hypothetical reuse. Escape hatch: if the prevailing pattern is clearly poor or two conflict,
   correctness/simplicity win and the divergence is noted — don't cement an anti-pattern.
3. Simplicity (YAGNI) — the simplest thing that works within the above: no premature abstraction, no dead
   code, no needless config/indirection, prefer the boring solution. "Might be reused later" is not a
   reason to abstract now.
```

## `CRITIQUE.md` — the rubric (content)

```
# CRITIQUE — the double-check rubric (read-only)

Run an INDEPENDENT reviewer before CP1, CP2, CP4 (never CP3 — no artifact). Tier: fresh subagent on
Claude Code, else persona pass. Severity-tag findings (blocking / should-fix / nit). Authority = advisory
+ ONE bounce-back, then surface to the advisor. Floor, not ceiling — flag defects, not polish.

CP1 · Brainstorm (read brief.md + discovery notes)
  - Blind spots BEYOND the six FOUNDATIONS topics?
  - Unstated assumptions presented as fact? Any scope fabricated vs. advisor-confirmed?
  - Are the proposed directions genuinely distinct (not 3 flavors of one)?
  - Any defining question left unasked? Internal contradictions in goals/constraints/risks?

CP2 · Plan (read roadmap.md + tasks)   [the net-new gap — most attention]
  - Does every roadmap item trace to a stated goal? Does every goal have >=1 item?
  - Is each of the six foundations shown as addressed or consciously deferred (not silently dropped)?
  - Are dependencies sequenced (nothing before its prerequisite)? Is anything unowned?
  - Are milestones achievable / not missing an obvious step?

CP4 · Implementation (per in_review task) — this IS the Review/QA pass, done independently
  - Acceptance criteria: every criterion met? When TDD on: tests written first, pass, and actually
    exercise the behavior?
  - Craft bar (CRAFT.md): error handling on plausible paths; consistency with existing patterns;
    simplicity/YAGNI — per the precedence.
  - Code lens (reuses reviewer.md): logic/edge/off-by-one, contract/API breaks, security basics.
```

## Ledger — exactly one new event (`critique`)

Justification (the foundations spec deliberately added *none*, so this is earned): the existing events
cannot express *"an independent review ran at this gate, at this independence tier, with this verdict."*
That auditability — did a real second-pair-of-eyes review happen, or a self-review? — is the whole point
of the feature.

- **Shape (unchanged schema):**
  `{"ts":..,"seq":..,"event":"critique","actor":"reviewer","task":"<id|null>","note":"<gate> | verdict:<clear|findings> | severity:<..> | tier:<subagent|persona> | <summary>"}`
- `task` is **null** at CP1/CP2 (phase-level) and **set** at CP4 (per-task).
- At **CP4** it rides *alongside* the unchanged `review_passed` / `review_failed` (which still drive the
  task lifecycle and TDD enforcement). At **CP1/CP2** the `critique` event is the only review record;
  the checkpoint outcome remains a `decision` event by `actor: advisor` as today.
- The bounce-back fix is logged with existing events (`work_started` / `artifact_written` by the owning
  role); an optional second `critique` records the re-check.

## skill.md changes

- The guided start and the `start` fast path note that, before CP1/CP2/CP4, an independent reviewer
  double-checks the work (subagent on Claude Code, persona otherwise) and that implementers write to the
  craft bar. **No new mode, no new checkpoint** — this folds into the existing phases/checkpoints.

## What stays exactly the same

- The 4-checkpoint advisor flow, the phase sequence, the role catalog, the crew sizes.
- The task lifecycle (`pending→assigned→in_progress→in_review→done`) and the `review_passed` /
  `review_failed` TDD-enforcement loop from the foundations spec.
- Two-layer install, cross-tool self-location, orchestrator-owned-state parallelism, the single-writer
  contract. The reviewer adds **one** event type and **two** read-only references — nothing else.
- `adapters/claude-code/agents/reviewer.md` is reused as the CP4 code lens; it is **not** modified.

## File impact (branch `hamilton-phase-1`, not yet deployed/pushed)

- **New:** `references/CRITIQUE.md`, `references/CRAFT.md`
- **Edit:** `references/PROTOCOL.md` (§1.5, §2 Phases 1/2/4/5, §5 event list + `reviewer` actor, §7);
  `skill.md`; one-line role pointers in `cto.md`, `software-architect.md`, `product-manager.md`,
  `qa-engineer.md`, and the implementer roles (`fullstack-developer.md`, `frontend-developer.md`,
  `backend-developer.md`, `frontend-lead.md`, `backend-lead.md`).
- **Unchanged:** `adapters/claude-code/agents/reviewer.md` (reused as a lens).

## Verification approach

Interactive flow, so verify in parts — and (a) must be a **catch-test**, not a fired-event test (for a
critic, "it ran" ≠ "it works"):

- **(a) Autonomous-assertable — seeded-defect catch-test.** Hand the CP2 critique a roadmap with a
  **deliberate hole** (a goal with no task, *and* an unowned item) and assert the critique **flags both**
  with appropriate severity and emits a `critique` event with `verdict:findings` + `tier`. Repeat a
  smaller seeded check for CP1 (a planted unstated assumption) and CP4 (a task whose code violates the
  craft bar — e.g. a swallowed error). Confirm the one-bounce-back path logs the fix and re-check, and
  that the conflict-precedence does **not** produce contradictory findings on a clean simple-inline case.
- **(b) Manual.** A guided `/aph-hamilton` run confirms an independent reviewer actually runs before
  CP1/CP2/CP4 (subagent tier on Claude Code) and that its findings appear in the checkpoint presentation.

## Decisions (locked with the user, 2026-06-26)

1. **Critique passes at CP1/CP2/CP4** (not CP3 — no artifact). ✓
2. **Fresh-subagent reviewer** for genuine independence; **persona-pass fallback** on non-subagent
   platforms; tier recorded in the ledger. ✓
3. **Authority = advisory + one bounce-back**, then surface to the advisor; advisor keeps the final call. ✓
4. **CP4 critic IS the Review/QA step** (independent), not a third layer after QA; `review_passed` /
   `review_failed` lifecycle + TDD loop unchanged. ✓ *(advisor-flagged fork, settled)*
5. **Craft bar = always-on, universal** (simplicity + consistency + error-handling); **fault-tolerance
   stays at CP1** FOUNDATIONS (not duplicated). ✓
6. **Conflict resolution:** floor-not-ceiling + lexical precedence (correctness > consistency-with-existing
   > simplicity/YAGNI) + one-source-of-truth + escape hatch + one-bounce-back backstop. ✓
7. **Exactly one new event** (`critique`) + one reserved actor (`reviewer`); two read-only references
   (`CRITIQUE.md`, `CRAFT.md`); flow carries the guarantee, roles get pointers. ✓
8. **Verification = seeded-defect catch-test** (a) + manual (b). ✓
```
