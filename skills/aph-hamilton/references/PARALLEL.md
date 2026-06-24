# PARALLEL — orchestrator-owned-state parallelism

This document defines Hamilton's **optional** parallel execution. It is **additive**: Hamilton MUST
remain fully runnable sequentially (PROTOCOL §1, §3). Parallelism is enabled only when ALL of these
hold; otherwise run sequentially:

1. the platform can spawn subagents (e.g. Claude Code), AND
2. `.aphelocoma/settings.yaml` sets `parallel_dispatch: true`, AND
3. native role-agents have been generated (`/aph-hamilton sync-agents`), AND
4. there are ≥2 `assigned` tasks whose specs' **Interfaces / files touched** (PROTOCOL §4) are
   **disjoint** and whose inputs are already `done`.

If any condition fails, the manager works the tasks one at a time per PROTOCOL §3. Never require
parallelism.

## The one safety rule: a single writer for shared state

Two files are **shared mutable state** and have exactly **one writer — the orchestrator** (the active
manager role running the Implementation phase):

- `.aphelocoma/state/tasks.json` — the live board.
- `.aphelocoma/ledger/events.jsonl` — the append-only history (`seq` must stay monotonic, gap-free).

**Dispatched subagents NEVER write those two files.** They write only:

- their deliverables under `product/` (within their spec's `files touched`), and
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
The manager dispatches each selected task to its owner role's subagent **in one batch** (all at once),
passing that subagent its `<task-id>`. Each subagent runs the single-role turn (PROTOCOL §3 d–e) for
its task only.

### 3. Subagent contract (what each dispatched role does and returns)
Each subagent:
- reads its task spec `.aphelocoma/specs/<task-id>.md` and the relevant `product/` context;
- produces its deliverable under `product/`, staying within the spec's `files touched`;
- appends its turn to `.aphelocoma/ledger/agents/<role-id[#N]>.md` (its own file);
- **does NOT touch `.aphelocoma/state/tasks.json` or `.aphelocoma/ledger/events.jsonl`**;
- **returns exactly this JSON as its result** (no prose around it):

```json
{
  "task": "<task-id>",
  "role": "<role-id[#N]>",
  "status": "in_review",
  "artifacts": ["product/<path>", "..."],
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
After all subagents in the batch return, the orchestrator processes the results **serially, in
ascending `task` order** (deterministic). For each result:
- append every entry in `events[]` to `.aphelocoma/ledger/events.jsonl`, assigning the next `seq`
  (read the current last line; increment by 1 per append) and stamping `ts`, `actor` = the result's
  `role`, and `task` = the result's `task`;
- update that task in `.aphelocoma/state/tasks.json`: set `status` (→ `in_review`, or back to
  `assigned` on `blocked`), record `artifacts`, refresh `updated`.

Because only the orchestrator appends to the ledger and edits the board, `seq` stays strictly
monotonic and no task update is lost — even though the work happened concurrently.

### 5. Continue
The orchestrator advances to the next batch, then to Review/QA (PROTOCOL §2.5). Review is itself a
single-role turn (the qa-engineer or a covering role per §7) and is run by the orchestrator (it may be
parallelized across independent `in_review` tasks under the same rules).

## Failure & honesty
- A `blocked` result leaves its task `assigned`; the orchestrator logs the `blocked` event and
  continues the other results — one blocked task never corrupts the batch.
- All the PROTOCOL §7 honesty rules still apply: §7 role coverage, `assumption_logged` disclosure, and
  "a task is `done` only when its acceptance criteria are met" are unchanged under parallelism.

## Fallback (the portable default)
If parallelism is not enabled (any of the four conditions unmet), the manager runs each task as a
normal sequential single-role turn (PROTOCOL §3) and writes state inline. The output — board, ledger,
specs, product — is identical in shape to a parallel run; only the wall-clock differs.
