# Software Architect ledger

- 2026-07-23T07:46:24Z — Derived binding conventions from the existing Markdown/YAML/JSON/Python/Bash
  repository and selected a Python standard-library CLI architecture for the reset.
- 2026-07-23T08:05:00Z — Split `aph doctor` checks by contract ownership so runtime diagnostics,
  Hamilton-state diagnostics, and deployment diagnostics are implemented only after their respective
  interfaces exist.

# T9 run-visibility breakdown

- 2026-07-26T02:55:00Z — Took the advisor's visibility request into the roadmap as Milestone 6 and broke
  it down into a single task. Chose print-only rendering over a persisted board file: a generated file
  under tracked `state/` is derived data that churns every commit and can drift from `tasks.json`.
  Put the board's content in `PROTOCOL.md` as the spec with the CLI as the fast path, so a project
  running newer protocol text against an older installed `aph` degrades to orchestrator rendering
  instead of failing at the moment it is meant to show progress. Assigned T9 to `fullstack-developer#1`,
  the T1 owner of the CLI and doctor surface.
