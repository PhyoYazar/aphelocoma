# Migrating to Aphelocoma v0.3

Aphelocoma v0.3 is a breaking, Hamilton-only reset. Read this guide before replacing a v0.2
installation.

## What changed

The v0.3 runtime contains the `aph` lifecycle CLI, the Hamilton skill, its shared definition, and
Claude/Codex crew generators. It no longer ships the former second-brain/context runtime, Cursor
deployment target, project registry, sync/journal/capture flow, or context-view generation.

There is no automatic compatibility path for those retired features. Existing legacy data remains an
archive unless you choose to handle it outside Aphelocoma.

## Legacy data is outside the migration

v0.3 protects both possible legacy data locations:

- the default `~/.aphelocoma/data`;
- the custom path from the retired `APHELOCOMA_HOME` environment variable, when set.

Neither location is read, modified, or deleted by install, deploy, undeploy, doctor, update,
uninstall, or legacy cleanup. `APHELOCOMA_HOME` is ignored when resolving active v0.3 storage and
causes the CLI to print a protected-legacy warning. Set `APHELOCOMA_ROOT` if the v0.3 installation
itself must live somewhere other than `~/.aphelocoma`.

For defense in depth, lifecycle commands also refuse roots, symlinks, deployment targets, or backup
paths that overlap a protected legacy location.

## Before upgrading

1. Record any deliberate edits you made to generated files in `~/.claude` or `~/.codex`. Legacy
   cleanup will not delete modified files; when a new generated path collides with one, deployment
   keeps its content in a recorded backup before installing the new crew.
2. Keep your legacy data where it is. Moving it into an active v0.3 tool, manifest, deployment, or
   backup path will make safety checks refuse the operation.
3. If a project already has Hamilton state in `.aphelocoma/`, commit or separately archive the
   project before running the project-state migration.

## Install and deploy v0.3

Run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/main/install.sh | bash
```

The installer stages and verifies the release before activation. If activation fails, a clean install
leaves no partial tool and an upgrade restores the previous tool and install manifest.

Open a new shell if the installer updated its managed PATH block, then deploy one or both supported
hosts:

```bash
aph deploy claude
aph deploy codex
aph doctor
```

Claude and Codex are the only first-class v0.3 targets. The minimum/tested CLI pairs are Claude Code
`2.1.0`/`2.1.217` and Codex `0.145.0`/`0.145.0`. An older detected CLI makes `aph doctor` fail with
upgrade remediation. If neither host CLI is on PATH, doctor remains healthy because Hamilton can use
its sequential workflow.

## What happens to old global artifacts

Installation, update, and uninstall inspect known v0.2-era global artifacts outside the protected
data directories. Cleanup removes an artifact only when it exactly matches a released artifact or,
for a known legacy skill tree, its structure and content prove its origin.

This means:

- exact legacy agents, hooks, PATH stanzas, and known legacy skill trees can be removed;
- modified legacy-looking files are preserved and reported;
- unrelated `CLAUDE.md`, `AGENTS.md`, settings, hooks, agents, and skills are not treated as legacy.

Run `aph doctor` to see unresolved global artifacts. Move or reconcile any preserved file yourself;
Aphelocoma will not guess that it owns a modified file.

## Migrate an existing Hamilton project

Current project state declares:

```json
{
  "schema_version": 1,
  "protocol_version": "1.0.0"
}
```

From the project root, check unversioned v0.2 state without writing:

```bash
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py check .
```

Then apply the migration:

```bash
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py apply .
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/validate.py .
```

`apply` copies the original `.aphelocoma/` byte-for-byte before swapping in validated state. In a Git
repository the backup lives under the authoritative Git metadata in `aphelocoma-backups/`, which keeps
it recoverable without making it a project file. Outside Git it uses a timestamped
`.aphelocoma.backup-v0.2-*` sibling. A failed migration restores the original state.

The migration adds explicit privacy settings:

```yaml
visibility: tracked
redact_sensitive: true
```

Review the choice after migration. Keep `tracked` when compact, redacted Hamilton plans/specs/ledger
may be committed. Change it to `local` only after removing every `.aphelocoma/` path from Git. Raw
dispatch prompts, results, logs, temporary files, and backups are transient in either mode and must
not be tracked.

Future schema or protocol versions are refused with upgrade remediation; v0.3 does not downgrade
them.

## Deployment ownership and drift

Each `aph deploy <tool>` writes a manifest under `$APHELOCOMA_ROOT/manifests/` and collision backups
under `$APHELOCOMA_ROOT/backups/<tool>/`. The manifest records exact paths and digests plus any
marker-delimited configuration block.

`aph undeploy <tool>`:

- removes a generated artifact only if its digest still matches;
- removes only the recorded managed block from shared configuration;
- restores pre-existing content from a verified collision backup;
- preserves drifted files or blocks and keeps a partial manifest until they are resolved.

If undeploy reports drift, copy or move the modified artifact somewhere safe, restore it to the
generated state or remove the deliberate edit, and retry. Do not delete the manifest or collision
backup to force cleanup; missing or tampered recovery records are refused before host mutation.

## Update, uninstall, and recovery

`aph update` first verifies the active tool and its install manifest. A failed activation restores the
previous tool and manifest byte-for-byte. A successful update retains the previous tool under
`$APHELOCOMA_ROOT/backups/install/` and records its path in the install manifest.

`aph uninstall` is ownership-aware:

1. it undeploys both Claude and Codex;
2. it removes the recorded PATH block;
3. it removes the manifest-owned active tool and install manifest.

Any deployment or PATH drift stops uninstall before the tool is removed. Resolve the reported drift
and retry. Uninstall retains recovery backups and, like every other v0.3 command, does not read,
modify, or delete default or custom legacy data.

Use human-readable or machine-readable diagnostics during recovery:

```bash
aph doctor
aph doctor --json
```
