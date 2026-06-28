# CRITIQUE — the double-check rubric (read-only)

Before each of the three work-output checkpoints, an **independent reviewer** double-checks the crew's
work, so blind spots, plan holes, and quality defects are caught before they reach the advisor. This is
distinct from `adapters/claude-code/agents/reviewer.md` (a code-diff reviewer reused only as the CP4 code
lens below).

Run a critique before **CP1** (brainstorm), **CP2** (plan), and **CP4** (implementation). **Never CP3** —
it chooses a build style, with no artifact to review.

## Operating rules

- **Independent — and always logged.** Prefer a reviewer that is *not* the agent that produced the work;
  use the most independent tier your platform offers:
  - a fresh-context **subagent** (Claude Code) — read-only on state, returns findings (`tier: subagent`);
    the genuine second pair of eyes, and the right tier for **per-task CP4**;
  - the host's own **review tool** (e.g. Claude Code's `advisor`), pointed at the artifact + the relevant
    lens below (`tier: host_tool`) — independent of the builder, best for the holistic **CP1/CP2** passes
    (it reviews the whole context, so it does not scope cleanly to one task);
  - a **persona pass** — the same agent adopts the reviewer hat, a checklist self-review (`tier: persona`)
    — the **floor**, used ONLY when neither of the above exists (e.g. `solo` on a platform without
    subagents). It is a self-review by construction, so on Claude Code prefer `host_tool` even in `solo`.
  Whichever you use, the review counts ONLY when the orchestrator writes a `critique` event for it
  (PROTOCOL §5), recording the tier and verdict. **No `critique` event = the review did not happen:** do
  not present at a checkpoint, and do not move a task to `done`, until that event exists.
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

Every `in_review` task gets its own CP4 critique, and the reviewer is **never** that task's builder.
Pass → log `critique` + `review_passed` → `done`. Serious findings → `review_failed` → one bounce-back to
the owner, then surface at CP4. A task may not reach `done` until both its `critique` and `review_passed`
events exist.
