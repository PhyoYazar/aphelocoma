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

- **Baseline (always works): sequential single-agent role-play.** One agent becomes one
  role at a time. This is the guaranteed mode on any platform.
- **Optional acceleration: parallel subagents (Claude Code).** When enabled, a manager role
  dispatches independent implementer tasks to subagents in parallel under **orchestrator-owned
  state**: the manager is the *single writer* of `.aphelocoma/state/tasks.json` +
  `.aphelocoma/ledger/events.jsonl`, while each subagent writes only the project files + its own
  `.aphelocoma/ledger/agents/<role>.md` and returns a structured result. The enabling conditions,
  dispatch loop, and result schema are in `PARALLEL.md`. Generate the agents with
  `/aph-hamilton sync-agents`.
- The system MUST remain fully runnable sequentially. Never require parallelism.

## 1.5 Advisor model (human-in-the-loop)

A **human advisor** (the user) steers every decision; the crew does all the building. The advisor
occupies the top seat — ledger `actor: advisor`. The crew **pauses at four checkpoints**, each time
presenting 2–3 options with trade-offs (or targeted questions) and a recommendation, then waits:

1. **After Discovery** — the advisor picks the product **direction** AND the **crew size** (leadership
   recommends a size from what Discovery revealed; see §2). The directions are presented *with their
   foundation implications* (from the §2 Phase 1 Foundations pass), and the TDD default is confirmed here.
2. **After Plan & Roadmap** — the advisor approves / reorders / cuts / adds.
3. **Before Implementation** — the advisor picks the build style (subagents vs one session; §1).
4. **At Review** — the advisor accepts, or says what to fix / add.

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
   End at **Checkpoint 1**: present 2–3 product
   **directions** with trade-offs AND a **recommended crew size/shape**; the advisor picks both (log a
   `decision`). THEN activate the chosen implementer/specialist roles (`role_activated`) and record the
   size in `brief.md` + `tasks.json`.
2. **Plan & Roadmap** — Leadership produces `.aphelocoma/state/roadmap.md`: milestones and sequence. The roadmap MUST show
   each of the six foundations (§2 Phase 1 Foundations pass) as **addressed** (how/when) or **consciously
   deferred** (why) — this is how they stay visible instead of forgotten.
   Log `plan_created` / `roadmap_updated`. End at **Checkpoint 2**: the advisor approves / reorders /
   cuts / adds (log a `decision`).
3. **Breakdown & Assign** — Architect/leads turn the roadmap into tasks. For each task:
   create an entry in `.aphelocoma/state/tasks.json` AND write `.aphelocoma/specs/<task-id>.md` with the handoff
   contract (§4). The engineering-manager (or top active manager) sets each task's
   `owner`. Log `task_created` then `task_assigned`.
4. **Implementation** — Begin at **Checkpoint 3**: if parallel is possible (Claude Code + ≥2 `assigned`
   tasks with disjoint file scopes), ask the advisor *subagents or one session?* and log a `decision`;
   otherwise build sequentially. Each owner role picks up its `assigned` tasks, builds **in the project
   (at the repo root, beside `.aphelocoma/`)**, records artifacts, and moves the task to `in_review`.
   Log `work_started`, `artifact_written`, then update status (see §3). Parallel dispatch follows
   `PARALLEL.md`.
5. **Review / QA** — qa-engineer (or covering role) checks each `in_review` task against its acceptance
   criteria. Pass → status `done`, log `review_passed`. Fail → status back to `assigned`/`in_progress`
   with notes, log `review_failed`. End at **Checkpoint 4**: the advisor accepts, or says what to fix /
   add (log a `decision`); fixes loop back as re-assigned tasks.
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
  `phase_advanced`, `project_completed`, `decision`.
- The **`advisor`** actor is the human (the user) in the top seat; it appears on `decision` events
  (the options offered + the pick) and on any direction the human gives. Crew actors are role-ids.
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
- **Stay in lane** — role work builds the *product* in the project (beside `.aphelocoma/`). Do not
  modify Hamilton's own definition files (`references/`) while running a project unless explicitly asked.

## 8. Quick reference — status lifecycle

`pending → assigned → in_progress → in_review → done`
(`blocked` reachable from any state; return to `assigned`/`in_progress` on `review_failed`.)
