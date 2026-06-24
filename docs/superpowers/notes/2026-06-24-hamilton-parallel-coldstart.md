# Hamilton — Phase 2 Parallel Cold-Start Verification (verdict: PASS)

_Date: 2026-06-24. Branch: `hamilton-phase-1`. Definition version: 1.1.0._

Gate for Phase 2 (native parallel agents): an **executed** parallel run proving the
orchestrator-owned-state model keeps shared state race-free. Run against the **repo** definition
(deployment is the user's; the definition content deploys identically — proven in Phase 1).

## Method

A throwaway project was bootstrapped mid-run (orchestrator had done kickoff→breakdown; seed ledger
`seq` 1..10) with **two disjoint `assigned` tasks**: T1 → `product/page-a.html` (owner
`fullstack-developer#1`), T2 → `product/page-b.html` (owner `fullstack-developer#2`). Then:

1. **`sync-agents` (real generation):** filled `references/agent-template.md` per the documented steps
   to produce `./.claude/agents/hamilton-fullstack-developer-1.md` and `-2.md` — validated: valid
   frontmatter, embedded single-writer contract, return-JSON schema, inlined canonical role, per-
   instance log path `fullstack-developer#1.md`, `MODEL_LINE` omitted cleanly.
2. **Parallel dispatch (real concurrency):** both implementer subagents were dispatched in ONE batch
   (overlapping wall-clock, ~85s & ~71s). Each read its generated agent file + spec, built its file,
   wrote its own role log, and returned the structured result.
3. **Orchestrator serialize (single writer):** the orchestrator appended the collected events to
   `events.jsonl` (monotonic `seq`) and updated `tasks.json`, then ran the §7-covered review/
   integration to `done`.

## The decisive safety proof

**After both parallel subagents finished, before the orchestrator wrote anything:**
- `.aphelocoma/ledger/events.jsonl` was **still at `seq` 10** — the subagents never appended.
- `.aphelocoma/state/tasks.json` still showed **both tasks `assigned`** — the subagents never mutated
  the board.
- Yet each subagent HAD produced its own outputs: disjoint `product/page-{a,b}.html`, its own
  `ledger/agents/fullstack-developer#{1,2}.md`, and its `_inbox` result.

Because the only writer of the two shared-mutable files is the orchestrator (serial), the
"two-appenders-corrupt-the-ledger" race **cannot occur** — and the run demonstrates the subagents
respect that contract under genuine concurrency.

## Gate assertions — PASS

- **(a) Schema-valid + strictly monotonic, gap-free `seq` 1..22** — no duplicate or lost line despite
  concurrent work.
- **(b) ≥2 parallel implementers** — `work_started` by `fullstack-developer#1` and `#2`.
- **(c) No lost task updates** — both T1/T2 `done`, both reviewed, `phase: done`.
- **(d) §7 coverage unprompted** — no `qa-engineer` active, so `engineering-manager` emitted
  `review_passed` (seq 18–19).
- **(e) Completion** — `project_completed` logged.
- **Sequential fallback intact** — PROTOCOL §1 keeps sequential as the guaranteed baseline and skill.md
  keeps "otherwise build sequentially"; the Phase-1 solo cold-start already exercised that path, and
  the Phase-2 changes are additive/opt-in (no change to the sequential branch).

## Scope / honesty

- **Orchestrator = the top-level agent (here, the main session).** This is faithful to the design —
  the orchestrator is always the skill-running top-level agent, never a subagent. The **implementers
  were genuine fresh parallel subagents**; the concurrency (and the single-writer safety it stresses)
  is real. The serialization step is deterministic file I/O performed exactly as `PARALLEL.md`
  prescribes.
- **Repo definition, not deployed `~/.claude`.** Install-location resolution is Phase 1's concern
  (already proven on both tools); Phase 2 tests concurrency/state-integrity, which is independent of
  where the definition lives. The user's deploy + Phase-1's wholesale-copy proof cover the install path.
- The `_inbox/<task>.result.json` files are a test-harness convenience for reliable result collection;
  in a live run the orchestrator reads each subagent's returned JSON directly.

## Verdict

**Phase 2 PASS** — `sync-agents` generates correct native role-agents from the canonical roles, and the
orchestrator-owned-state model runs implementers as real parallel subagents while keeping the shared
board and append-only ledger schema-valid and gap-free-monotonic. Sequential role-play remains the
guaranteed, unchanged default.
