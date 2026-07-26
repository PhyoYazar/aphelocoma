Spin up / resume / inspect a Hamilton crew that builds software for the current project. Argument: $ARGUMENTS

## What this is

Hamilton is a portable, file-based **crew** of role-agents (CTO, software-architect, developers, QA,
DevOps, …). **You are the advisor:** the leadership core brainstorms *with you*, you decide the
direction/plan/build-style at four checkpoints, and the crew builds it autonomously — **in parallel by
default on Claude Code** (native role-agents) **and Codex** (headless `codex exec` workers —
`references/DISPATCH-CODEX.md`), sequentially everywhere else. Before you see the
work at Checkpoints 1, 2, and 4, an **independent reviewer** double-checks it (`references/CRITIQUE.md`) and logs a `critique` —
catching blind spots, plan holes, and code defects — and implementers write to a standing **craft bar**
(`references/CRAFT.md`: simplicity, consistency, error handling). Every action is appended to a file
ledger so you can review who did what. Full rules live in the definition's `PROTOCOL.md` (located below).

## Locating the Hamilton definition (read this first)

The definition — protocol, roles, sizes — is installed **once**, bundled **beside this SKILL.md** in
the skill's own install folder. Nothing is copied into projects. Resolve the install folder, call it
`<skill>`:

- **Claude Code:** `<skill>` = `${CLAUDE_SKILL_DIR}` → definition at `${CLAUDE_SKILL_DIR}/references/`.
- **Codex / other tools:** `${CLAUDE_SKILL_DIR}` is **not** set. `<skill>` is the directory **this
  SKILL.md was loaded from** (your tool gives you this skill file's path — use its parent). The
  definition is the `references/` folder beside this file, e.g. `~/.codex/skills/aph-hamilton/references/`.

From `<skill>`, these are fixed:
- **Definition (read-only):** `<skill>/references/` — `PROTOCOL.md`, `PARALLEL.md`,
  `DISPATCH-CODEX.md`, `roles/<id>.md`, `sizes.yaml`, `roles.index.md`, `settings.example.yaml`,
  `agent-template.md`, `result.implementer.schema.json`, `result.reviewer.schema.json`,
  `state.schema.json`, `FOUNDATIONS.md`, `CRITIQUE.md`, `CRAFT.md`, `validate.py`, and `migrate.py`
  are siblings inside it.
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
1. Read `<skill>/references/PROTOCOL.md`. If `./.aphelocoma/` already exists, inspect its version
   fields and STOP (never overwrite): offer `resume` when schema `1` / protocol `1.0.0` is current,
   or the explicit backed-up migration below when it is unversioned v0.2 state. A future version must
   stop with "upgrade Aphelocoma"; never interpret or downgrade it. Otherwise copy
   `<skill>/templates/aphelocoma/` → `./.aphelocoma/` (leaves `ledger/events.jsonl` empty so `seq`
   starts at 1).
2. Write `./.aphelocoma/hamilton.json`: retain `schema_version: 1` and
   `protocol_version: "1.0.0"` from the template; fill `project` (slug from the brief / directory
   name), `created` (ISO-8601 now), and `phase: "kickoff"`. Roles + size are filled in after Discovery.
3. **Kickoff:** activate only the **leadership core** (`cto`, `software-architect`, `product-manager`;
   `solo` → `cto` covers all per §7). Log `role_activated` each.
4. Run the protocol as the **advisor flow** (PROTOCOL §1.5) — adopt one role at a time from
   `<skill>/references/roles/<id>.md`, and **pause at the four checkpoints**, each presenting 2–3
   options with trade-offs and waiting for the advisor (log a `decision`, `actor: advisor`):
   - **Checkpoint 1 (after Discovery):** run the **Foundations pass** (the six topics in
     `<skill>/references/FOUNDATIONS.md` + confirm the TDD default), then present directions + a
     recommended crew size; the advisor picks both; then activate the chosen implementer/specialist
     roles and record the size + foundations + TDD choice in `brief.md` + `tasks.json`, and — with the
     stack now picked — have the architect write `state/conventions.md` (the binding project
     conventions; PROTOCOL §2 Phase 1). (If `<size>`
     was given on the command line, propose it as the recommendation; the advisor still confirms.)
   - **Checkpoint 2 (after Plan & Roadmap):** advisor approves / reorders / cuts / adds.
   - **Checkpoint 3 (before Implementation):** parallel subagents is the **default** where possible
     (a dispatch backend per `PARALLEL.md` — Claude Code crew agents, or Codex `codex exec` with its
     preflight passing — plus ≥2 disjoint `assigned` tasks) — note it and let the advisor opt for one
     sequential session; else sequential.
   - **Checkpoint 4 (at Review):** advisor accepts, or says what to fix / add.
   **Review gate — applies at CP1/CP2/CP4, do not skip:** the independent reviewer should not be the agent
   that built the work — use a fresh subagent or the host's own review tool (e.g. `advisor`); a persona
   self-review is the floor only when neither exists. A review counts ONLY when you log a `critique` event
   for it (record the tier). At CP4 every task is reviewed **individually** (a fresh per-task subagent is
   the right tier — the host tool reviews the whole context, not one task) and reaches `done` only once
   its `critique` + `review_passed` are in the ledger. The CP4 critique actor must differ from the
   builder. No `critique` event = it didn't happen.
   Build the product **in the project (at the repo root, beside `.aphelocoma/`)** — no `product/`. Keep
   `./.aphelocoma/state/tasks.json` current and append every action to `./.aphelocoma/ledger/`
   (events.jsonl + agents/<role>.md) per PROTOCOL §3/§5. **Git (PROTOCOL §5.5):** the orchestrator is
   the only committer — commit on the checked-out branch at kickoff, checkpoints, and once per `done`
   task; never branch or push (the advisor owns those). Apply §7 coverage. Between checkpoints work
   autonomously; the advisor may interject anytime.
   - **Parallel build (the default at Checkpoint 3):** dispatch disjoint `assigned` tasks to their
     native `hamilton-<role>` subagents (generated at `/deploy` — real role names + per-role
     model/effort/tools) and serialize results per `<skill>/references/PARALLEL.md` — you stay the single
     writer of `tasks.json` + `events.jsonl`. Only if the crew agents are missing, fall back to generic
     subagents with the role content injected (they show as `general-purpose` and lose per-role effort +
     tool-scoping). **On Codex**, dispatch per `<skill>/references/DISPATCH-CODEX.md`'s selection
     order: headless `codex exec` workers by default (role body injected, result contract enforced via
     `--output-schema`, reviewers sandboxed read-only); the experimental collab tools only via
     `dispatch: collab` or as the fallback when exec preflight fails (then label every spawn with its
     role and narrate by role, not thread id). On platforms with no backend, build sequentially.

### `resume`
Read `./.aphelocoma/`. **Version + integrity check first:** run
`python3 <skill>/references/validate.py .` (skip silently only if `python3` is unavailable). Current
schema `1` / protocol `1.0.0` continues. Unversioned v0.2 state must stop and offer
`python3 <skill>/references/migrate.py check .` then `... migrate.py apply .`; apply retains a
recoverable backup and rolls back on any failed validation. An unsupported future version must stop
and tell the advisor to upgrade Aphelocoma. The validator also checks event references/transitions,
reviewer independence/order, task IDs/specs, tracked transient data, and representative credentials.
It mechanically enforces `state.schema.json`; schema documentation is never merely advisory.
Report findings before continuing; fix ledger/state drift as new corrective events (never rewrite
history — PROTOCOL §5). Then print the **progress board** and write it to `.aphelocoma/STATUS.md`
(PROTOCOL §5.6) at the top of the resume — `aph status . --write` is the fast path; render and write it
yourself if `aph` is unavailable or older than §5.6 — and continue per PROTOCOL §6. The board is
printed and written the same way after each `task_completed` commit, on `blocked`, and on
`review_failed`.
Hit a bug or want a change? Just say so — it becomes a tracked **fix task** routed to the owning role
(PROTOCOL §6.5), not a side channel.

### `status`
**Fast path: `aph status .`** (add `--json` for the complete machine-readable form). It prints the
PROTOCOL §5.6 progress board: the project name, the current `phase`, the done/total count, and one line
per task with its id, status **as a word**, and title — so a `blocked` task reads as blocked in its own
row. Owners, dependencies, versions, visibility, the next actionable task, and the repo situation stay
in `--json`. `aph status . --write` additionally regenerates `.aphelocoma/STATUS.md`, the same board in
a file the advisor can open any time. Exit `1` means no `./.aphelocoma/` or an unsupported version,
with the remediation printed. If `aph` is missing, fails, or is older than §5.6, render the same board
yourself from `./.aphelocoma/hamilton.json` + `./.aphelocoma/state/tasks.json` and name any field you
could not determine.

Then add what the board does not cover: the last few `./.aphelocoma/ledger/events.jsonl` entries and
the active crew's `role → model → effort → tools` table (from the generated agents / the applicable
settings). Also run the integrity check (`python3 <skill>/references/validate.py .`, skip if no
`python3`) and include its verdict. Do not silently inspect unversioned or unsupported-future state;
report the same migration/upgrade remediation as `resume`.
Read-only — no state changes.

### `sync-agents`  (Claude Code only — per-project override)
The standard crew is generated **globally at `/deploy`** (`~/.claude/agents/hamilton-<role>.md`), so most
runs already have native agents and need this command only to **override models/effort for one project**
(via that project's `./.aphelocoma/settings.yaml`). It regenerates that project's crew so the
orchestrator can dispatch implementers as native **parallel** subagents (see
`<skill>/references/PARALLEL.md`). Steps:
1. Read the active roles from `./.aphelocoma/hamilton.json`.
2. For each active role (one per instance — `<role-id>`, or `<role-id>#N` for repeats), fill
   `<skill>/references/agent-template.md`: `{{ROLE_ID}}`, `{{AGENT_NAME}}` (`hamilton-<role-id>`,
   `#`→`-`), `{{ROLE_TITLE}}` (the `title:` from the role's frontmatter), `{{ROLE_BODY}}` (the verbatim
   text of `<skill>/references/roles/<role-id>.md`), `{{TOOLS_LINE}}` (`tools: <list>` from the role's
   frontmatter `tools:` if present — read-only reviewer roles like `qa-engineer` drop `Write`/`Edit` —
   else the default `tools: Read, Write, Edit, Bash, Grep, Glob`), `{{MODEL_LINE}}`/`{{EFFORT_LINE}}` from
   `./.aphelocoma/settings.yaml` (omit each when unlisted → the agent inherits the session). Use the
   **reviewer** body for look-only roles (no `Write`/`Edit`), the **implementer** body otherwise
   (`agent-template.md` defines both).
3. Write each generated file to `./.claude/agents/<AGENT_NAME>.md` in the current project.
4. Print a **crew table** — `role → agent name → model → effort → tools` — so the models/effort are
   visible at a glance.
5. **Tell the advisor to restart the session** (then `/aph-hamilton resume`): Claude Code loads agent
   files only at session start, so a freshly regenerated project crew is dispatchable only after a
   restart. (The global `/deploy` crew needs no restart — it is already loaded.)

Regenerable — rerun after any role or settings change; **never hand-edit** the generated files (they are
derived). Each generated agent embeds the single-writer contract: it writes only the project files + its
own `.aphelocoma/ledger/agents/<role>.md` and returns a structured result; the orchestrator is the sole
writer of `.aphelocoma/state/tasks.json` + `.aphelocoma/ledger/events.jsonl`.

**Non-Claude platforms:** generate nothing here. On **Codex**, print "sync-agents is Claude-Code-only;
the Codex crew is generated globally by `aph deploy codex` (named `[agents.hamilton-*]` roles), and
per-project model/effort overrides in `.aphelocoma/settings.yaml` apply at dispatch time
(DISPATCH-CODEX.md) — no per-project regeneration or restart needed". On other platforms, print
"running sequentially" — the run still works via sequential role-play (PROTOCOL §3 / `PARALLEL.md`
Fallback).

## Notes
- Per-project `./.aphelocoma/settings.yaml` declares required privacy fields
  (`visibility: tracked|local`, `redact_sensitive: true`); model, effort, dispatch, and concurrency
  overrides remain optional. It is modeled on `<skill>/references/settings.example.yaml`.
- `.aphelocoma/dispatch/`, prompts, worker results, temporary files, backups, and logs are transient
  in both visibility modes and never enter durable state. Durable notes contain only compact redacted
  summaries — never raw prompts or credentials.
- Migration backups remain recoverable but untrackable: Git projects store them under the repository's
  Git metadata (`.git/aphelocoma-backups/`, including the resolved gitdir for worktrees); non-Git
  projects use a clearly named sibling backup.
- The definition is shared and read-only. Do not edit `<skill>/references/` while running a project
  (PROTOCOL §7 "Stay in lane").
