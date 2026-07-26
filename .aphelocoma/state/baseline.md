# Advisor-owned WIP baseline

The repository was already dirty when the Hamilton-only reset began. These changes belong to the
advisor and predate the reset. No implementation task may start and no crew commit may be made until
the advisor selects a baseline treatment at Checkpoint 2.

## Preserve and integrate semantically

- `adapters/codex/scripts/gen-hamilton-crew-codex.py`
- `skills/aph-hamilton/references/DISPATCH-CODEX.md`
- `skills/aph-hamilton/references/result.implementer.schema.json`
- `skills/aph-hamilton/references/result.reviewer.schema.json`
- The Codex parallel-dispatch, named-role, model/effort, reviewer-sandbox, and schema-contract changes
  in `skills/aph-hamilton/skill.md` and `references/{ABOUT,PARALLEL,PROTOCOL,settings.example.yaml}`
- The matching project template settings

These are inputs to the v0.3 Hamilton contract. Implementers must compare their work against the
advisor baseline and preserve the intended behavior rather than reverting or blindly overwriting it.

## Intentionally superseded by the reset

- `README.md` wording will be rewritten around the Hamilton-only product, while retaining accurate
  Codex parallel-dispatch behavior.
- `skills/deploy/skill.md` will be removed with the legacy standalone skills after its Hamilton
  generator/readiness requirements move into the CLI and tests.
- `adapters/codex/hooks.json` will be removed because the global journal/context reminder is outside
  the Hamilton-only product and v0.3 will not own global hooks.

## Advisor decision

Approved option 1 on 2026-07-23:

- Advisor-owned baseline commit: `79697c0` (`Hamilton: baseline Codex parallel dispatch WIP`)
- Hamilton planning state is committed separately after task breakdown.
- Implementers work on top of `79697c0`; no task may revert the preserved Codex semantics listed
  above without an explicit, documented replacement that passes the corresponding tests.

## Options considered

1. **Recommended:** commit the current WIP exactly as an advisor baseline, then let Hamilton make
   task-scoped commits on top.
2. Export an exact binary-safe patch outside the repository and restore a clean tree before Hamilton
   work; reapply only the classified preserved changes.
3. Stop the Hamilton run and let the advisor finish/reorganize the WIP manually.

The advisor selected option 1. The overlapping WIP is no longer uncommitted.
