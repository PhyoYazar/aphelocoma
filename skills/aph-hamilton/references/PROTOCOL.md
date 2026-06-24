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
- **The product** (the software being built) lives in the **project proper** — the repo
  root, or a `product/` subdirectory. Below, `product/` names that location.
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
  `.aphelocoma/ledger/events.jsonl`, while each subagent writes only `product/` + its own
  `.aphelocoma/ledger/agents/<role>.md` and returns a structured result. The enabling conditions,
  dispatch loop, and result schema are in `PARALLEL.md`. Generate the agents with
  `/aph-hamilton sync-agents`.
- The system MUST remain fully runnable sequentially. Never require parallelism.

## 2. Phases

Run these in order. Skip a phase only if no active role covers it (see §7 coverage). On each
transition, set `.aphelocoma/state/tasks.json`'s `phase` and log a `phase_advanced` event (note `from`→`to`).
Canonical `phase` values, one per step below: `kickoff`, `discovery`, `planning`, `breakdown`,
`implementation`, `review`, `integration`, `done`.

0. **Kickoff** — Read the user's brief. Choose a **crew size** (`sizes.yaml`) or a
   custom role list. Write `.aphelocoma/state/brief.md` (brief, size, activated roles, start time),
   initialize `.aphelocoma/state/tasks.json` (project, size, `phase: discovery`, seed tasks empty).
   Activate only the selected roles. Log `role_activated` per activated role.
1. **Discovery / Brainstorm** — Leadership/product roles (ceo, cto, product-manager,
   business-analyst, software-architect as available) capture goals, constraints, risks,
   and requirements. Log `brainstorm_note` entries.
2. **Plan & Roadmap** — Leadership produces `.aphelocoma/state/roadmap.md`: milestones and sequence.
   Log `plan_created` / `roadmap_updated`.
3. **Breakdown & Assign** — Architect/leads turn the roadmap into tasks. For each task:
   create an entry in `.aphelocoma/state/tasks.json` AND write `.aphelocoma/specs/<task-id>.md` with the handoff
   contract (§4). The engineering-manager (or top active manager) sets each task's
   `owner`. Log `task_created` then `task_assigned`.
4. **Implementation** — Each owner role picks up its `assigned` tasks, builds under
   `product/`, records artifacts, and moves the task to `in_review`. Log `work_started`,
   `artifact_written`, then update status (see §3). If parallel dispatch is enabled and ≥2
   `assigned` tasks have disjoint file scopes, the manager dispatches them concurrently per
   `PARALLEL.md`; otherwise it works them one at a time.
5. **Review / QA** — qa-engineer (or covering role) checks each `in_review` task against
   its acceptance criteria. Pass → status `done`, log `review_passed`. Fail → status back
   to `assigned`/`in_progress` with notes, log `review_failed`. Repeat until done.
6. **Integration** — devops/sre/cloud (if active) integrate, build, and judge readiness.
   When all roadmap tasks are `done` and integration passes, set `phase: done` and log `project_completed`.

## 3. Single-role turn protocol

Every unit of work is one role-turn. Do these steps in order:

a. **Adopt the role** — read `roles/<role-id>.md`. Act only within that role's mission.
b. **Read state** — read `.aphelocoma/state/tasks.json`, the relevant `.aphelocoma/specs/<task-id>.md`, and the
   tail of `.aphelocoma/ledger/events.jsonl` for recent context.
c. **Check idempotency** (§7) — if the task is already `done`, skip it.
d. **Do the work** — produce the role's outputs.
e. **Write outputs** — code/docs under `product/`; specs under `.aphelocoma/specs/`. Record file
   paths in the task's `artifacts[]`.
f. **Update live state** — edit `.aphelocoma/state/tasks.json` (status, owner, artifacts, `updated`).
g. **Append history** — append one JSON line per event to `.aphelocoma/ledger/events.jsonl` AND a
   human-readable entry to `.aphelocoma/ledger/agents/<role-id>.md`.
h. **Hand off** — per the role's "Hands off to". Logging a `handoff` (or `task_assigned`)
   makes the next role's work discoverable.

## 4. Handoff contract (`.aphelocoma/specs/<task-id>.md`)

A task is only assignable once its spec exists. Every spec MUST contain:

- **Goal** — what this task achieves, in one or two sentences.
- **Scope / Non-scope** — what is and isn't included.
- **Interfaces / files touched** — the surfaces or files under `product/` involved.
- **Acceptance criteria** — a concrete checklist the reviewer (QA) will verify. Each item
  must be objectively checkable.

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
  `phase_advanced`, `project_completed`.
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
- **Stay in lane** — role work builds the *product* under `product/`. Do not modify
  Hamilton's own definition files (`references/`) while running a project unless explicitly asked.

## 8. Quick reference — status lifecycle

`pending → assigned → in_progress → in_review → done`
(`blocked` reachable from any state; return to `assigned`/`in_progress` on `review_failed`.)
