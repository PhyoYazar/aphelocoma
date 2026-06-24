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
- **Definition (read-only):** `<skill>/references/` — `PROTOCOL.md`, `PARALLEL.md`, `roles/<id>.md`,
  `sizes.yaml`, `roles.index.md`, `settings.example.yaml`, `agent-template.md`, `VERSION` are siblings
  inside it.
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

### `sync-agents`  (Claude Code only)
Generate native role-agents so the orchestrator can dispatch implementers as **parallel** subagents
(see `<skill>/references/PARALLEL.md`). Steps:
1. Read the active roles from `./.aphelocoma/hamilton.json`.
2. For each active role (one per instance — `<role-id>`, or `<role-id>#N` for repeats), fill
   `<skill>/references/agent-template.md`: `{{ROLE_ID}}`, `{{AGENT_NAME}}` (`hamilton-<role-id>`,
   `#`→`-`), `{{ROLE_TITLE}}` (the `title:` from the role's frontmatter), `{{ROLE_BODY}}` (the verbatim
   text of `<skill>/references/roles/<role-id>.md`), and `{{MODEL_LINE}}` (`model: <model>` if
   `.aphelocoma/settings.yaml` `models:` maps this role or a `default`, else omit the line).
3. Write each generated file to `./.claude/agents/<AGENT_NAME>.md` in the current project.

Regenerable — rerun after any role change; **never hand-edit** the generated files (they are derived).
Each generated agent embeds the single-writer contract: it writes only `product/` + its own
`.aphelocoma/ledger/agents/<role>.md` and returns a structured result; the orchestrator is the sole
writer of `.aphelocoma/state/tasks.json` + `.aphelocoma/ledger/events.jsonl`.

**Non-Claude platforms:** print "sync-agents is Claude-Code-only; running sequentially" and generate
nothing — the run still works via sequential role-play (PROTOCOL §3 / `PARALLEL.md` Fallback).

## Notes
- Optional per-project config: `./.aphelocoma/settings.yaml` (role→model map, `parallel_dispatch`
  toggle), modeled on `<skill>/references/settings.example.yaml`. Hamilton runs fine without it.
- The definition is shared and read-only. Do not edit `<skill>/references/` while running a project
  (PROTOCOL §7 "Stay in lane").
