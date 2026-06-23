Spin up / resume / inspect a Hamilton crew that builds software for the current project. Argument: $ARGUMENTS

## What this is

Hamilton is a portable, file-based **crew** of role-agents (CTO, software-architect, developers, QA,
DevOps, …). Leadership roles brainstorm → plan → roadmap → assign; implementers build; every action
is appended to a file ledger so you can review who did what. Full rules live in the definition's
`PROTOCOL.md` (located below).

## Locating the Hamilton definition (read this first)

The definition — protocol, roles, sizes — is installed **once**, bundled **beside this SKILL.md** in
the skill's own install folder. Nothing is copied into projects. Resolve the install folder, call it
`<skill>`:

- **Claude Code:** `<skill>` = `${CLAUDE_SKILL_DIR}` → definition at `${CLAUDE_SKILL_DIR}/references/`.
- **Codex / other tools:** `${CLAUDE_SKILL_DIR}` is **not** set. `<skill>` is the directory **this
  SKILL.md was loaded from** (your tool gives you this skill file's path — use its parent). The
  definition is the `references/` folder beside this file, e.g. `~/.codex/skills/aph-hamilton/references/`.

From `<skill>`, these are fixed:
- **Definition (read-only):** `<skill>/references/` — `PROTOCOL.md`, `roles/<id>.md`, `sizes.yaml`,
  `roles.index.md`, `settings.example.yaml`, `VERSION` are siblings inside it.
- **Per-project skeleton:** `<skill>/templates/aphelocoma/` — copied into the project at `start`.
- **Per-project state (read/write):** `./.aphelocoma/` in the **current project** — never in the definition.
- **The product:** the project proper — repo root, or `./product`. Never inside `.aphelocoma/`.

Background: `<skill>/references/ABOUT.md`. Example run: `<skill>/examples/todo-solo/`.

## Modes (parse from `$ARGUMENTS`)

### `start "<brief>" <size>`
1. Read `<skill>/references/PROTOCOL.md` (the operating rules) and resolve `<size>` from
   `<skill>/references/sizes.yaml` (`solo | startup | mid | big | custom:[role-id,…]`). The preset
   (or explicit custom list) gives the **active role list**.
2. Create per-project state: copy `<skill>/templates/aphelocoma/` → `./.aphelocoma/` in the current
   project (leaves `.aphelocoma/ledger/events.jsonl` empty so `seq` starts at 1).
3. Write `./.aphelocoma/hamilton.json`: `project` (slug from the brief / directory name), `size`, the
   active `roles`, `definition_version` (read verbatim from `<skill>/references/VERSION`), `created`
   (ISO-8601 now), `phase: "kickoff"`.
4. Run the protocol (Kickoff → Discovery → Plan & Roadmap → Breakdown & Assign → Implementation →
   Review/QA → Integration), adopting one role at a time by reading `<skill>/references/roles/<id>.md`.
   Build the product in the project. Keep `./.aphelocoma/state/tasks.json` current and append every
   action to `./.aphelocoma/ledger/` (events.jsonl + agents/<role>.md) per PROTOCOL §3/§5. Apply §7
   role coverage when the chosen size lacks a role a phase needs.

### `resume`
Read `./.aphelocoma/`. Compare `hamilton.json.definition_version` with `<skill>/references/VERSION`:
if they differ, **warn** (definition drift) and let the user choose to continue — if they do, log an
`assumption_logged` event noting the version gap. Then report the current `phase` and open tasks
(anything not `done`) from `./.aphelocoma/state/tasks.json`, and continue per PROTOCOL §6.

### `status`
Print the current `phase` and the open/closed tasks from `./.aphelocoma/state/tasks.json`, plus the
last few `./.aphelocoma/ledger/events.jsonl` entries. Read-only — no state changes.

### `sync-agents`  (Phase 2 — Claude Code only; not yet implemented)
Generate `.claude/agents/<role>.md` for the **active** roles, **derived from**
`<skill>/references/roles/`, so a manager role can dispatch implementers as native **parallel**
subagents with orchestrator-owned state (the manager is the single writer of `tasks.json` +
`events.jsonl`). Regenerable; never hand-edited. On non-Claude platforms, skip this and run the
sequential file-based role-play that is the portable default.

## Notes
- Optional per-project config: `./.aphelocoma/settings.yaml` (role→model map, `parallel_dispatch`
  toggle), modeled on `<skill>/references/settings.example.yaml`. Hamilton runs fine without it.
- The definition is shared and read-only. Do not edit `<skill>/references/` while running a project
  (PROTOCOL §7 "Stay in lane").
