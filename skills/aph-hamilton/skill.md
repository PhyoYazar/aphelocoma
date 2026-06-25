Spin up / resume / inspect a Hamilton crew that builds software for the current project. Argument: $ARGUMENTS

## What this is

Hamilton is a portable, file-based **crew** of role-agents (CTO, software-architect, developers, QA,
DevOps, …). **You are the advisor:** the leadership core brainstorms *with you*, you decide the
direction/plan/build-style at four checkpoints, and the crew builds it autonomously. Every action is
appended to a file ledger so you can review who did what. Full rules live in the definition's
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
  `sizes.yaml`, `roles.index.md`, `settings.example.yaml`, `agent-template.md` are siblings inside it.
- **Per-project skeleton:** `<skill>/templates/aphelocoma/` — copied into the project at `start`.
- **Per-project state (read/write):** `./.aphelocoma/` in the **current project** — never in the definition.
- **The product:** the project itself — at the repo root, beside `.aphelocoma/`, structured however the work needs (no forced `product/` folder). Never inside `.aphelocoma/`.

Background: `<skill>/references/ABOUT.md`. Example run: `<skill>/examples/todo-solo/`.

## Modes (parse from `$ARGUMENTS`)

### (no arguments) — guided start (the default)
When `$ARGUMENTS` is empty, run a short guided start:
1. **Detect context:** is there existing code in this directory? Does `./.aphelocoma/` already exist?
   If `.aphelocoma/` exists, report the in-progress project (phase + open tasks) and offer **`resume`**
   instead of starting over.
2. **Ask:** "New project, or work on this existing one?" then "What do you want to build / add / fix?"
   (plain words; vague is fine — the crew brainstorms it out with you).
3. Bootstrap `./.aphelocoma/` and begin the **advisor flow** (`start` steps 3–4): the leadership core
   activates and discussion begins, including the **Foundations pass** — the six cross-cutting topics
   from `<skill>/references/FOUNDATIONS.md` (deploy, fault-tolerance, security, UX, observability,
   accessibility) and the **TDD default** (on unless you opt out for a PoC). **Crew size is chosen
   after Discovery (Checkpoint 1) — not here.**

### `start "<brief>" <size>`  (fast path — skips the wizard)
For when the advisor already knows the brief; otherwise use the bare `/aph-hamilton` wizard above.
1. Read `<skill>/references/PROTOCOL.md`. If `./.aphelocoma/` already exists, STOP and offer `resume`
   (never overwrite). Otherwise copy `<skill>/templates/aphelocoma/` → `./.aphelocoma/` (leaves
   `ledger/events.jsonl` empty so `seq` starts at 1).
2. Write `./.aphelocoma/hamilton.json`: `project` (slug from the brief / directory name), `created`
   (ISO-8601 now), `phase: "kickoff"`. (Roles + size are filled in after Discovery — step 4.)
3. **Kickoff:** activate only the **leadership core** (`cto`, `software-architect`, `product-manager`;
   `solo` → `cto` covers all per §7). Log `role_activated` each.
4. Run the protocol as the **advisor flow** (PROTOCOL §1.5) — adopt one role at a time from
   `<skill>/references/roles/<id>.md`, and **pause at the four checkpoints**, each presenting 2–3
   options with trade-offs and waiting for the advisor (log a `decision`, `actor: advisor`):
   - **Checkpoint 1 (after Discovery):** run the **Foundations pass** (the six topics in
     `<skill>/references/FOUNDATIONS.md` + confirm the TDD default), then present directions + a
     recommended crew size; the advisor picks both; then activate the chosen implementer/specialist
     roles and record the size + foundations + TDD choice in `brief.md` + `tasks.json`. (If `<size>`
     was given on the command line, propose it as the recommendation; the advisor still confirms.)
   - **Checkpoint 2 (after Plan & Roadmap):** advisor approves / reorders / cuts / adds.
   - **Checkpoint 3 (before Implementation):** if parallel is possible (Claude Code + ≥2 disjoint
     `assigned` tasks) ask the advisor *subagents or one session?*; else build sequentially.
   - **Checkpoint 4 (at Review):** advisor accepts, or says what to fix / add.
   Build the product **in the project (at the repo root, beside `.aphelocoma/`)** — no `product/`. Keep
   `./.aphelocoma/state/tasks.json` current and append every action to `./.aphelocoma/ledger/`
   (events.jsonl + agents/<role>.md) per PROTOCOL §3/§5. Apply §7 coverage. Between checkpoints work
   autonomously; the advisor may interject anytime.
   - **Parallel build (Checkpoint 3 = "subagents"):** dispatch disjoint `assigned` tasks as parallel
     subagents and serialize results per `<skill>/references/PARALLEL.md` — you stay the single writer
     of `tasks.json` + `events.jsonl`. If a generated `hamilton-<role>` agent isn't selectable as a
     subagent type yet, dispatch a generic subagent with that agent file's content injected.

### `resume`
Read `./.aphelocoma/`. Report the current `phase` and open tasks (anything not `done`) from
`./.aphelocoma/state/tasks.json`, and continue per PROTOCOL §6.

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
Each generated agent embeds the single-writer contract: it writes only the project files + its own
`.aphelocoma/ledger/agents/<role>.md` and returns a structured result; the orchestrator is the sole
writer of `.aphelocoma/state/tasks.json` + `.aphelocoma/ledger/events.jsonl`.

**Non-Claude platforms:** print "sync-agents is Claude-Code-only; running sequentially" and generate
nothing — the run still works via sequential role-play (PROTOCOL §3 / `PARALLEL.md` Fallback).

## Notes
- Optional per-project config: `./.aphelocoma/settings.yaml` (role→model map, `parallel_dispatch`
  toggle), modeled on `<skill>/references/settings.example.yaml`. Hamilton runs fine without it.
- The definition is shared and read-only. Do not edit `<skill>/references/` while running a project
  (PROTOCOL §7 "Stay in lane").
