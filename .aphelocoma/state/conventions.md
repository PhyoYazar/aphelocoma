# Conventions

- Runtime: Python 3.9+ standard library for the CLI and generators; Bash is limited to the installer
  entrypoint and must work on macOS and GNU/Linux.
- Layout: `bin/aph` is a thin executable entrypoint; reusable CLI logic lives in a small Python package
  under `src/`; tests mirror behavior under `tests/`.
- Paths: use `pathlib`; resolve the install root from `APHELOCOMA_ROOT` or `~/.aphelocoma`; never inject
  shell values into Python source or rely on string-prefix path containment.
- Writes: create parent directories explicitly and use temporary-file + atomic-replace for JSON,
  configuration, and manifest updates.
- Ownership: deployments record exact paths, digests, backups, generated blocks, and tool versions.
  Undeploy changes only artifacts proven to be owned by Aphelocoma.
- Configuration: never replace a user's entire `CLAUDE.md`, `AGENTS.md`, hooks, or Codex config.
  Prefer standalone skill/agent files and marker-delimited blocks.
- Errors: commands return `0` on success, `1` for an actionable health/usage failure, and `2` for an
  unexpected internal failure; messages name the failed artifact and remediation.
- Privacy: never write secrets or raw credentials; `.aphelocoma/dispatch/`, worker prompts, results,
  and logs are transient and ignored; compact state visibility is explicit per project.
- Tests: use `unittest`, `tempfile`, isolated `HOME`, and subprocess-level CLI tests. Every regression
  identified in the audit gets a test before its fix.
- Compatibility: stored Hamilton state declares schema and protocol versions. Migrations are explicit,
  backed up, testable, and reversible.
- Product scope: v0.3 ships Hamilton only. Removed context features are not left as hidden compatibility
  paths; legacy data is preserved but inactive.
- Documentation: claims must match tested behavior and the supported tool/OS matrix.
