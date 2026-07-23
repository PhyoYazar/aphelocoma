# PARALLEL — orchestrator-owned-state parallelism

This document defines Hamilton's parallel execution — the **default** wherever a dispatch backend
exists (PROTOCOL §1), with sequential as the guaranteed fallback. It stays **additive**: Hamilton MUST
remain fully runnable sequentially (PROTOCOL §1, §3). Parallel is the default only when ALL of these
hold; otherwise run sequentially:

1. a **dispatch backend** is available (see "Dispatch backends" below): native subagents on Claude
   Code, or headless CLI workers on Codex (`DISPATCH-CODEX.md` preflight passes), AND
2. the backend's role definitions are reachable — on Claude Code the native crew agents, generated
   globally at `/deploy` (`~/.claude/agents/hamilton-<role>.md`) or per-project by
   `/aph-hamilton sync-agents`; on Codex the bundled definition itself (`roles/`, `agent-template.md`,
   the `result.*.schema.json` files ship beside this file, so this holds whenever the skill is
   installed), AND
3. there are ≥2 `assigned` tasks whose specs' **Interfaces / files touched** (PROTOCOL §4) are
   **disjoint** and whose inputs are already `done`.

When these hold, parallel is the **default** (the advisor may still pick one sequential session at CP3).
If any condition fails, the manager works the tasks one at a time per PROTOCOL §3. Never require
parallelism.

## Dispatch backends

The loop below is backend-agnostic: only *how a worker is launched* (step 2) and *how its result JSON
travels back* differ. The contract (step 3) and the collect/serialize rules (step 4) are identical.

- **Claude Code — native subagents.** Dispatch each task to its `hamilton-<role>` agent; the result
  JSON arrives as the subagent's tool result.
- **Codex — headless workers (default), collab tools (opt-in/fallback).** Fan out one background
  `codex exec` per task, role body injected into the prompt and `--output-schema` pinned to the result
  schema; the result JSON arrives as a file at `.aphelocoma/dispatch/<task-id>/result.json`. The
  experimental collab tools (`spawn_agent`/`wait_agent`) are used only when `dispatch: collab` is set
  or the exec preflight fails. Selection order, mechanics, preflight, flags, and labeling rules:
  `DISPATCH-CODEX.md`.
- **Anything else** — no backend: sequential fallback (below).

## The one safety rule: a single writer for shared state

Two files are **shared mutable state** and have exactly **one writer — the orchestrator** (the active
manager role running the Implementation phase):

- `.aphelocoma/state/tasks.json` — the live board.
- `.aphelocoma/ledger/events.jsonl` — the append-only history (`seq` must stay monotonic, gap-free).

**Dispatched subagents NEVER write those two files.** They write only:

- their deliverables in the project (within their spec's `files touched`), and
- their own human-readable log at `.aphelocoma/ledger/agents/<role-id>.md` — and for a role with
  multiple instances, `<role-id>#<N>.md` (e.g. `fullstack-developer#2.md`), so two instances never
  write the same file.

Parallel work on disjoint files + a single writer for the board and ledger ⇒ no races.

## The loop

### 1. Select
The manager picks a batch of `assigned` tasks that are mutually disjoint in `files touched` and whose
dependencies are `done`. Tasks that overlap or depend on an unfinished task are deferred to a later
batch (or run sequentially).

### 2. Dispatch (parallel)
The manager dispatches each selected task to its owner's worker **in one batch** (all at once), passing
each worker its `<task-id>`, via the platform backend:

- **Claude Code:** the task's **native `hamilton-<role>` subagent**. Native agents make the fleet view
  show the role and apply that role's model/effort/tools (the look-only reviewer included). Only if the
  crew agents are missing, fall back to a generic subagent with the role file's content injected — this
  shows as `general-purpose` and loses the role label, per-role effort, and tool-scoping.
- **Codex:** per `DISPATCH-CODEX.md`'s selection order — by default a background `codex exec` worker
  per task (role body injected; per-role model/effort as flags; reviewers sandboxed read-only;
  concurrency capped by `max_parallel`); collab-tool spawns (role-labeled, `agent_type` when defined)
  only on the opt-in/fallback rungs.

Each worker runs the single-role turn (PROTOCOL §3 d–e) for its task only.

### 3. Subagent contract (what each dispatched role does and returns)
Each subagent:
- reads its task spec `.aphelocoma/specs/<task-id>.md`, `.aphelocoma/state/conventions.md` (when
  written), and the relevant project context;
- never runs git — commits belong to the orchestrator alone (PROTOCOL §5.5);
- produces its deliverable in the project, staying within the spec's `files touched`;
- appends its turn to `.aphelocoma/ledger/agents/<role-id[#N]>.md` (its own file);
- **does NOT touch `.aphelocoma/state/tasks.json` or `.aphelocoma/ledger/events.jsonl`**;
- **returns exactly this JSON as its result** (no prose around it):

```json
{
  "task": "<task-id>",
  "role": "<role-id[#N]>",
  "status": "in_review",
  "artifacts": ["<path>", "..."],
  "events": [
    {"event": "work_started",     "to": null,              "note": "<text>"},
    {"event": "artifact_written", "to": null,              "note": "<text>"},
    {"event": "handoff",          "to": "<reviewer-role>", "note": "<text>"}
  ],
  "blocked_reason": null
}
```

If the subagent cannot complete the task, it returns `"status": "blocked"`, a populated
`"blocked_reason"`, whatever `artifacts` exist, and a single `{"event":"blocked", ...}` entry.

### 4. Collect + serialize (single writer)
After all workers in the batch return (on Codex: after the batch's processes exit and their result
files are read — `DISPATCH-CODEX.md` "Collect"), the orchestrator processes the results **serially, in
ascending `task` order** (deterministic). For each result:
- **(replay safety)** first check the ledger tail: if this task's `work_started`/`artifact_written`
  events from this dispatch are already there (an interruption hit between appending and finishing the
  batch), the result was already serialized — **skip it**, don't re-append. This is PROTOCOL §7
  idempotency applied to events; it makes crash-resume safe;
- append every entry in `events[]` to `.aphelocoma/ledger/events.jsonl`, assigning the next `seq`
  (read the current last line; increment by 1 per append) and stamping `ts`, `actor` = the result's
  `role`, and `task` = the result's `task`;
- (visibility) annotate the `work_started` entry's note with the dispatched agent + its model/effort, so
  the ledger is an audit of which model ran which task;
- update that task in `.aphelocoma/state/tasks.json`: set `status` (→ `in_review`, or back to
  `assigned` on `blocked`), record `artifacts`, refresh `updated`.

**Scope check (after the batch, when the project is a git repo).** Disjointness is *declared* in specs;
verify it actually held: compare the files that changed during the batch (a `git diff --name-only`
against the last Hamilton commit — PROTOCOL §5.5 — or `git status --porcelain` when there is none) with
the union of the batch specs' **Interfaces / files touched**. Any
changed file outside that union → log a `scope_violation` event (actor = the responsible role, note =
the stray file + owning spec) and make sure the CP4 review of the affected tasks sees it. A violation is
a review flag, not an automatic revert — the reviewer and advisor decide.

Because only the orchestrator appends to the ledger and edits the board, `seq` stays strictly
monotonic and no task update is lost — even though the work happened concurrently.

### 5. Continue
The orchestrator advances to the next batch, then to Review/QA (PROTOCOL §2 Phase 5). Review is itself a
single-role turn (the qa-engineer or a covering role per §7), run by the orchestrator. It may be
parallelized across independent `in_review` tasks under the same rules — each reviewer worker uses the
**reviewer contract** (read-only: a `hamilton-<reviewer>` agent on Claude Code, a
`codex exec --sandbox read-only` worker on Codex; returns findings + a `pass`/`fail` verdict, writes
nothing), and the orchestrator logs the `critique` + `review_passed`/`review_failed` per
task (CRITIQUE.md; PROTOCOL §2 Phase 5).

## Failure & honesty
- A `blocked` result leaves its task `assigned`; the orchestrator logs the `blocked` event and
  continues the other results — one blocked task never corrupts the batch.
- All the PROTOCOL §7 honesty rules still apply: §7 role coverage, `assumption_logged` disclosure, and
  "a task is `done` only when its acceptance criteria are met" are unchanged under parallelism.

## Fallback (the portable default)
If parallelism is not enabled (any of the three conditions unmet), the manager runs each task as a
normal sequential single-role turn (PROTOCOL §3) and writes state inline. The output — board, ledger,
specs, product — is identical in shape to a parallel run; only the wall-clock differs.
