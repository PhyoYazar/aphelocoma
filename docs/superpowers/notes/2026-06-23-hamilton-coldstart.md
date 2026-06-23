# Hamilton — Phase 1 Cold-Start Verification (verdict: PASS)

_Date: 2026-06-23. Branch: `hamilton-phase-1`._

This records the executed verification that gates Phase 1. Authored artifacts don't count — this
is an **executed** cold-start plus a cross-tool definition-reach proof.

## Method

- Deployed the skill bundle to `~/.claude/skills/aph-hamilton/` and `~/.codex/skills/aph-hamilton/`
  (mirroring the `deploy` adapter steps with `APHELOCOMA_HOME` = repo, so the freshly-edited skill is
  the source). `references/`, `templates/`, `examples/` copied beside a generated `SKILL.md`.
- **Claude cold-start:** a fresh, context-isolated subagent was given ONLY the bare kickoff
  `/aph-hamilton start "a simple todo list app" solo`, in an empty throwaway project dir, told to
  invoke the skill through its own skill mechanism and resolve the definition itself (not fed the
  path). It ran the full protocol loop unaided.
- **Codex reach:** a real `codex exec` (gpt-5.5, read-only) read the deployed `SKILL.md`, followed
  its "Locating the definition" wording, and self-resolved `references/` with no `CLAUDE_SKILL_DIR`.

## Deploy defect found and fixed (the cold-start earned its keep)

The first deploy generated an `argument-hint` frontmatter line that was **invalid YAML** (value
starts with `[` → parsed as a flow sequence, then hit the `:` in `custom:[roles]`). Effect: the skill
was **silently dropped from the registry on BOTH platforms** — Codex logged `failed to load skill`,
and a fresh Claude subagent's skill listing omitted `aph-hamilton`. Fix: match the adapter exactly —
Claude gets a **single-quoted** `argument-hint`, Codex gets **none** (the documented Codex deploy path
doesn't add it). Re-deployed; Codex then listed the skill with no load error. (Follow-up: harden
`skills/deploy/skill.md` to quote `argument-hint` so any skill whose args start with `[` is safe.)

## Cross-tool definition reach — PASS on both

- **Codex:** `REACH=OK` — resolved `/Users/.../.codex/skills/aph-hamilton/references/`, read
  `PROTOCOL.md` (Hamilton header), `VERSION` (1.0.0), 27 role files — derived from the injected
  `SKILL.md` path, no env var, no hardcoded path.
- **Claude:** definition reachable beside `SKILL.md`; `${CLAUDE_SKILL_DIR}` resolves to the install dir.

## Cold-start checks a–e — PASS (mechanical assertions on the produced files)

Throwaway project: `…/scratchpad/cold-start-claude/`.

- **(a) Bootstraps `.aphelocoma/`** — `hamilton.json`, `state/{tasks,brief,roadmap}.md/json`,
  `ledger/events.jsonl`, `ledger/agents/{cto,fullstack-developer}.md`, `specs/T1.md` all present.
- **(b) Reads the installed definition + records the version pin** —
  `hamilton.json.definition_version = 1.0.0` == installed `references/VERSION` (1.0.0).
- **(c) Schema-valid ledger + strictly monotonic `seq`** — 24 events, every line has the 7 required
  keys, all event types within the PROTOCOL §5 vocabulary, `seq` 1..24 with no gaps or repeats.
- **(d) §7 coverage applied unprompted** — `solo` has no QA/DevOps; `cto` emitted `review_passed`
  (seq 19, "CTO covering QA (§7)") and the DevOps integration check (seq 21), and covered
  software-architect/engineering-manager during breakdown (seq 12–13). Honest `assumption_logged`
  at seq 24 discloses the one approximate event-label choice (§5).
- **(e) Completes the loop** — `phase: done`, `project_completed` logged (seq 23); product at
  `product/todo.html` (46 lines, implements add/list/complete/remove) — in the **project**, not
  inside `.aphelocoma/`.

## Minor (non-blocking) observations → fold into Task 9

- The agent-written `state/brief.md` used the heading "Company size" (legacy label). The shipped
  template uses "Crew size"; the stale `examples/todo-solo/` (old flat-layout, old vocabulary) is the
  likely model the agent copied. Refreshing the example (Task 9) removes that source.

## Verdict

**Phase 1 PASS** — portable thin+global-ref Hamilton bootstraps and runs end-to-end from a fresh
agent given only the kickoff, reads its installed definition, keeps a schema-valid monotonic ledger,
applies §7 coverage unprompted, and records the version pin — with cross-tool definition reach proven
on **both** Claude and Codex.
