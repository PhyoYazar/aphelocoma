# PROTOCOL — How the Hamilton crew runs

This document is the operating manual for **Hamilton** — a portable, file-based crew of
role-agents. Any coding agent can run the crew by reading this file and following it. It
depends on **no platform-specific features** — only the ability to read and write files.

## 0. Mental model

- **Hamilton's definition** (this protocol, the `roles/`, and `sizes.yaml`) is installed
  once and read-only. Paths named bare below — `roles/<id>.md`, `sizes.yaml`,
  `roles.index.md` — are **siblings of this file inside the definition** (the skill's
  `references/`).
- **Per-project state** lives in a `.aphelocoma/` folder in the project you are building.
  Paths below that begin `.aphelocoma/…` are there.
- **The product** (the software being built) lives in the **project itself — at the repo root,
  beside `.aphelocoma/`**, structured however the work needs. `.aphelocoma/` is the ONLY directory
  Hamilton owns; there is no forced `product/` subfolder.
- You, the running agent, **adopt one role at a time** (see `roles/`), do that role's
  work, record it, and hand off — exactly like an employee.
- Two records are kept and must never be conflated:
  - **Live state** — `.aphelocoma/state/tasks.json` (+ `.aphelocoma/state/roadmap.md`,
    `.aphelocoma/state/brief.md`): the *current* truth (what exists, who owns what, status).
  - **History** — `.aphelocoma/ledger/events.jsonl` (+ `.aphelocoma/ledger/agents/<role>.md`):
    an *append-only* record of what happened. See §5.

## 1. Execution model

- **Default on Claude Code: parallel subagents.** When the platform can spawn subagents and the native
  crew agents exist (generated at `/deploy`, or per-project via `/aph-hamilton sync-agents`),
  Implementation runs in parallel by default: a manager role dispatches independent implementer tasks to
  native `hamilton-<role>` subagents under **orchestrator-owned state** — the manager is the *single
  writer* of `.aphelocoma/state/tasks.json` + `.aphelocoma/ledger/events.jsonl`, while each subagent
  writes only the project files + its own `.aphelocoma/ledger/agents/<role>.md` and returns a structured
  result. Conditions, dispatch loop, and result schema are in `PARALLEL.md`.
- **Baseline / fallback (always works): sequential single-agent role-play.** One agent becomes one role
  at a time — the guaranteed mode on any platform, the automatic fallback when subagents or the crew
  agents are unavailable, and selectable whenever the advisor prefers it (CP3).
- The system MUST remain fully runnable sequentially. **Parallelism is the default where available, but
  never required** — non-Claude platforms and missing-agent cases run sequentially with identical output.

## 1.5 Advisor model (human-in-the-loop)

A **human advisor** (the user) steers every decision; the crew does all the building. The advisor
occupies the top seat — ledger `actor: advisor`. The crew **pauses at four checkpoints**, each time
presenting 2–3 options with trade-offs (or targeted questions) and a recommendation, then waits:

1. **After Discovery** — the advisor picks the product **direction** AND the **crew size** (leadership
   recommends a size from what Discovery revealed; see §2). The directions are presented *with their
   foundation implications* (from the §2 Phase 1 Foundations pass), and the TDD default is confirmed here.
2. **After Plan & Roadmap** — the advisor approves / reorders / cuts / adds.
3. **Before Implementation** — the build style. **Parallel subagents is the default** where available
   (§1); the advisor may opt for one sequential session instead.
4. **At Review** — the advisor accepts, or says what to fix / add.

Before CP1, CP2, and CP4 an **independent reviewer** — a fresh subagent or the host's own review tool
(e.g. Claude Code's `advisor`), or a persona self-review only when neither exists — double-checks the
crew's work against `CRITIQUE.md` (blind spots at brainstorm, holes at plan, defects at implementation),
**always recorded as a `critique` event** (§5). The work is presented to the advisor
*with* the reviewer's findings and any fixes (see §2 Phases 1/2/5). CP3 has no artifact, so no critique.
The reviewer's authority is **advisory + one bounce-back**; the advisor still decides.

Record each as a `decision` event: `actor: advisor`, `note` = the options offered + the choice (or
"delegated" if the advisor says "you decide" — then proceed with the recommendation). Between
checkpoints the crew works autonomously; the advisor may interject at any time. **Never fabricate
scope** — an unknown becomes a question to the advisor, not an assumption.

## 2. Phases

Run these in order. Skip a phase only if no active role covers it (see §7 coverage). On each
transition, set `.aphelocoma/state/tasks.json`'s `phase` and log a `phase_advanced` event (note `from`→`to`).
Canonical `phase` values, one per step below: `kickoff`, `discovery`, `planning`, `breakdown`,
`implementation`, `review`, `integration`, `done`.

0. **Kickoff** — Read the advisor's brief. Activate only the **leadership core** — `cto`,
   `software-architect`, `product-manager` (in `solo`, the `cto` covers all three per §7) — NOT a full
   crew size yet. Write `.aphelocoma/state/brief.md` (brief, advisor, start time) and initialize
   `.aphelocoma/state/tasks.json` (`phase: discovery`, seed tasks empty). Log `role_activated` per
   leadership role.
   Set the **TDD default**: write `TDD: on` in `.aphelocoma/state/brief.md` (the advisor may flip it off during Discovery for a throwaway/PoC — §1.5).
1. **Discovery / Brainstorm** — The leadership core works WITH the advisor: for a vague brief,
   **interview** the advisor (ask the defining questions; never fabricate scope); for an existing
   project, **survey the codebase first** (structure, key files, conventions) and log it. Capture
   goals, constraints, risks (`brainstorm_note`).
   **Foundations pass (always):** before Checkpoint 1, walk `FOUNDATIONS.md`'s six topics (deploy,
   fault-tolerance, security, UX, observability, accessibility) WITH the advisor — for a new project
   ask where each lands for v1; for an existing project assess each topic's current state after the
   survey. Record decisions in `brief.md` `## Foundations` (log `brainstorm_note`s). These are
   **advisory**: they shape the direction options and the crew-size recommendation (a foundation that
   matters may add a specialist owner, e.g. security → `appsec`, UX/accessibility → `uiux-designer`).
   Also confirm the **TDD** default (on unless the advisor opts out for a PoC); record it in `brief.md`
   `## TDD` and log a `decision`.
   **Brainstorm critique (before CP1):** an independent reviewer checks the captured direction, goals,
   and risks against `CRITIQUE.md`'s CP1 lens (blind spots beyond the six foundations, unstated
   assumptions, fabricated scope, whether the directions are distinct, unasked defining questions,
   contradictions). Serious findings bounce back **once** to leadership to address; then the work +
   findings are presented to the advisor. Log a `critique` event (§5).
   End at **Checkpoint 1**: present 2–3 product
   **directions** with trade-offs AND a **recommended crew size/shape**; the advisor picks both (log a
   `decision`). THEN activate the chosen implementer/specialist roles (`role_activated`) and record the
   size in `brief.md` + `tasks.json`.
2. **Plan & Roadmap** — Leadership produces `.aphelocoma/state/roadmap.md`: milestones and sequence. The roadmap MUST show
   each of the six foundations (§2 Phase 1 Foundations pass) as **addressed** (how/when) or **consciously
   deferred** (why) — this is how they stay visible instead of forgotten.
   Log `plan_created` / `roadmap_updated`. **Plan critique (before CP2):** an independent reviewer checks
   the roadmap against `CRITIQUE.md`'s CP2 lens — every item traces to a goal, every goal has ≥1 item, each
   of the six foundations is addressed or consciously deferred, dependencies are sequenced, nothing is
   unowned. Serious findings bounce back **once** to leadership; then plan + findings are presented. Log a
   `critique` event (§5). End at **Checkpoint 2**: the advisor approves / reorders /
   cuts / adds (log a `decision`).
3. **Breakdown & Assign** — Architect/leads turn the roadmap into tasks. For each task:
   create an entry in `.aphelocoma/state/tasks.json` AND write `.aphelocoma/specs/<task-id>.md` with the handoff
   contract (§4). The engineering-manager (or top active manager) sets each task's
   `owner`. Log `task_created` then `task_assigned`.
4. **Implementation** — Begin at **Checkpoint 3**: if parallel is possible (Claude Code + native crew
   agents + ≥2 `assigned` tasks with disjoint file scopes), **default to parallel subagents** — tell the
   advisor it's the default and let them opt for one sequential session instead; log the `decision`.
   Otherwise build sequentially. Each owner role picks up its `assigned` tasks, builds **in the project
   (at the repo root, beside `.aphelocoma/`)**, records artifacts, and moves the task to `in_review`.
   Implementers write code to the **craft bar** (`CRAFT.md`: error handling, consistency, simplicity —
   in that precedence) as a standing definition-of-done alongside the §4 acceptance criteria.
   Log `work_started`, `artifact_written`, then update status (see §3). Parallel dispatch follows
   `PARALLEL.md`.
5. **Review / QA (independent critique)** — the Review **is** an independent critique pass, not a layer
   after QA. qa-engineer (or covering role per §7) reviews **each** `in_review` task as a fresh-context
   reviewer — a fresh subagent on Claude Code (the right tier for per-task CP4), the host's own review
   tool (`tier: host_tool`), or, only when neither exists, a persona self-review (`tier: persona`, the
   floor) — independent of the builder wherever a subagent or host tool is available — against
   `CRITIQUE.md`'s CP4 lens:
   **(a)** its acceptance criteria (incl. tests-first when TDD is on), **(b)** the craft bar (`CRAFT.md`),
   and **(c)** the code lens (logic/edge/contract/security, reusing `reviewer.md`). Log a `critique` event
   (§5; tier recorded). Pass → status `done`, log `review_passed`. Serious findings → status back to
   `assigned`/`in_progress` with notes, log `review_failed`, **one** bounce-back to the owner. **No task
   moves to `done` until both its `critique` and `review_passed` events are in the ledger** (in `solo`
   without subagents, the persona self-review is the acknowledged floor; on Claude Code prefer
   `host_tool`). End at **Checkpoint 4**: the advisor accepts, or says
   what to fix / add (log a `decision`); fixes loop back as re-assigned tasks.
6. **Integration** — devops/sre/cloud (if active) integrate, build, and judge readiness.
   When all roadmap tasks are `done` and integration passes, set `phase: done` and log `project_completed`.

## 3. Single-role turn protocol

Every unit of work is one role-turn. Do these steps in order:

a. **Adopt the role** — read `roles/<role-id>.md`. Act only within that role's mission.
b. **Read state** — read `.aphelocoma/state/tasks.json`, the relevant `.aphelocoma/specs/<task-id>.md`, and the
   tail of `.aphelocoma/ledger/events.jsonl` for recent context.
c. **Check idempotency** (§7) — if the task is already `done`, skip it.
d. **Do the work** — produce the role's outputs.
e. **Write outputs** — code/docs in the project (at the repo root, beside `.aphelocoma/`); specs under
   `.aphelocoma/specs/`. Record file paths in the task's `artifacts[]`.
f. **Update live state** — edit `.aphelocoma/state/tasks.json` (status, owner, artifacts, `updated`).
g. **Append history** — append one JSON line per event to `.aphelocoma/ledger/events.jsonl` AND a
   human-readable entry to `.aphelocoma/ledger/agents/<role-id>.md`.
h. **Hand off** — per the role's "Hands off to". Logging a `handoff` (or `task_assigned`)
   makes the next role's work discoverable.

## 4. Handoff contract (`.aphelocoma/specs/<task-id>.md`)

A task is only assignable once its spec exists. Every spec MUST contain:

- **Goal** — what this task achieves, in one or two sentences.
- **Scope / Non-scope** — what is and isn't included.
- **Interfaces / files touched** — the surfaces or files in the project involved.
- **Acceptance criteria** — a concrete checklist the reviewer (QA) will verify. Each item
  must be objectively checkable.
- **Tests-first (when TDD is on)** — if `brief.md` `## TDD` is `on`, the acceptance criteria MUST
  include that tests for the task's behavior were written first and pass; QA verifies this at Review
  (§2 Phase 5). When TDD is `off` (e.g. a PoC), this requirement is skipped.

Vague handoffs are not allowed — "build the cart" without acceptance criteria is rejected
back to the author.

## 5. State vs history (do not conflate)

- `.aphelocoma/state/tasks.json` is the **single source of truth for current status**. Mutate it in
  place. Always refresh `updated` to an ISO-8601 timestamp.
- `.aphelocoma/ledger/events.jsonl` is **append-only history**. One JSON object per line:
  `{"ts":"<iso>","seq":<int>,"event":"<type>","actor":"<role-id>","task":"<id|null>","to":"<role-id|null>","note":"<text>"}`
  `seq` increases by 1 each append (read the last line to find the next). Never edit or
  delete a line; corrections are new events.
- Event types: `role_activated`, `brainstorm_note`, `plan_created`, `roadmap_updated`,
  `task_created`, `task_assigned`, `work_started`, `artifact_written`, `task_completed`,
  `review_passed`, `review_failed`, `blocked`, `assumption_logged`, `handoff`,
  `phase_advanced`, `project_completed`, `decision`, `critique`.
- The **`advisor`** actor is the human (the user) in the top seat; it appears on `decision` events
  (the options offered + the pick) and on any direction the human gives. Crew actors are role-ids.
- The **`reviewer`** actor marks an independent critique pass (§1.5); `critique` events use it. The
  `note` records the gate (CP1/CP2/CP4), the verdict (`clear` / `findings`), severity, and the
  independence **tier** — one of `subagent` (a fresh-context reviewer on Claude Code), `host_tool` (the
  host's own review feature, e.g. Claude Code's `advisor`, pointed at the artifact + lens), or `persona`
  (a self-review where neither is available) — so a real second-pair-of-eyes review is distinguishable
  from a self-review. `task` is null at CP1/CP2 (phase-level) and set at CP4 (per-task). At CP4 the
  `critique` event rides alongside the `review_passed` / `review_failed`, and a task reaches `done` ONLY
  once both exist.
- A role file's **Ledger rule** is *indicative, not an exclusive whitelist* — a role may emit
  any documented event its work legitimately requires (especially when covering another role
  per §7; e.g. a CTO covering QA logs `review_passed`).
- `.aphelocoma/ledger/agents/<role-id>.md` is the same history in human-readable form, per role —
  append timestamped bullet entries; never rewrite past entries.
- **Never reconstruct state from the log or vice versa.** They are written together (§3 f, g).

## 6. Resumability

On start, read `.aphelocoma/state/brief.md`:
- If it is the stub / `status: no-active-project` → fresh start; go to Phase 0.
- If it is populated → a project is in progress. Report the current `phase` and the open
  tasks (anything not `done`) from `.aphelocoma/state/tasks.json`, then **continue** from there. Do not
  restart or rebuild completed work.

## 7. Rules that keep runs honest

- **Idempotency** — before working a task, check its `status`; skip if `done`. Re-running
  Hamilton must not duplicate completed work or double-append the same event.
- **Role coverage** — if a phase needs a function with no active role (e.g. no QA in
  `solo`), the nearest active senior/leadership role covers it and notes that it did so.
  While covering, it emits the covered role's events (e.g. CTO covering QA → `review_passed`),
  regardless of its own role file's Ledger rule.
- **Disclosure** — never fabricate completion. If something is uncertain or assumed, log
  an `assumption_logged` event and proceed transparently. A task is `done` ONLY when all
  its acceptance criteria are met.
- **Independent review (always logged)** — the CP1/CP2 critique is dispatched by leadership (the
  always-active `cto` runs it; covers per role-coverage above), the CP4 critique by `qa-engineer` (or
  nearest senior under coverage), and the reviewer should be **independent of** the agent that built the
  work. Use the strongest reviewer the platform offers — a fresh read-only **subagent** (Claude Code), the
  host's own **review tool** (e.g. `advisor`; `tier: host_tool`), or, only when neither exists, a
  **persona pass** (a self-review — the floor) — but it counts only when
  the orchestrator logs a `critique` event for it; the reviewer never writes state itself (single-writer
  contract, `PARALLEL.md`). **No `critique` event means no review happened:** do not present at CP1/CP2,
  and do not move any task to `done` at CP4, until the matching `critique` (and, at CP4, `review_passed`)
  is in the ledger.
- **Stay in lane** — role work builds the *product* in the project (beside `.aphelocoma/`). Do not
  modify Hamilton's own definition files (`references/`) while running a project unless explicitly asked.

## 8. Quick reference — status lifecycle

`pending → assigned → in_progress → in_review → done`
(`blocked` reachable from any state; return to `assigned`/`in_progress` on `review_failed`.)
The **`in_review → done`** step is gated: it requires a logged `critique` **and** `review_passed`
(§2 Phase 5, §7) — from an independent reviewer (subagent or host tool) where one exists, or the persona
self-review floor in `solo` with neither. No shortcut to `done`.
