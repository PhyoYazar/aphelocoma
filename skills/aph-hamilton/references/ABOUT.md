# Hamilton — a portable, file-based crew of role-agents

**Hamilton** turns **any coding agent** (Claude Code, Codex, or others) into a small
software organization. You give it a brief like *"build a furniture ecommerce"*; leadership
roles brainstorm → plan → roadmap → assign; implementer roles build the product; and every
action is recorded so you can review **who did what** later.

It is **portable**: roles are just markdown files, coordination is a written protocol, and
history is plain files. Nothing depends on a specific tool's features.

## Two layers

- **Definition (read-only, installed once)** — this `references/` directory: `PROTOCOL.md`,
  `roles/`, `sizes.yaml`, `roles.index.md`, `PARALLEL.md`, `agent-template.md`. Shared by every project; never copied
  into them.
- **Per-project state** — a `.aphelocoma/` folder in the project being built:
  `hamilton.json`, `state/`, `ledger/`, `specs/`. Plus the **product** itself in the project (at the
  repo root, beside `.aphelocoma/`).

## How it works (30-second version)

The running agent **adopts one role at a time** (see `roles/`), reads the current task
state, does that role's work, writes the product into the project, and appends to the audit
ledger. Full rules: **`PROTOCOL.md`**.

## Start a project

Just run the **`/aph-hamilton`** skill (no arguments). It asks what you want, then the leadership core
brainstorms it **with you**. You're the **advisor**: you decide the direction, plan, build style, and
review at four checkpoints (PROTOCOL §1.5); the crew builds it. Fast path if you know the brief:

    /aph-hamilton start "Build an ecommerce site for furniture" startup

(The size is a *proposal* the crew confirms with you after Discovery.) See `START.reference.md`.

## Crew sizes

Chosen **after Discovery** (the leadership core recommends, you pick — see `sizes.yaml`):

- **solo** (~2) — one generalist; fastest, smallest loop.
- **startup** (~6) — CTO, architect, 2 full-stack devs, QA, DevOps. Proves the full loop.
- **mid** (~12) — leads + devs, product, design, QA/automation, DevOps, data.
- **big** (~25) — the full org chart, end to end.
- **custom** — pass your own role list (overrides the preset).

Only the selected roles activate; the rest stay dormant in `roles/`.

## Resume a project

Run `/aph-hamilton resume`. Hamilton reads `.aphelocoma/state/brief.md` +
`.aphelocoma/state/tasks.json`, reports the current phase and open tasks, and continues —
projects don't need to finish in one session.

## Review who did what (history)

- **`.aphelocoma/ledger/events.jsonl`** — append-only, one event per line (assignments,
  work, reviews, decisions). Machine-readable; each line has a `seq`, `ts`, `actor`, `event`.
- **`.aphelocoma/ledger/agents/<role>.md`** — the same history per role, human-readable.
- **`.aphelocoma/state/tasks.json`** — the *current* board (who owns what, status). Live
  state, not history — see `PROTOCOL.md` §5.

## Directory map

    references/             <- the Hamilton definition (read-only, installed once)
      PROTOCOL.md           <- the operating rules (read this to run)
      ABOUT.md              <- you are here
      START.reference.md    <- the kickoff reference + crew-size menu
      roles.index.md        <- the role catalog
      sizes.yaml            <- crew-size presets
      settings.example.yaml <- optional config example
      roles/                <- one markdown file per role (the "job descriptions")

    <project>/.aphelocoma/  <- per-project state (created by `start`)
      hamilton.json         <- project, size, roles, phase
      state/                <- tasks.json (live board), roadmap.md, brief.md
      specs/                <- one spec per task (handoff contracts w/ acceptance criteria)
      ledger/               <- events.jsonl + agents/<role>.md (append-only history)
    <project>/              <- the product itself (at the repo root, beside .aphelocoma/)

## Optional settings

`.aphelocoma/settings.yaml` is optional — Hamilton runs without it. It can set a role→model mapping
(used when generating native agents). The product always builds at the project root, and the build
style is chosen by the advisor at the Implementation checkpoint. See `settings.example.yaml`.

## Example run

`examples/todo-solo/` is a **real, executed reference run** — a fresh agent was handed only
the kickoff `/aph-hamilton start "a simple todo list app" solo` and ran it unaided. Browse it
to see exactly what gets written under `.aphelocoma/` and where the product lands. It ships
with the skill as a reference and is not part of any live project.
