# Hamilton — Advisor Collaboration Design Spec

_Date: 2026-06-25_

> Revises the interaction model of the Hamilton built on branch `hamilton-phase-1` (design:
> `2026-06-23-hamilton-design.md`, amended). The verified **machinery** — two-layer install, ledger
> schema, cross-tool resolution, orchestrator-owned-state parallelism — is **kept**. What changes is
> the **interaction layer** (human-in-the-loop) and two simplifications (no `product/`, interactive entry).

## Context — what's changing and why

The first build made Hamilton **autonomous**: the crew decided everything and built unattended. The
user wants the opposite of a black box: **they are the advisor on every decision; the crew does all
the building.** Concretely:

- A vague brief (e.g. *"build an ecommerce"*) must trigger a **real brainstorm** — the crew interviews
  the user and proposes options with trade-offs; it never guesses a product.
- The user steers the *thinking* (brief, brainstorm, plan, roadmap, what-to-build/fix/add); the crew
  owns the *building* (implementation). The user never writes code.
- There are **no modes** ("advisor" vs "autopilot"). This collaborative flow is simply how Hamilton works.

## Decisions (locked with the user, 2026-06-25)

1. **One flow, no modes.** You advise (decisions); the crew builds (implementation). Always.
2. **Decision cadence = phase checkpoints** (5 of them — §"Decision points"). Between checkpoints the
   crew works on its own; the user can interject at any time (it's one chat).
3. **Vague brief ⇒ interview, not guess.** At Discovery the crew asks the user the defining questions
   and proposes 2–3 directions with trade-offs before anything is built.
4. **"You decide" is always allowed.** At any checkpoint the user may defer to the crew's
   recommendation; the crew proceeds and records that the user delegated the call.
5. **No `product/` constraint.** `.aphelocoma/` is the **only** directory Hamilton owns. The product is
   built at the **project root, beside `.aphelocoma/`**, structured however fits (`src/`, `index.html`,
   a framework app, …).
6. **Build-execution is the user's choice.** Right before Implementation, when parallel is possible
   (Claude Code + ≥2 disjoint tasks), the crew asks: *subagents or one session?* This replaces the
   hidden `parallel_dispatch` toggle.
7. **Interactive entry.** Bare `/aph-hamilton` starts a guided session; the typed fast path
   (`/aph-hamilton start "…" <size>`) still works.
8. **Existing projects: survey-first, build in place.** Discovery reads the existing codebase before
   proposing; the crew edits/extends in place following existing patterns. Detect an existing
   `.aphelocoma/` and offer `resume` instead of overwriting.

## The model in one line

> **You advise, the crew builds.** The crew proposes options + asks the right questions at the decision
> points; you pick (or say "you decide"); the crew implements autonomously; you review.

## Decision points (the five checkpoints)

At each checkpoint the crew **pauses and presents a short menu** — 2–3 options with trade-offs and a
recommendation (or targeted questions) — and waits for the user's pick / answer / "you decide".

| # | Checkpoint | Crew presents | User does |
|---|---|---|---|
| 1 | **After Kickoff** | the scope it understood + the crew it proposes to activate | confirm / adjust scope + size |
| 2 | **After Discovery** | for a vague brief: defining questions, then 2–3 product directions w/ trade-offs | answer + pick the direction (what to build) |
| 3 | **After Plan & Roadmap** | milestones, the feature/task list, and the order | approve / reorder / cut / add |
| 4 | **Before Implementation** | *how to build* — parallel subagents vs one session (only if parallel is possible) | pick the execution strategy |
| 5 | **At Review** | what got built vs each task's acceptance criteria | accept, or say what to fix / add |

Between checkpoints (notably during Implementation) the crew works autonomously. The user can still
type at any time ("also add dark mode") and the crew folds it in.

## Vague-brief brainstorm (Discovery, expanded)

For an under-specified brief the Discovery phase becomes a short **interview** run by the product/
architecture roles. Example — brief *"build an ecommerce"*:
- "What are you selling, and who buys it?"
- "v1 must-haves vs later: product list, cart, checkout, accounts, payments, search, inventory — which now?"
- "Here are 2–3 ways to shape v1 (lean storefront / full catalog+accounts / marketplace), with
  trade-offs — which direction?"

Only after the user answers + picks does the crew produce the roadmap (checkpoint 3). The crew **must
not** fabricate scope; unknowns become questions, not assumptions.

## File layout (simplified)

```
<project>/                     ← the product is built HERE, at the root, beside .aphelocoma/
├─ .aphelocoma/                ← the ONLY directory Hamilton owns (bookkeeping)
│  ├─ hamilton.json            project · size · roles · phase
│  ├─ state/                   tasks.json · roadmap.md · brief.md
│  ├─ specs/                   <task>.md handoff contracts
│  └─ ledger/                  events.jsonl + agents/<role>.md
├─ src/ · index.html · …       ← whatever structure the build needs (no forced `product/`)
```

The retired `product/` term is removed from PROTOCOL.md and the role files: "build under `product/`"
→ "build in the project (the files beside `.aphelocoma/`)".

## Interactive entry

**Bare `/aph-hamilton`** runs a short guided Q&A:
1. New project, or work on this existing one? (auto-detect: existing code present? existing `.aphelocoma/`?)
2. What do you want to build / add / fix? (plain words; may be vague)
3. Crew size — it recommends one from the answer; user confirms or changes.
4. (Then the normal flow begins at checkpoint 1.)

If an `.aphelocoma/` already exists, it reports the in-progress project and offers `resume`. The typed
fast path stays for power users.

## Existing projects

- Discovery begins with a **codebase survey** (structure, key files, conventions, stack) before any
  proposal; the survey is logged (`brainstorm_note`s).
- Implementation **edits/extends in place**, following the project's existing patterns — no separate
  output folder.
- Safety comes from checkpoint 3: **no file is changed until the user has approved the plan.**

## The logbook records your decisions

A new ledger event **`decision`** captures each checkpoint: the options the crew offered and the
user's pick (or "delegated"). `actor` is `advisor` (the human seat). So the timeline reads like
meeting minutes — *"crew proposed A/B/C → advisor chose B."* This is the only ledger-schema change
(one added event type); the line shape `{ts,seq,event,actor,task,to,note}` is unchanged.

## What stays exactly the same (kept from the verified build)

- The phase sequence (Kickoff→Discovery→Plan→Breakdown→Implementation→Review→Integration) and the role
  catalog.
- The ledger format + monotonic `seq` + state-vs-history rule (PROTOCOL §5).
- Two-layer install (definition in `references/`, per-project `.aphelocoma/`), cross-tool self-location.
- Orchestrator-owned-state parallelism (`PARALLEL.md`) — now *chosen by the user* at checkpoint 4
  rather than a settings toggle.
- Sequential single-agent role-play remains the guaranteed default when parallel isn't chosen/possible.

## Impact on the existing build (branch `hamilton-phase-1`, not yet deployed/pushed)

This **modifies** (not rebuilds): PROTOCOL.md (add checkpoints; drop `product/`), `skill.md`
(interactive entry; the advisor flow; build-choice prompt; `resume`-on-existing), the role files
(`product/` → project root; leadership roles present options to the advisor), and `PARALLEL.md`
(triggered by the build-choice). Adds the `decision` event type. The machinery verified in Phase 1/2
is reused as-is.

## Verification approach (note)

The old gate was an *unattended* cold-start. This flow is **interactive**, so it can't be fully
cold-started by a fresh agent with no human. The plan will verify in parts: (a) the autonomous pieces
(survey, build-in-place, ledger incl. `decision` events, no `product/`) via an executed run where the
human picks are scripted/stubbed; (b) the checkpoint prompts + interactive entry via a guided manual
run. State-integrity + parallel single-writer remain mechanically asserted as before.

## Open questions

- **`decision` vs reuse:** add the `decision` event (chosen) vs. recording picks as `brainstorm_note`/
  `plan_created` by `actor: advisor`. Current choice: a dedicated `decision` event for a clean audit.
- **Build-choice memory:** ask every Implementation phase, or remember the user's pick for the project
  (e.g. in `hamilton.json`)? Current lean: ask each Implementation entry; allow "use this for the rest."
- **Auto-detect size:** how aggressively the wizard recommends a crew size from a vague brief.
