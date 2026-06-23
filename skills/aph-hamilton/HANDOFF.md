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
- **Version pin** in `.aphelocoma/hamilton.json` (`definition_version` from `references/VERSION`).
- **Native parallel agents = Phase 2**, opt-in, generated from canonical roles (`sync-agents`),
  orchestrator-owned state for concurrency. Sequential file-based role-play is the portable default.
- Distribution reuses aphelocoma's `deploy` adapters. Personal use.

## Current status
- **Phase 1: DONE & cold-start-verified** (branch `hamilton-phase-1`). Rename/remap complete (company/OS
  → Hamilton, two-layer paths), `skill.md` finalized with cross-tool self-location + version pin,
  deployed to Claude + Codex, and a fresh agent ran the full solo loop with a schema-valid monotonic
  ledger + §7 coverage. Plan: `docs/superpowers/plans/2026-06-23-hamilton-phase-1.md`. Verdict:
  `docs/superpowers/notes/2026-06-23-hamilton-coldstart.md`.
- **Pending:** Phase 2 (native parallel agents) below.

> **Source of truth:** `ceo/company/` was the prototype origin; the canonical copy now lives here in
> `skills/aph-hamilton/references/`. Make future edits here, not in `ceo/company/`.

## Phase 1 (MVP, portable) — task list
1. **Rename pass:** company/OS → Hamilton across `references/` (incl. `ABOUT.md`,
   `START.reference.md`, `PROTOCOL.md`, role files). Keep "crew/team" as descriptive nouns.
2. **Finalize `skill.md`:** make `start`/`resume`/`status` read the definition via
   `${CLAUDE_SKILL_DIR}/references/…` and create/maintain the thin `.aphelocoma/` from
   `templates/aphelocoma/`.
3. **Version pin:** write `definition_version` on `start`; compare + warn on `resume`.
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

## Phase 1 deferred residuals (non-blocking — fold into Phase 2 verification)
- **`resume` + version-drift warning is unexercised.** Phase 1 proved the *write* side of the pin
  (`definition_version` recorded). The drift *detection* on `resume` is untested (same file-reading
  machinery, low risk). Cheap smoke test: bump installed `references/VERSION` to `1.0.1`, point a fresh
  agent at the example's populated `.aphelocoma/` (pin `1.0.0`) with `resume`, expect a drift warning.
- **Spec §4 content not asserted.** Phase 1 confirmed `specs/T1.md` exists but not that it carries
  Goal / Scope / Interfaces / Acceptance-criteria. Trivial to add to the next cold-start's checks.
- **Real Claude `/aph-hamilton` not run.** The `${CLAUDE_SKILL_DIR}` path (var *set*) is the easy case
  vs. the self-location path Phase 1 already proved with the var unset; backed by adr/journal in prod.
  Final confirmation is one interactive `/aph-hamilton` in a real Claude session.

## How to work
- Treat the spec as approved. Use the `writing-plans` skill to turn Phase 1 into a concrete plan,
  then implement. Don't deploy widely until the cold-start test passes.
- **Verification (non-negotiable):** copy a throwaway project, deploy Hamilton, give a FRESH agent
  only `/aph-hamilton start "a simple todo list app" solo`, and confirm it bootstraps `.aphelocoma/`,
  reads the installed definition, runs the full loop with schema-valid + monotonically-`seq`'d ledger
  events, applies §7 role coverage unprompted, and records the version pin. (This is how the prototype
  was validated — authored artifacts don't count as proof; an executed cold-start does.)

---

## Paste-this prompt to continue

> Read `docs/superpowers/specs/2026-06-23-hamilton-design.md` and `skills/aph-hamilton/HANDOFF.md` in
> full. We are building **Hamilton** — an aphelocoma-bound, file-based crew of role-agents that builds
> software, installed once and bootstrapped per-project into `.aphelocoma/`. The design is approved
> and the verified prototype is already relocated into `skills/aph-hamilton/`. Proceed with **Phase 1**
> from the spec: (1) rename company/OS → Hamilton across `references/`; (2) finalize `skill.md`
> start/resume/status against `${CLAUDE_SKILL_DIR}` + thin `.aphelocoma/`; (3) version pin; (4) adapter
> overrides if needed; (5) deploy to Claude + Codex and run the cold-start verification described in
> the spec. Use `writing-plans` to plan Phase 1 before implementing, and do not claim it works until a
> fresh-agent cold-start run passes. Then Phase 2 (native parallel agents).
