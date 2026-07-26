# Changelog

All notable changes to Aphelocoma are recorded here.

## [0.3.0] — Unreleased

v0.3 is a breaking reset that makes Hamilton the complete Aphelocoma product.

### Added

- A Python 3.9+ standard-library `aph` CLI with `deploy`, `undeploy`, `doctor`, `status`, `update`,
  `uninstall`, `version`, and `help`.
- `aph status [path] [--json]`: a read-only Hamilton progress board reporting project, phase,
  schema/protocol version, visibility, done/total progress, every task with its status word, title and
  owner, blocked tasks, the next actionable task, and the repository's branch, short HEAD, commits
  since the run began, and working-tree cleanliness. It writes nothing under `.aphelocoma/`, uses no
  colour, and degrades to a plain statement rather than guessing when Git details are unavailable.
- Transactional installation and update with release verification, owned PATH blocks, rollback, and
  retained previous-tool recovery.
- Manifest-owned Claude Code and Codex deployment, including exact digests, marker-delimited shared
  configuration, collision backups, drift preservation, and reversible undeploy.
- Generated 27-role Hamilton crews for Claude Code and Codex.
- Versioned Hamilton project state with schema `1`, protocol `1.0.0`, lifecycle replay validation,
  privacy validation, strict worker/reviewer result contracts, and backed-up v0.2 state migration.
- Human-readable and JSON doctor reports for installation, deployment, host versions, legacy global
  artifacts, project-state compatibility, and privacy.
- Tested host floors: Claude Code 2.1.0 and Codex 0.145.0. Tested versions: Claude Code 2.1.217 and
  Codex 0.145.0.
- Explicit `tracked` and `local` durable-state privacy modes, with dispatch prompts/results/logs kept
  transient in both.

### Changed

- Claude Code and Codex are the only first-class deployment targets.
- Parallel implementation is used when the supported backend and at least two dependency-ready,
  file-disjoint tasks are available; sequential execution remains selectable and is the automatic
  fallback.
- The installer activates only the Hamilton runtime at `$APHELOCOMA_ROOT/tool` (default
  `~/.aphelocoma/tool`).
- Uninstall now stops on unresolved deployment or PATH drift and retains recovery backups.

### Removed

- The former second-brain/context runtime and its identity, knowledge, project-registry, journal,
  capture, reflection, sync, second-brain dashboard, and view surfaces. The unrelated v0.3
  `aph status` command reports Hamilton project progress only.
- Cursor deployment and web-context export.
- Automatic first-run context setup.

### Migration and safety

- The default legacy data directory `~/.aphelocoma/data` and a custom path from the retired
  `APHELOCOMA_HOME` variable are not read, modified, or deleted.
- `APHELOCOMA_HOME` is ignored for active v0.3 storage; `APHELOCOMA_ROOT` is the active-root override.
- Cleanup removes only exact or structurally proven legacy global artifacts. Modified and unrelated
  host files are preserved and reported.
- Unversioned v0.2 Hamilton project state migrates only through the explicit `migrate.py check|apply`
  flow with a persistent byte-for-byte backup and rollback.

See [the v0.3 migration guide](docs/migration-v0.3.md) for upgrade and recovery steps.

## [0.2.0]

- Final release of the retired context-oriented product line.
- Added the earlier Hamilton workflow that v0.3 promotes into the sole product.

[0.3.0]: https://github.com/PhyoYazar/aphelocoma/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/PhyoYazar/aphelocoma/releases/tag/v0.2.0
