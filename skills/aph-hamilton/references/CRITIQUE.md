# CRITIQUE — the double-check rubric (read-only)

Before each of the three work-output checkpoints, an **independent reviewer** double-checks the crew's
work, so blind spots, plan holes, and quality defects are caught before they reach the advisor. This is
distinct from `adapters/claude-code/agents/reviewer.md` (a code-diff reviewer reused only as the CP4 code
lens below).

Run a critique before **CP1** (brainstorm), **CP2** (plan), and **CP4** (implementation). **Never CP3** —
it chooses a build style, with no artifact to review.

## Operating rules

- **Independent.** The reviewer must not be the agent that produced the work. Tier: a fresh-context
  **subagent** on Claude Code; on platforms without subagents, a **persona pass** (the running agent
  adopts the reviewer hat — roughly a checklist self-review). The achieved tier is logged on the
  `critique` event (PROTOCOL §5).
- **Floor, not ceiling.** Flag genuine *defects* against the rubric, not polish. Severity-tag each
  finding: **blocking** / **should-fix** / **nit**.
- **Authority = advisory + one bounce-back.** Serious (blocking) findings go back to the owning role
  **once** to fix; then the work + findings + fixes surface to the advisor at the checkpoint regardless.
  One cycle only — it cannot loop. The advisor always makes the final call.
- **Read-only on state.** The reviewer writes nothing — not even its own ledger file. It returns
  findings; the orchestrator logs the `critique` event, records the reviewer's ledger note, and updates
  state (single-writer contract, `PARALLEL.md`). On Claude Code the generated reviewer agent is
  tool-scoped to look-only (`Read, Grep, Glob, Bash` — no `Write`/`Edit`), so this is enforced at the
  tool level, not by prose alone.

## CP1 · Brainstorm  (read brief.md + Discovery notes)

- Blind spots **beyond** the six FOUNDATIONS topics (deploy, fault-tolerance, security, UX,
  observability, accessibility)?
- Unstated assumptions presented as fact? Any scope **fabricated** vs. advisor-confirmed?
- Are the proposed directions genuinely **distinct** (not three flavors of one)?
- Any defining question left unasked? Internal **contradictions** in goals/constraints/risks?

## CP2 · Plan  (read roadmap.md + tasks.json)   — the net-new gap; most attention

- Does **every roadmap item trace to a stated goal**? Does **every goal have at least one item**?
- Is each of the six foundations shown as **addressed or consciously deferred** (not silently dropped)?
- Are **dependencies sequenced** (nothing scheduled before its prerequisite)?
- Is **anything unowned**? Are milestones achievable / not missing an obvious step?

## CP4 · Implementation  (per in_review task) — this IS the Review/QA pass, done independently

- **Acceptance criteria** — every criterion in the task spec actually met? When **TDD is on**: tests
  written first, they pass, and they actually exercise the behavior.
- **Craft bar** (`CRAFT.md`) — error handling on plausible paths; consistency with existing patterns;
  simplicity/YAGNI — applying the precedence.
- **Code lens** (reuses `reviewer.md`) — logic / edge / off-by-one, contract or API breaks, security
  basics.

Pass → `review_passed` → `done`. Serious findings → `review_failed` → one bounce-back to the owner, then
surface at CP4.
