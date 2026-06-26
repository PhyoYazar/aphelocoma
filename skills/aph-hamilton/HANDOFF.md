# Hamilton — Continue Here

This is the handoff for continuing the **Hamilton** build inside the aphelocoma repo. Open a fresh
session at `/Users/phyoyarzar/personal/codes/aphelocoma` and paste the prompt at the bottom.

## What Hamilton is (one paragraph)

A portable, file-based **crew** of role-agents (CTO, architect, developers, QA, DevOps, …) that
brainstorm → plan → roadmap → assign → build software for a project, logging who-did-what to a file
ledger. It installs **once** (bundled with the `aph-hamilton` skill, read via `${CLAUDE_SKILL_DIR}`)
and runs in **any** project by bootstrapping a thin `.aphelocoma/` state folder there. Full design:
`docs/superpowers/specs/2026-06-23-hamilton-design.md`.

## Read these first
1. `docs/superpowers/specs/2026-06-23-hamilton-design.md` — the full design + locked decisions.
2. `skills/aph-hamilton/skill.md` — the DRAFT entrypoint (start/resume/status/sync-agents).
3. `skills/aph-hamilton/references/PROTOCOL.md` — the coordination protocol the crew follows.
4. `skills/aph-hamilton/examples/todo-solo/` — a real executed run (fresh agent, solo, todo app).

## Locked decisions (do not re-litigate)
- Name **Hamilton**; retire "company"/"OS" as labels. Skill = `/aph-hamilton`.
- **Thin + global ref**: definition installed once (in the skill's `references/`), per-project state
  only in `.aphelocoma/`. **No vendored copies.**
- **No version pin** (dropped 2026-06-25 — YAGNI for personal use; git history + the `created`
  timestamp cover reproducibility). `hamilton.json` records no `definition_version`; there is no `VERSION` file.
- **Native parallel agents = Phase 2**, opt-in, generated from canonical roles (`sync-agents`),
  orchestrator-owned state for concurrency. Sequential file-based role-play is the portable default.
- Distribution reuses aphelocoma's `deploy` adapters. Personal use.

## Current status
- **Phase 1: DONE & cold-start-verified** (branch `hamilton-phase-1`). Rename/remap complete (company/OS
  → Hamilton, two-layer paths), `skill.md` finalized with cross-tool self-location, deployed to Claude +
  Codex, and a fresh agent ran the full solo loop with a schema-valid monotonic ledger + §7 coverage.
  Plan: `docs/superpowers/plans/2026-06-23-hamilton-phase-1.md`. Verdict:
  `docs/superpowers/notes/2026-06-23-hamilton-coldstart.md`.
- **Phase 2: DONE & parallel-cold-start-verified.** `sync-agents` generation + orchestrator-owned-state
  parallelism implemented; an executed parallel run kept the shared ledger schema-valid +
  gap-free-monotonic under concurrent subagents. Plan:
  `docs/superpowers/plans/2026-06-24-hamilton-phase-2.md`. Verdict:
  `docs/superpowers/notes/2026-06-24-hamilton-parallel-coldstart.md`.
- **Post-build change (2026-06-25):** the version-pin was **dropped** (see Locked decisions) — no
  `definition_version`/`VERSION` anywhere; `resume` just reports phase + open tasks. The plans and
  verdict notes are dated records that still mention it; they are historical, not current.
- **Advisor collaboration: DONE & verified (2026-06-25).** Hamilton is now human-in-the-loop — you
  advise at 4 checkpoints (each a `decision` event), leadership brainstorms first + the crew is sized
  **after** Discovery, **no `product/`** (build at the project root, beside `.aphelocoma/`), interactive
  `/aph-hamilton` entry, and existing-project **survey + build-in-place**. Spec/plan/verdict:
  `docs/superpowers/specs/2026-06-25-hamilton-advisor-collaboration.md`,
  `docs/superpowers/plans/2026-06-25-hamilton-advisor-collaboration.md`,
  `docs/superpowers/notes/2026-06-25-hamilton-advisor-verification.md` (a–e PASS via scripted run).
- **Project foundations: DONE & cold-start-verified (2026-06-26).** At Discovery the leadership core
  raises six **advisory** foresight topics — deploy, fault-tolerance, security, UX, observability,
  accessibility — that shape direction (CP1) + roadmap (CP2) but never gate `done`; plus **TDD as a
  default-on, per-project-opt-out toggle** enforced (when on) via §4 acceptance criteria + QA at Review.
  Flow-anchored: `references/FOUNDATIONS.md` + a Discovery "Foundations pass" (PROTOCOL §2 Phase 1) +
  `## Foundations` / `## TDD` in `brief.md` surfaced in `roadmap.md`; one-line role pointers (`cto` runs
  the pass + covers absent owners §7; specialists own their topic when active). Spec/plan/verdict:
  `docs/superpowers/specs/2026-06-25-hamilton-project-foundations.md`,
  `docs/superpowers/plans/2026-06-25-hamilton-project-foundations.md`,
  `docs/superpowers/notes/2026-06-25-hamilton-foundations-verification.md` (A1–A4 PASS via scripted run).
  ADR-0018.
- **Checkpoint critique passes & craft bar: DONE & catch-test-verified (2026-06-26).** Before the three
  work-output checkpoints an **independent reviewer** (fresh subagent on Claude Code; persona-pass
  fallback, tier logged) double-checks the crew's work: CP1 brainstorm (blind spots beyond the six
  foundations, unstated assumptions), CP2 plan (the net-new gap — every roadmap item traces to a goal,
  nothing unowned, deps sequenced), CP4 implementation (the Review/QA step done **independently** + a
  craft/code lens). Authority = **advisory + one bounce-back**; one new `critique` event + reserved
  `reviewer` actor. Plus an always-on **craft bar** (`references/CRAFT.md`: precedence
  `correctness/error-handling > consistency-with-existing > simplicity/YAGNI`, floor-not-ceiling) that
  guides implementers and is enforced by the CP4 critique. Flow-anchored: `references/CRITIQUE.md` +
  `references/CRAFT.md` + PROTOCOL §1.5 / §2 Phases 1/2/4/5 / §5 / §7 + 9 role pointers + `skill.md`.
  Fault-tolerance stays at CP1 (not duplicated); `reviewer.md` reused as the CP4 code lens, unmodified.
  Spec/plan/verdict: `docs/superpowers/specs/2026-06-26-hamilton-critique-passes.md`,
  `docs/superpowers/plans/2026-06-26-hamilton-critique-passes.md`,
  `docs/superpowers/notes/2026-06-26-hamilton-critique-verification.md` (CP1/CP2/CP4 seeded-defect
  catch-test PASS; opus whole-branch review = MERGE, 0 Critical / 0 Important).
- **Remaining (user-owned):** deploy (`/deploy claude` + `/deploy codex`) and `git push`; then run the
  **manual checklists** in the verdict notes (the interactive stop-and-ask pauses) — for advisor-collab
  the a–e checklist, for foundations one interactive `/aph-hamilton` confirming the six topics are
  *spoken* before CP1, and for critique-passes one interactive `/aph-hamilton` confirming an independent
  reviewer runs before CP1/CP2/CP4 (the catch-test drove the critic subagents directly); plus the
  low-risk residuals (spec §4 content).

> **Source of truth:** `ceo/company/` was the prototype origin; the canonical copy now lives here in
> `skills/aph-hamilton/references/`. Make future edits here, not in `ceo/company/`.

## Phase 1 (MVP, portable) — task list
1. **Rename pass:** company/OS → Hamilton across `references/` (incl. `ABOUT.md`,
   `START.reference.md`, `PROTOCOL.md`, role files). Keep "crew/team" as descriptive nouns.
2. **Finalize `skill.md`:** make `start`/`resume`/`status` read the definition via
   `${CLAUDE_SKILL_DIR}/references/…` and create/maintain the thin `.aphelocoma/` from
   `templates/aphelocoma/`.
3. ~~**Version pin**~~ — built, then **dropped** (2026-06-25); `start`/`resume` carry no version.
4. **Confirm cross-tool skill-dir resolution + adapter overrides:** `${CLAUDE_SKILL_DIR}` is verified
   on Claude only — confirm Codex resolves the skill's bundled `references/` too (or have the codex
   adapter rewrite the variable). This is the one unverified piece of the platform-agnostic promise —
   check it early. Add `adapters/*/overrides/aph-hamilton.yaml` only if needed.
5. **Deploy** (`aph deploy claude`, `aph deploy codex`) and **cold-start test** (below).

## Phase 2 — native agents
- `sync-agents`: generate `.claude/agents/<role>.md` from `references/roles/` (derived, regenerable).
- Orchestrator-owned-state parallelism (manager dispatches; manager is the single writer of
  `tasks.json` + `events.jsonl`). Cold-start test the parallel path.
- **De-risked already (Phase 1 finding):** `disable-model-invocation: true` does NOT conflict with
  native agents. In the Phase-1 cold-start, a subagent couldn't *invoke* `/aph-hamilton` (manual skills
  are off the model-invocable list) yet ran the entire protocol by reading the role file + PROTOCOL +
  `.aphelocoma/` directly — exactly how a generated `.claude/agents/<role>.md` subagent will operate.
  So the generated agents read the definition/state directly; they never re-invoke the skill.

## Deferred residuals (non-blocking)
- **Spec §4 content not asserted.** Phase 1 confirmed `specs/T1.md` exists but not that it carries
  Goal / Scope / Interfaces / Acceptance-criteria. Trivial to add to the next cold-start's checks.
- **Real Claude `/aph-hamilton` not run.** The `${CLAUDE_SKILL_DIR}` path (var *set*) is the easy case
  vs. the self-location path Phase 1 already proved with the var unset; backed by adr/journal in prod.
  Final confirmation is one interactive `/aph-hamilton` in a real Claude session.

## How to work (Phase 2)
- Phase 1 is **done + cold-start-verified** on branch `hamilton-phase-1`; Hamilton is deployed to
  Claude + Codex. The Phase 2 plan is written:
  `docs/superpowers/plans/2026-06-24-hamilton-phase-2.md`. Execute it with the `executing-plans` skill
  (or `subagent-driven-development`), task by task.
- **Verification (non-negotiable):** the Phase-2 gate is an EXECUTED **parallel** cold-start — a fresh
  agent runs a size with ≥2 disjoint implementer tasks, the manager dispatches them as parallel
  subagents, and the shared `.aphelocoma/state/tasks.json` + `ledger/events.jsonl` come out
  schema-valid with strictly monotonic, **gap-free** `seq` (proof no race corrupted the append-only
  ledger) and no lost task updates. Authored artifacts don't count. Also confirm the sequential
  fallback (with `parallel_dispatch` off) is unchanged.

---

## Paste-this prompt to continue (remaining work)

> Read `skills/aph-hamilton/HANDOFF.md` and the two verdict notes under `docs/superpowers/notes/`.
> **Both Phase 1 and Phase 2 are implemented and cold-start-verified** on branch `hamilton-phase-1`.
> What remains: (1) deploy with `/deploy claude` and `/deploy codex`, and `git push` the branch;
> (2) the two low-risk residuals — assert spec §4 content in a run, and run one real interactive
> `/aph-hamilton` in a Claude session to confirm the `${CLAUDE_SKILL_DIR}` path. Don't claim a fix
> works without an executed check.
