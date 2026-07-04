#!/usr/bin/env python3
"""Hamilton ledger/board integrity check (read-only, stdlib-only).

Usage:  python3 validate.py [project-dir]

Validates a project's `.aphelocoma/` state against the invariants in
PROTOCOL.md (§5 ledger schema, §7 honesty rules, §8 status gate):

  errors   — invariant violations (exit 1):
    * events.jsonl: unparsable line, missing required field, `seq` not
      gap-free-monotonic from 1
    * tasks.json: unreadable, invalid task `status`
    * a `done` task missing its `critique` or `review_passed` event
    * a task past `pending` with no spec file in .aphelocoma/specs/
  warnings — suspicious but not fatal (exit stays 0):
    * unknown event type / unknown phase value
    * consecutive duplicate events (possible double-append on resume)
    * a spec file without an "Acceptance criteria" section
    * a project past planning with conventions.md missing or still the stub

Exit codes: 0 = no errors, 1 = errors found, 2 = could not run.
The script never writes anything.
"""

import json
import sys
from pathlib import Path

EVENT_TYPES = {
    "role_activated", "brainstorm_note", "plan_created", "roadmap_updated",
    "task_created", "task_assigned", "work_started", "artifact_written",
    "task_completed", "review_passed", "review_failed", "blocked",
    "assumption_logged", "handoff", "phase_advanced", "project_completed",
    "decision", "critique", "bug_reported", "scope_violation",
}
REQUIRED_FIELDS = ("ts", "seq", "event", "actor")
STATUSES = {"pending", "assigned", "in_progress", "in_review", "done", "blocked"}
PHASES = {"kickoff", "discovery", "planning", "breakdown",
          "implementation", "review", "integration", "done"}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load_events(ledger_path):
    """Parse events.jsonl; report per-line problems; return the good events."""
    events = []
    prev = None
    expected_seq = 1
    for n, line in enumerate(ledger_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"events.jsonl:{n}: unparsable JSON ({e.msg})")
            continue
        for field in REQUIRED_FIELDS:
            if ev.get(field) is None:
                err(f"events.jsonl:{n}: missing required field '{field}'")
        seq = ev.get("seq")
        if isinstance(seq, int):
            if seq != expected_seq:
                err(f"events.jsonl:{n}: seq {seq}, expected {expected_seq} "
                    "(must be gap-free-monotonic from 1)")
            expected_seq = (seq if isinstance(seq, int) else expected_seq) + 1
        if ev.get("event") not in EVENT_TYPES and ev.get("event") is not None:
            warn(f"events.jsonl:{n}: unknown event type '{ev['event']}'")
        if prev is not None and all(
            prev.get(k) == ev.get(k) for k in ("event", "actor", "task", "note")
        ):
            warn(f"events.jsonl:{n}: duplicate of previous event "
                 f"('{ev.get('event')}', task {ev.get('task')}) — possible double-append")
        prev = ev
        events.append(ev)
    return events


def check_tasks(board, events, specs_dir):
    tasks = board.get("tasks") or []
    critiqued = {e.get("task") for e in events if e.get("event") == "critique"}
    passed = {e.get("task") for e in events if e.get("event") == "review_passed"}
    for t in tasks:
        tid = t.get("id", "<no-id>")
        status = t.get("status")
        if status not in STATUSES:
            err(f"tasks.json: task {tid}: invalid status '{status}'")
            continue
        if status != "pending":
            spec = specs_dir / f"{tid}.md"
            if not spec.is_file():
                err(f"tasks.json: task {tid} is '{status}' but has no spec "
                    f"({spec.relative_to(specs_dir.parent.parent)}) — §4 handoff contract")
            elif "acceptance criteria" not in spec.read_text().lower():
                warn(f"specs/{tid}.md: no 'Acceptance criteria' section (§4)")
        if status == "done":
            if tid not in critiqued:
                err(f"tasks.json: task {tid} is 'done' with no 'critique' event "
                    "— the §8 gate says no critique = no review happened")
            if tid not in passed:
                err(f"tasks.json: task {tid} is 'done' with no 'review_passed' event (§8 gate)")
    phase = board.get("phase")
    if phase is not None and phase not in PHASES:
        warn(f"tasks.json: unknown phase '{phase}'")
    if phase in {"breakdown", "implementation", "review", "integration", "done"}:
        conventions = specs_dir.parent / "state" / "conventions.md"
        if not conventions.is_file() or "no active project yet" in conventions.read_text().lower():
            warn(f"state/conventions.md missing or still the stub while phase is '{phase}' "
                 "— it should be written right after Checkpoint 1 (PROTOCOL §2 Phase 1)")
    return tasks


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    aph = root / ".aphelocoma"
    if not aph.is_dir():
        print(f"validate: no .aphelocoma/ in {root} — nothing to check", file=sys.stderr)
        return 2

    ledger_path = aph / "ledger" / "events.jsonl"
    tasks_path = aph / "state" / "tasks.json"

    events = []
    if ledger_path.is_file():
        events = load_events(ledger_path)
    else:
        warn("ledger/events.jsonl missing")

    tasks = []
    if tasks_path.is_file():
        try:
            board = json.loads(tasks_path.read_text())
            tasks = check_tasks(board, events, aph / "specs")
        except json.JSONDecodeError as e:
            err(f"state/tasks.json: unparsable JSON ({e.msg})")
    else:
        err("state/tasks.json missing")

    done = sum(1 for t in tasks if t.get("status") == "done")
    print(f"Hamilton validate — {root.name}: "
          f"{len(events)} events, {len(tasks)} tasks ({done} done)")
    for msg in errors:
        print(f"  ERROR {msg}")
    for msg in warnings:
        print(f"  WARN  {msg}")
    if errors:
        print(f"  {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"  OK — no errors ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
