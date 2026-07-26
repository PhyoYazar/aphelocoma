# Project Brief

status: active

## Brief

Refocus Aphelocoma into the portable distribution and CLI for Hamilton. Remove the global personal
context/second-brain product because the advisor no longer finds it convenient or uses it. Preserve
the current Codex parallel-dispatch work and fix the reliability, portability, privacy, deployment,
validation, and product-positioning issues found in the July 2026 audit.

## Advisor

Phyo Yazar — owns product direction, compatibility policy, branches, and publishing.

## Direction

Clean Hamilton-only reset for v0.3.0:

- Aphelocoma is the installable product and distribution; Hamilton is its single core workflow.
- Global installation contains the tool, deployment ownership manifests, backups, and generated
  Hamilton agents—no identity, knowledge, journal, registry, or cross-project context database.
- Each software project keeps its own versioned `.aphelocoma/` Hamilton state.
- Existing `~/.aphelocoma/data` is legacy user data: detect and explain it, but never create, read,
  migrate, expose, or delete it automatically.
- Claude Code and Codex are first-class v0.3 targets. Cursor support is deferred until it has a
  truthful Hamilton-only adapter.

## Crew size

Startup-shaped custom crew: CTO, software architect, product manager, two full-stack implementers,
QA engineer, DevOps engineer, and technical writer.

## Foundations

- Deploy: support macOS and Linux; deploy Hamilton to Claude Code and Codex using ownership manifests,
  managed configuration blocks, collision backups, and reversible undeploy.
- Fault-tolerance: use transactional writes and directory swaps where practical; make deployment,
  migration, and cleanup idempotent; never report success when owned artifacts remain.
- Security: never overwrite or delete unowned configuration; keep legacy data untouched; never persist
  raw secrets; ignore dispatch prompts/results/logs; support tracked or local Hamilton state.
- UX: first-run path is install → `aph deploy <tool>` → `/aph-hamilton`; no second-brain setup ceremony.
  `aph doctor` reports exact problems and remediation.
- Observability: human-readable diagnostics plus stable exit codes; deployment manifests explain what
  Aphelocoma owns; validation reports state/protocol compatibility.
- Accessibility: respect non-interactive terminals and `NO_COLOR`; output remains understandable
  without colour or symbols.

## TDD

TDD: on

Every behavior-changing task begins with a failing standard-library test or integration smoke case.

## Compatibility policy

- v0.3.0 is an intentional pre-1.0 breaking release.
- Old personal-context features are removed rather than maintained as a plugin.
- Upgrade cleanup removes only exact-match or manifest-owned Aphelocoma artifacts. Modified or
  ambiguous files are backed up or left in place with a warning.
- Active Hamilton projects gain explicit schema/protocol versions and backed-up migrations; an
  incompatible resume fails clearly rather than silently interpreting old state.

## Activated roles

- cto
- software-architect
- product-manager
- fullstack-developer#1
- fullstack-developer#2
- qa-engineer
- devops-engineer
- technical-writer

## Existing worktree

The advisor's pre-existing Codex/Hamilton work was preserved in baseline commit `79697c0`.
`.aphelocoma/state/baseline.md` classifies what is preserved versus intentionally superseded.
