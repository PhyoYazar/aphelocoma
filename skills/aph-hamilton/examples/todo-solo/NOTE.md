# About this example

`todo-solo/` is a **real, executed reference run** of Hamilton, shipped with the skill so you can see
exactly what a run writes and where. It is not part of any live project.

## Provenance

Produced on 2026-06-23 by handing a **fresh, context-isolated agent** only the user-level kickoff —
nothing else:

> `/aph-hamilton start "a simple todo list app" solo`

The agent located the installed definition on its own, bootstrapped `.aphelocoma/`, and ran the full
protocol loop (Kickoff → Discovery → Plan & Roadmap → Breakdown & Assign → Implementation → Review/QA
→ Integration → done) unaided. This run is the Phase-1 cold-start verification; the full verdict is in
`docs/superpowers/notes/2026-06-23-hamilton-coldstart.md`.

## Layout (the two layers)

- `.aphelocoma/` — the per-project state Hamilton creates in the project:
  - `hamilton.json` — project, schema/protocol versions, size, active roles, phase.
  - `settings.yaml` — explicit tracked visibility and sensitive-data redaction policy.
  - `state/` — `tasks.json` (live board), `roadmap.md`, `brief.md`, and binding `conventions.md`.
  - `specs/T1.md` — the handoff contract (goal, scope, files, acceptance criteria).
  - `ledger/events.jsonl` — append-only history (25 events, `seq` 1..25, schema per PROTOCOL §5).
  - `ledger/agents/{cto,fullstack-developer}.md` — the same history per role, human-readable.
- `todo.html` — the actual product, built **in the project** (not inside `.aphelocoma/`).

## What to notice

- **§7 role coverage.** `solo` activates only `cto` + `fullstack-developer`, so the `cto` covers the
  missing roles and says so: software-architect + engineering-manager during breakdown (seq 12–13), QA
  at review (`critique` + `review_passed`, seq 19–20), and DevOps at integration (seq 22).
- **Honest disclosure (§5).** Seq 25 is an `assumption_logged` event in which the `cto` flags that the
  integration check at seq 22 reused the `artifact_written` event type (the vocabulary has no
  dedicated integration/readiness type) — the check was real; only the label is approximate.

> The shipped copy is normalized to current state schema 1 / protocol 1.0.0: explicit privacy settings
> and dependency fields were added, and the CTO's recorded independent QA pass is represented by the
> required `critique` event before `review_passed`. The original product artifact is unchanged.
