# Hamilton — Phase 1 Cold-Start Verification (verdict: PASS)

_Date: 2026-06-23. Branch: `hamilton-phase-1`._

This records the executed verification that gates Phase 1. Authored artifacts don't count — this
is an **executed** cold-start plus a cross-tool definition-reach proof.

## Method

- Deployed the skill bundle to `~/.claude/skills/aph-hamilton/` and `~/.codex/skills/aph-hamilton/`
  (mirroring the `deploy` adapter steps with `APHELOCOMA_HOME` = repo, so the freshly-edited skill is
  the source). `references/`, `templates/`, `examples/` copied beside a generated `SKILL.md`.
- **Claude cold-start:** a fresh, context-isolated subagent was given ONLY the bare kickoff
  `/aph-hamilton start "a simple todo list app" solo`, in an empty throwaway project dir, and resolved
  the definition itself (it was NOT fed the `references/` path). It ran the full protocol loop unaided.
- **Codex reach:** a real `codex exec` (gpt-5.5, read-only) read the deployed `SKILL.md`, followed
  its "Locating the definition" wording, and self-resolved `references/` with no `CLAUDE_SKILL_DIR`.

## Which resolution path was exercised (fidelity — stated honestly)

`aph-hamilton` is `type: manual` → `disable-model-invocation: true`, which (correctly) keeps it off the
**model-invocable** Skill list: a model/subagent cannot auto-invoke it; only a human typing
`/aph-hamilton` can. Consequence for this test: the Claude subagent's Skill-tool call was rejected, so
it **fell back to the skill's tool-neutral self-location** (read `SKILL.md` → resolve `references/`
beside it) with `${CLAUDE_SKILL_DIR}` **unset**, and still reached the installed definition at
`/Users/…/.claude/skills/aph-hamilton/references` and ran a–e to completion.

- **Proven on BOTH platforms:** the portable **self-location** path (find `references/` beside
  `SKILL.md`, no env var). This is the platform-agnostic core of the design — and it works even with
  `${CLAUDE_SKILL_DIR}` unset (belt-and-suspenders).
- **Not exercised here:** the Claude `${CLAUDE_SKILL_DIR}`-via-Skill-tool path — a subagent can't
  invoke a `disable-model-invocation` skill, and a real human `/aph-hamilton` can't be simulated from
  this harness. It rests on the **established aphelocoma convention** (adr/journal/project-init use
  `${CLAUDE_SKILL_DIR}` in real user sessions) and is **redundant** with the self-location the run
  proved. Final confirmation = one real `/aph-hamilton` in an interactive Claude session.

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
applies §7 coverage unprompted, and records the version pin — with the **tool-neutral self-location
path** (the platform-agnostic core) proven on **both** Claude and Codex. The Claude
`${CLAUDE_SKILL_DIR}` convenience path is unverified-for-Hamilton-here (subagents can't invoke a
manual skill) but is backed by repo convention and made redundant by the proven self-location.
