# Hamilton — Project Foundations Design Spec

_Date: 2026-06-25_

> Adds **kickoff foundations** to Hamilton (branch `hamilton-phase-1`). Builds on the
> advisor-collaboration design (`2026-06-25-hamilton-advisor-collaboration.md`): the 4-checkpoint
> human-in-the-loop flow is **kept**. This spec adds *what the leadership core must always raise with
> the advisor at the start of every project*, so cross-cutting concerns shape the project from day one
> instead of being bolted on after the app already exists.

## Context — the problem

Hamilton's Discovery brainstorm is currently open-ended: it interviews the advisor about the *product*,
but nothing guarantees the project's **cross-cutting foundations** — how it deploys, how it fails
gracefully, how it's secured, how it feels to use, how it's observed, how accessible it is — are even
discussed. The user wants these on the table **from the start of every project**, visible in the
roadmap, so they *shape the direction* rather than becoming expensive afterthoughts. Separately, the
user wants **TDD by default** on every project, with the ability to opt a given project out (e.g. a
quick PoC).

The user's framing question was: *"should these go in the role files (`<role>.md`) or in other flows?"*
This spec answers that (the flow carries the guarantee; roles get pointers) and defines the wiring.

## Two mechanisms (the core of this design)

The requirements split into two different shapes, wired differently. Modeling both as one uniform
"decide-then-enforce" loop was considered and **rejected**: the user explicitly wants the six topics to
be *foresight that can change direction*, not a checklist that blocks shipping — and TDD enforced. A
uniform gate would contradict the stated intent.

### A. Foresight topics (advisory) — six of them

`deploy` · `fault-tolerance` · `security` · `UX` · `observability` · `accessibility`

- **Raised in Discovery, every run**, by the leadership core, *with* the advisor.
- **Advisory, not gates.** They shape the **direction** (Checkpoint 1) and the **roadmap**
  (Checkpoint 2). They are *not* acceptance criteria that block a task from `done`. ("Helps us later,
  but not must-do.")
- **Anti-theater mechanism = the roadmap.** Each foundation appears in `roadmap.md` as either
  *addressed* (how) or *consciously deferred* (why). Surfacing in the plan — not QA-gating — is what
  keeps them honest at the planning layer.

Scope notes captured with the user:
- **Fault-tolerance** is meant broadly: graceful degradation, retries, error handling, no single point
  of failure.
- **Observability** and **accessibility** were added at the user's request (alongside the original
  four). The checklist is structured so more topics can be added later without rework.

### B. TDD (default-on toggle) — the one enforced standard

- **On by default** on every project. The advisor can **turn it off per-project** at kickoff (e.g. a
  PoC) just by saying so.
- **When ON, it is enforced** through Hamilton's *existing* closed loop: each task's **§4 acceptance
  criteria** require *tests written first*, and **QA verifies them at Review** (Phase 5 / Checkpoint 4)
  before a task is `done`. This is the one place "enforce" is real — and it comes free: QA already
  verifies acceptance criteria at Phase 5, so no `qa-engineer.md` change is needed.
- **When OFF**, that loop is skipped; the choice is recorded in `brief.md` so it's a deliberate
  decision, not silent drift.

## Where it lives — flow, not roles (the answer to the original question)

**The flow carries the guarantee; roles get one-line pointers.**

A role file is a *mission statement* (prose describing what a role cares about). A protocol phase is a
*checklist the agent steps through every run*. A guarantee — "always raise these six" — must live where
it is **executed every run**: the **Discovery phase**. Putting it only in role prose would let it
silently not happen. (Note: this is *not* because `cto` is size-gated — `cto` is active in every size;
it's because prose ≠ executed checklist.)

**Three artifacts** carry the foresight topics:

1. `references/FOUNDATIONS.md` — **NEW, read-only.** The canonical *Discovery checklist*: the six
   topics + the prompts to ask for each. Lives with the definition; never written during a run
   (PROTOCOL §7 keeps `references/` read-only).
2. `.aphelocoma/state/brief.md` — **per-project (read/write).** A new `## Foundations` section records
   the **decisions**; a `## TDD` line records on/off.
3. `.aphelocoma/state/roadmap.md` — **per-project.** Each foundation shown as **addressed or
   consciously deferred** — the artifact the user wants to "see from the start."

**Role pointers (one line each):**
- `cto` (active in *every* crew size) — runs the Foundations pass during Discovery; covers any absent
  foundation owner per §7.
- Specialists own their foundation **when active**: `security-engineer` / `appsec-engineer` → security;
  `uiux-designer` → UX + accessibility; `devops-engineer` / `cloud-engineer` → deploy; `sre` →
  fault-tolerance + observability.

## Flow changes (PROTOCOL.md)

- **§2 Phase 1 (Discovery)** gains a **Foundations pass**: before Checkpoint 1, the leadership core
  walks `FOUNDATIONS.md` with the advisor, records leanings in `brief.md`, and uses them to **inform the
  direction options + the crew-size recommendation** at CP1 (e.g. "security is central → recommend a
  size that includes `appsec`"; "UX/accessibility-heavy → include `uiux-designer`"). Foundations are
  advisory; unknowns become questions to the advisor, never fabricated scope.
  - **New project:** the pass asks the advisor where each foundation should land for v1.
  - **Existing project:** the pass runs *after* the codebase survey and assesses the **current state**
    of each foundation (how does it deploy today? is it observable? accessible?), surfacing gaps as
    roadmap candidates rather than asking from scratch.
- **§1.5 / Checkpoint 1** wording: directions are presented *with their foundation implications*, and
  the crew-size recommendation reflects which foundations need a specialist owner.
- **Phase 2 (Plan & Roadmap)**: the roadmap must show each foundation as addressed or consciously
  deferred (visible to the advisor at Checkpoint 2).
- **TDD default**: a line establishing TDD is **on unless the advisor disables it at kickoff**; the
  choice is recorded as a `decision` event + in `brief.md`.
- **§4 (Handoff contract)**: when TDD is on, each spec's **Acceptance criteria** must require
  tests-first for the task's behavior; QA verifies them at Review.

## brief.md template changes

Add to `templates/aphelocoma/state/brief.md`:

```
## Foundations
_(raised at Discovery; advisory — they shape direction + roadmap, not done-gates)_
- Deploy: _(target platform / tech / how we ship)_
- Fault-tolerance: _(graceful degradation, retries, error handling, no SPOF)_
- Security: _(threat model, authn/authz, secrets, data protection)_
- UX: _(experience bar, key flows)_
- Observability: _(logging, metrics, tracing, alerting)_
- Accessibility: _(WCAG target, keyboard nav, screen-reader, contrast)_

## TDD
_(on by default; advisor may set this off for a PoC at kickoff)_
TDD: on
```

## skill.md changes

- The guided start and the `start` fast path mention, at the Discovery step, that the leadership core
  raises the six foundations and that TDD is on by default (the advisor can say "no TDD" for a PoC).
- **No new mode, no new checkpoint** — this folds into the existing Discovery phase + Checkpoint 1.

## Optional settings

`references/settings.example.yaml` may document an optional `tdd: true` default a project could pin,
but Hamilton runs fine without it — the kickoff decision recorded in `brief.md` is the source of truth.

## What stays exactly the same

- The 4-checkpoint advisor flow, the phase sequence
  (Kickoff→Discovery→Plan→Breakdown→Implementation→Review→Integration), the role catalog.
- The ledger schema. **No new event type** — foundation + TDD choices ride on the existing `decision`
  and `brainstorm_note` events. **No new checkpoint.**
- Two-layer install, cross-tool self-location, orchestrator-owned-state parallelism.

## File impact (branch `hamilton-phase-1`, not yet deployed/pushed)

- **New:** `references/FOUNDATIONS.md`
- **Edit:** `references/PROTOCOL.md` (§1.5, §2 Phase 1 + Phase 2, §4); `templates/aphelocoma/state/brief.md`;
  `skill.md`; `references/roles/cto.md` (one-line pointer) + one-line pointers in
  `security-engineer.md`, `appsec-engineer.md`, `uiux-designer.md`, `devops-engineer.md`,
  `cloud-engineer.md`, `sre.md`; optionally `references/settings.example.yaml`.

## Verification approach

The flow is interactive, so verify in parts (matching the advisor-collaboration approach):

- **(a) Autonomous-assertable:** a scripted/stubbed run produces a `brief.md` with a populated
  `## Foundations` section + a `TDD:` line, and a `roadmap.md` that references each of the six
  foundations (addressed or deferred). With TDD on, at least one task spec's acceptance criteria include
  tests-first and the QA `review_passed` depends on them.
- **(b) Manual:** a guided `/aph-hamilton` run confirms the leadership core actually raises the six
  topics + the TDD default *before* Checkpoint 1.

## Decisions (locked with the user, 2026-06-25)

1. **Two mechanisms** — six advisory foresight topics + one default-on TDD toggle. ✓
2. **Six foresight topics** — deploy, fault-tolerance, security, UX, observability, accessibility
   (observability + accessibility added at the user's request). ✓
3. **Fault-tolerance = broad** — graceful degradation, retries, error handling, no single point of
   failure. ✓
4. **Advisory, not gates** for the six — they shape direction + roadmap; the anti-theater mechanism is
   roadmap visibility, not QA gating. ✓
5. **TDD on by default, per-project opt-out** at kickoff (PoC) — enforced via §4 acceptance criteria +
   QA at Review when on (QA already checks acceptance criteria, so no QA-role change needed). ✓
6. **Flow carries the guarantee** (Discovery Foundations pass + `references/FOUNDATIONS.md` +
   `brief.md`); roles get one-line pointers. ✓
