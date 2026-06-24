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

## How to work (Phase 2)
- Phase 1 is **done + cold-start-verified** on branch `hamilton-phase-1`; Hamilton is deployed to
  Claude + Codex at definition version `1.0.0`. The Phase 2 plan is written:
  `docs/superpowers/plans/2026-06-24-hamilton-phase-2.md`. Execute it with the `executing-plans` skill
  (or `subagent-driven-development`), task by task.
- **Verification (non-negotiable):** the Phase-2 gate is an EXECUTED **parallel** cold-start — a fresh
  agent runs a size with ≥2 disjoint implementer tasks, the manager dispatches them as parallel
  subagents, and the shared `.aphelocoma/state/tasks.json` + `ledger/events.jsonl` come out
  schema-valid with strictly monotonic, **gap-free** `seq` (proof no race corrupted the append-only
  ledger) and no lost task updates. Authored artifacts don't count. Also confirm the sequential
  fallback (with `parallel_dispatch` off) is unchanged.

---

## Paste-this prompt to continue (Phase 2)

> Read `docs/superpowers/specs/2026-06-23-hamilton-design.md`, `skills/aph-hamilton/HANDOFF.md`, and
> the Phase 2 plan `docs/superpowers/plans/2026-06-24-hamilton-phase-2.md` in full. **Phase 1 is done
> and cold-start-verified** on branch `hamilton-phase-1` (verdict:
> `docs/superpowers/notes/2026-06-23-hamilton-coldstart.md`); Hamilton is deployed to Claude + Codex at
> definition version 1.0.0. Execute **Phase 2 (native parallel agents)** from the plan: `sync-agents`
> generation from `references/roles/`, orchestrator-owned-state parallel dispatch (the orchestrator is
> the single writer of `tasks.json` + `events.jsonl`; subagents return structured results + write only
> `product/` and their own per-role ledger), version bump to 1.1.0, redeploy. Use `executing-plans`.
> Do NOT claim it works until an executed parallel cold-start passes with a gap-free monotonic ledger
> and no lost task updates, and the sequential path still works. Where cheap, fold in the three
> Phase-1 deferred residuals listed above (resume drift-warning, spec §4 content, a real interactive
> `/aph-hamilton` invocation).
