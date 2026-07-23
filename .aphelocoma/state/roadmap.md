# Roadmap — Aphelocoma v0.3 Hamilton-only reset

## Goal traceability

1. Make Hamilton the only product → Milestones 2, 4.
2. Repair deployment, portability, quoting, environment, undeploy, update, and uninstall failures →
   Milestones 1, 3, 5.
3. Establish privacy and state compatibility guarantees → Milestones 2, 5.
4. Preserve and complete the advisor's Codex parallel-dispatch work → Milestones 0, 2, 3, 5.
5. Make documented confidence match tested confidence → Every implementation milestone plus Milestone 5.

## Milestone 0 — Resolve the advisor-owned baseline

Owner: advisor, facilitated by CTO

- Use `.aphelocoma/state/baseline.md` to classify every current dirty file as preserved or
  intentionally superseded.
- Before Breakdown, the advisor chooses: commit the current WIP as a separate baseline (recommended),
  export it as an external patch and restore a clean tree, or stop for manual reorganization.
- Record the chosen baseline SHA or patch checksum in the ledger. No implementation or crew commit
  begins before this gate.

Tests-first: not applicable—this is a source-ownership and history decision.

Dependencies: none. This gates Milestones 1–5.

## Milestone 1 — Tested CLI and diagnostics foundation

Contract owner: software-architect

Implementation owner: fullstack-developer#1

- Add failing standard-library subprocess tests using isolated `HOME`, `APHELOCOMA_ROOT`, custom
  legacy `APHELOCOMA_HOME`, quoted paths, and non-interactive/no-colour output.
- Replace the 1,198-line Bash CLI with a small Python 3.9+ standard-library CLI and thin executable
  entrypoint.
- Implement the Hamilton-only command contracts: `deploy`, `undeploy`, `doctor`, `update`, `uninstall`,
  `version`, and `help`.
- Define `APHELOCOMA_ROOT` as the only active v0.3 root. If legacy `APHELOCOMA_HOME` is set, warn and
  protect both that custom location and the default `~/.aphelocoma/data` as read-only legacy data.
- Make Git, Python, macOS, and Linux requirements explicit and return stable command exit codes.

Base `aph doctor` contract and tests owned by this milestone:

- Check Python/Git/OS support and installed Aphelocoma version/definition completeness.
- Human output names remediation; `--json` is stable machine-readable output.
- Exit `0` when healthy, `1` for actionable health findings, `2` for unexpected internal failure.

The command exposes an internal check registry so later milestones add checks only after owning
contracts exist: Milestone 2 adds project-state/schema/privacy checks; Milestone 3 adds deployment,
managed-block, host-tool readiness, parallel/fallback, and legacy-artifact checks.

Dependencies: Milestone 0.

## Milestone 2 — Versioned, privacy-aware Hamilton contract

Contract owner: software-architect

Implementation owner: fullstack-developer#2

Review owner: qa-engineer

- First add failing validator/migration/schema tests for unversioned state, future incompatible state,
  reviewer=builder, out-of-order critique/review events, missing task/event references, invalid
  transitions, transient tracked files, and representative secret material.
- Add schema/protocol fields to templates, examples, validation, start, resume, and status.
- Provide an explicit check/apply migration script: back up `.aphelocoma/`, migrate unversioned v0.2
  state, validate the result, and restore the backup on failure. Refuse unsupported future versions.
- Define `visibility: tracked | local`; keep dispatch prompts, worker results, and logs transient in
  both modes; never put raw prompts or credentials in durable audit notes.
- Finalize the existing Codex result schemas and `DISPATCH-CODEX.md` contract here. This milestone owns
  Hamilton protocol/schema files; deployment code does not edit them.
- Add the project-state `aph doctor` checks and tests now that the contracts exist: schema/protocol
  compatibility, migration requirement, validator integrity, tracked transient files, and common
  secret patterns.

Dependencies: Milestone 0. Its finalized interfaces gate Milestone 3.

## Milestone 3 — Transactional lifecycle and reversible deployment

Contract owner: software-architect

Implementation owner: fullstack-developer#1

Integration owner: devops-engineer

- Add failing tests before each behavior change: clean install, interrupted clone/install, failed
  update with rollback, successful update, ownership-aware uninstall, deploy twice, undeploy twice,
  modified collision, corrupt manifest, managed-block drift, legacy default/custom data, and partial
  generator failure.
- Make `install.sh` stop invoking removed context setup and install the v0.3 tool transactionally.
- Make update stage and verify a new release before an atomic swap; retain a recoverable previous tool
  until success. Failure restores the last working tool.
- Install only the Hamilton skill/references/templates/examples and generated crew agents.
- Complete Codex deployment using the finalized Milestone 2 contracts; generate all 27 named roles.
  Do not rewrite the protocol/schema files owned by Milestone 2.
- Add per-tool manifests, digests, backups, managed blocks, and idempotent deploy/undeploy.
- Uninstall first performs ownership-aware undeploy, removes only the installed tool/PATH marker, and
  leaves legacy default/custom data, backups, and unowned configuration untouched.
- Detect v0.2 artifacts and remove only exact-match or proven-owned content; warn and preserve anything
  modified or ambiguous.
- Add deployment `aph doctor` checks and tests now that the deployment contracts exist: Claude/Codex
  availability and tested/minimum versions, agent/skill readiness, parallel versus sequential
  fallback, manifest/digest drift, managed-block integrity, collision backups, and legacy artifacts.

Dependencies: Milestones 1 and 2.

## Milestone 4 — Remove the second-brain product and reposition Aphelocoma

Code-removal owner: fullstack-developer#2

Product owner: product-manager

Documentation owner: technical-writer

- Begin with a package-inventory test that fails while any context skill, registry/journal/view command,
  private-knowledge export, legacy adapter override, or unsupported Cursor claim remains shipped.
- Remove context-layer skills, overrides, templates, CLI paths, hooks, generated global instructions,
  and the Cursor adapter from the v0.3 package.
- Rewrite the README around “Aphelocoma — the portable Hamilton agent crew.”
- Document v0.2 → v0.3 behavior, tested/minimum Claude/Codex versions, sequential fallback, privacy,
  recovery/rollback, legacy default/custom data, and exact install/deploy/undeploy/uninstall behavior.
- Add a changelog and ensure every claim traces to an automated scenario.

Dependencies: Milestones 1–3 define the behavior and safe cleanup path.

## Milestone 5 — Cross-platform release verification

Review owner: qa-engineer

CI/release owner: devops-engineer

- Add CI on Ubuntu and macOS using the tests written inside Milestones 1–4.
- Run isolated clean-install/deploy/undeploy flows for both Claude Code and Codex on both operating
  systems, including repeated operations and sequential fallback when host parallel features are absent.
- Rerun failure-injection cases for interrupted install/update, rollback, uninstall, manifest drift,
  modified config, default/custom legacy data, Hamilton migration, Codex generation, and validator
  enforcement.
- Verify no command changes or deletes either legacy data location and no context/private-knowledge
  feature remains in the shipped package.
- Run an independent per-task CP4 review and one end-to-end Hamilton cold start before v0.3.0 readiness.

Dependencies: Milestones 1–4.

## Foundations disposition

- Deploy: addressed by Milestones 1, 3, and 5.
- Fault-tolerance: addressed by transactional lifecycle operations, idempotency, backups, rollback, and
  failure injection in Milestones 1, 2, 3, and 5.
- Security: addressed by ownership boundaries, privacy/visibility policy, secret checks, and protected
  default/custom legacy locations in Milestones 1–3.
- UX: addressed by the reduced command surface, exact doctor remediation, and onboarding in
  Milestones 1, 3, and 4.
- Observability: addressed by doctor output, manifests, validation, stable exit codes, and CI in
  Milestones 1–3 and 5.
- Accessibility: addressed by terminal-aware/no-colour output and cross-platform tests in Milestones
  1 and 5.

## Conscious deferrals

- Cursor, Copilot, Windsurf, MCP, semantic search, journals, knowledge capture, cross-project context,
  and web-AI views are outside v0.3.
- Third-party Python packages and a plugin system are deferred; the reset remains standard-library only.
