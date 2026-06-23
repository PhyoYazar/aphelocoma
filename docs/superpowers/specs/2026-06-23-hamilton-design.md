# Hamilton — Design Spec

_Date: 2026-06-23_

## Context

**Hamilton** is a portable, file-based system where many role-agents (CTO, software architect,
frontend/backend/mobile developers, DevOps, SRE, data, security, QA, product, design, support, …)
collaborate to build software for a project: leadership roles brainstorm → plan → roadmap → assign,
implementers build, and every action is appended to a file ledger so you can review **who did what**.

A verified prototype already exists (built and **cold-start-tested** in the `ceo` repo): 27 role
files + a coordination `PROTOCOL.md` + size presets, proven followable by a fresh agent that ran a
full solo build of a todo app unaided.

**Problem being solved here:** the prototype lived as a `company/` folder that had to be **copied into
every project** — a template, not a tool. We want it **installed once, invoked anywhere**, bound to
aphelocoma and distributed through aphelocoma's existing `deploy` adapters (Claude Code, Codex, …).

## Decisions (locked with the user)

1. **Name: Hamilton** — after Margaret Hamilton (coined "software engineering"; led the Apollo
   flight-software team). The terms **"company" and "OS" are retired as brand labels**; use "crew" /
   "roles" descriptively. Command/skill: **`/aph-hamilton`**.
2. **Distribution = a module inside aphelocoma.** Reuse the existing `deploy` adapter pipeline; no new
   distribution layer. (Personal use, not packaged for third parties — hence aphelocoma-bound.)
3. **Thin + global ref.** The definition (roles + protocol + sizes) installs **once**, bundled with
   the skill and read at runtime via `${CLAUDE_SKILL_DIR}`. Each project gets only **thin per-project
   state** in a `.aphelocoma/` folder. **No vendored copies** of the definition.
4. **Version pin.** Each project records the `definition_version` it ran against (in
   `.aphelocoma/hamilton.json`) — a reproducibility *record* + drift detection, without the cost of
   vendoring. (Analogous to "built with engine vX.Y".)
5. **Native parallel agents: wanted, but Phase-2, opt-in, derived.** Generated from the canonical
   roles on demand (`/aph-hamilton sync-agents`) — never a hand-maintained second copy. On Claude Code
   they enable real parallel subagents (the value is **context isolation**, not just speed); on
   Codex/others, file-based role-play. Concurrency handled by **orchestrator-owned state** (below).
6. **Explicit invocation** (a skill), not auto-hook magic.

## Skill identity

- `name: aph-hamilton` · `type: manual`
- `arguments: "[start \"<brief>\" <size> | resume | status | sync-agents]"`
- See `skills/aph-hamilton/metadata.yaml`.

## Architecture — two layers + a bridge

- **Definition (install once)** — `references/{PROTOCOL.md, roles/, sizes.yaml, roles.index.md,
  VERSION}`, bundled with the skill, deployed per-tool, read at runtime via
  `${CLAUDE_SKILL_DIR}/references/…`.
- **Per-project state** — `.aphelocoma/{hamilton.json, state/, ledger/, specs/}` in the target
  project, created from `templates/aphelocoma/`.
- **Bridge** — the `aph-hamilton` skill: reads definitions from `${CLAUDE_SKILL_DIR}`, reads/writes
  state in the project's `.aphelocoma/`. The **product** (the app being built) lives in the project
  proper (repo root or `./product`), NOT inside `.aphelocoma/`.

## Repo placement (aphelocoma `tool` repo)

```
skills/aph-hamilton/
├─ skill.md                 # entrypoint: start / resume / status / sync-agents
├─ metadata.yaml            # name, description, type, arguments
├─ HANDOFF.md               # continue-here doc for the implementation session
├─ references/              # the Hamilton definition  (deploy copies this →  ${CLAUDE_SKILL_DIR}/references)
│  ├─ PROTOCOL.md  roles/ (27)  sizes.yaml  roles.index.md  VERSION
│  ├─ settings.example.yaml  ABOUT.md  START.reference.md
├─ templates/aphelocoma/    # per-project .aphelocoma/ skeleton  (deploy copies this)
│  ├─ hamilton.json  state/{tasks.json,brief.md,roadmap.md}  ledger/{events.jsonl,agents/}  specs/
└─ examples/todo-solo/      # a real executed run  (deploy copies this)
```

- **Deploy:** the existing `deploy` skill reads `skills/aph-hamilton/{skill.md, metadata.yaml}`,
  generates a per-tool `SKILL.md` from the frontmatter, and copies `references/`, `templates/`,
  `examples/` alongside it. Add `adapters/claude-code/overrides/aph-hamilton.yaml` and
  `adapters/codex/overrides/aph-hamilton.yaml` only if tool-specific tweaks prove necessary (likely
  minimal, since `type: manual`).
- **Built-in vs custom:** built-ins live in the repo `skills/` (this is one). Users can still drop
  custom skills in `~/.aphelocoma/data/skills/`.

## Per-project layout (created by `start`)

```
X-project/
├─ .aphelocoma/
│  ├─ hamilton.json     # project · size · roles · definition_version · phase
│  ├─ state/  tasks.json · roadmap.md · brief.md
│  ├─ ledger/ events.jsonl · agents/<role>.md
│  └─ specs/  <task>.md
└─ (the product — repo root or ./product)
```

## Skill behavior

- **`start "<brief>" <size>`** — resolve size from `sizes.yaml`; copy `templates/aphelocoma/` →
  `./.aphelocoma/`; write `hamilton.json` (version from `references/VERSION`); run the PROTOCOL phases
  reading roles from `references/roles/`; build the product in the project; log to the ledger.
- **`resume`** — read `.aphelocoma/`; warn on version drift; continue per PROTOCOL §6.
- **`status`** — phase + tasks + recent events.
- **`sync-agents`** (Phase 2) — generate `.claude/agents/<role>.md` from `references/roles/`.

## Version-pin semantics

- `references/VERSION` = the Hamilton **definition** version (starts `1.0.0`; bump on protocol/role
  changes; independent of aphelocoma's own `VERSION`).
- `hamilton.json.definition_version` = the version a project started under.
- `resume` compares them; on mismatch it warns and lets the user choose to continue (optionally noting
  the drift in the ledger as `assumption_logged`).

## Native agents (Phase 2)

- **Generation** — for each active role, write `.claude/agents/<id>.md` (Claude agent frontmatter:
  name, description, tools, model) wrapping the canonical `references/roles/<id>.md` plus a runner
  preamble ("you are `<role>`; follow PROTOCOL; read/write the project's `.aphelocoma/`"). **Derived +
  regenerable** via `sync-agents` ⇒ no drift from the canonical roles.
- **Concurrency — orchestrator-owned state.** The active manager role (engineering-manager, or the top
  active leadership role under §7 coverage) dispatches implementer subagents in parallel; each
  subagent does its work, writes its artifacts + its own `ledger/agents/<role>.md`, and **returns a
  structured result**; the **orchestrator** serializes all `state/tasks.json` updates and
  `events.jsonl` appends (single writer). Parallel work, single-writer state ⇒ no races on the
  append-only ledger or live board.
- **Fallback** — non-Claude platforms skip generation and run sequential file-based role-play.
  Portability preserved by default; native agents are purely additive.

## Phasing

- **Phase 1 (MVP, portable):**
  1. **Rename pass:** company/OS → Hamilton across `references/` (and update `ABOUT.md` /
     `START.reference.md`; keep "crew/team" as descriptive nouns).
  2. Finalize `skill.md` `start`/`resume`/`status` to read the definition via `${CLAUDE_SKILL_DIR}`
     and write the thin `.aphelocoma/`.
  3. `hamilton.json` + version-pin read/compare.
  4. **Confirm cross-tool skill-dir resolution:** verify the skill reaches its bundled `references/`
     on **both** Claude (`${CLAUDE_SKILL_DIR}`) and Codex (confirm the equivalent, or have the codex
     adapter rewrite it); add `adapters/*/overrides/aph-hamilton.yaml` only if needed.
  5. Deploy to Claude + Codex; **cold-start test** (see Verification).
- **Phase 2:** `sync-agents` generation + orchestrator-owned-state parallelism on Claude Code; cold-start
  test of parallel mode.

## Terminology

- System/brand: **Hamilton**. Command: `/aph-hamilton`. Per-project dir: `.aphelocoma/`. Definition
  bundle: "the Hamilton definition" (not "OS"). The set of role-agents: "the crew" (not "the company").
  The relocated seed under `references/` still uses the old labels — fixing that is Phase-1 task #1.

## Verification (must re-run after the build)

Reuse the **cold-start** method that validated the prototype: copy a throwaway project, deploy
Hamilton, hand a **fresh agent** only the user-level kickoff (`/aph-hamilton start "a simple todo list
app" solo`), and verify it (a) bootstraps `.aphelocoma/` correctly, (b) reads the definition from the
installed location, (c) runs the full loop with schema-valid ledger events + monotonic `seq`,
(d) applies §7 coverage unprompted, (e) records the version pin. Phase 2: verify parallel subagents do
not corrupt state (orchestrator-owned writes).

## Status (as of this spec)

- **Done:** decisions locked; verified prototype relocated into
  `skills/aph-hamilton/{references,templates,examples}`; `metadata.yaml` + DRAFT `skill.md` +
  `references/VERSION` (1.0.0) + `templates/aphelocoma/hamilton.json` written; this spec.
- **Pending (next session):** everything under **Phasing** — rename, finalize + test `skill.md`,
  adapter overrides, deploy, cold-start test (Phase 1); native agents (Phase 2).

## Open questions

- **Cross-tool skill-dir resolution (verify in Phase 1 — NOT deferrable):** the skill reads its bundled
  definition via `${CLAUDE_SKILL_DIR}`, which is verified on **Claude Code only** (used by
  `project-init`). Confirm the **Codex** equivalent resolves under `~/.codex/skills/aph-hamilton/`
  (or have the codex deploy adapter rewrite the variable) **before** claiming thin+global-ref works
  cross-tool. This sits directly on the platform-agnostic promise — test it early, don't assume it.
- `.aphelocoma/` shared with possible future aphelocoma per-project data vs namespacing Hamilton under
  `.aphelocoma/hamilton/`. Current choice: Hamilton state directly in `.aphelocoma/` (matches the
  user's mental model); revisit if aphelocoma adds other per-project artifacts.
- Whether to register each Hamilton project in aphelocoma's `core/projects/registry.json` (tie-in with
  `project-init`). Nice-to-have.
