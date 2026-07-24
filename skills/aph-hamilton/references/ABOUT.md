# Hamilton — the Aphelocoma agent crew

Hamilton is a file-based software crew that discovers, plans, implements, and independently reviews a
project in Claude Code or Codex while a human advisor makes the key decisions.

## Definition and project state

Hamilton separates its shared operating definition from each project's writable state:

- **Shared definition (read-only)** — this `references/` directory contains `PROTOCOL.md`, role
  definitions, crew sizes, parallel-dispatch rules, state/result schemas, validation, and migration.
  Aphelocoma installs it once with the skill.
- **Per-project state (read/write)** — `.aphelocoma/` in the project contains the brief, roadmap,
  conventions, task contracts, live board, and append-only ledger.
- **Product** — the software being built stays at the project root beside `.aphelocoma/`; Hamilton
  does not force it into a wrapper directory.

The two durable records have distinct jobs:

- `.aphelocoma/state/tasks.json` is the current task board;
- `.aphelocoma/ledger/events.jsonl` is gap-free, append-only history;
- `.aphelocoma/ledger/agents/<role>.md` is the human-readable record for each role.

The orchestrator is the sole writer of the shared board and event ledger, including during parallel
implementation.

## Advisor flow

Start with the guided skill:

```text
/aph-hamilton
```

Hamilton asks whether the project is new or existing and what you want to build. When the brief is
already clear, use the fast path:

```text
/aph-hamilton start "build a furniture store" startup
```

The initial size is a proposal. Leadership first surveys the project and runs the Foundations pass,
then the advisor chooses the direction and crew. Available crew shapes are `solo`, `startup`, `mid`,
`big`, and `custom:[role,…]`.

The crew pauses at four advisor checkpoints:

1. direction and crew size after Discovery;
2. roadmap and task breakdown;
3. parallel or sequential build style;
4. final review and acceptance.

Independent critique runs before checkpoints 1, 2, and 4. Every implementation task also needs its
own fresh critique and review pass before it can be marked `done`. The orchestrator commits each
finished task on the current branch; it does not branch or push.

Resume or inspect a run with:

```text
/aph-hamilton resume
/aph-hamilton status
```

Both use the project state at `.aphelocoma/`; resume validates integrity before continuing and status
is read-only.

## Claude Code and Codex

Claude Code and Codex are the two first-class Hamilton hosts in Aphelocoma v0.3.

| Host | Minimum CLI | Tested CLI | Parallel implementation |
| --- | ---: | ---: | --- |
| Claude Code | 2.1.0 | 2.1.217 | Native `hamilton-<role>` crew agents |
| Codex | 0.145.0 | 0.145.0 | Background `codex exec` role workers |

Parallel implementation is the default only when the host backend is available, its role definition
is reachable, and at least two dependency-ready tasks declare disjoint file scopes. Otherwise
Hamilton runs one role at a time in the sequential workflow. The advisor can also select sequential
execution at checkpoint 3.

On Claude Code, `aph deploy claude` installs the skill and global named crew. A project can override
role model/effort settings with `.aphelocoma/settings.yaml`; after changing those settings, run:

```text
/aph-hamilton sync-agents
```

Restart the Claude session after a per-project crew regeneration.

On Codex, `aph deploy codex` installs the skill, named role configuration, and generated agent files.
Headless `codex exec` workers are the default dispatch path. The experimental collaboration backend is
used only when explicitly selected or when automatic exec preflight falls back to it; a failed
preflight ultimately falls back to sequential execution. See `DISPATCH-CODEX.md`.

## Privacy modes

Every `.aphelocoma/settings.yaml` declares:

```yaml
visibility: tracked  # or: local
redact_sensitive: true
```

- `tracked` allows compact, redacted plans, specs, task state, and ledger entries in version control.
- `local` requires all `.aphelocoma/` paths to remain untracked.

Raw prompts, results, worker logs, temporary files, and backups are transient in both modes. Put
dispatch scratch under `.aphelocoma/dispatch/`; it is not durable state and must not be tracked.
Durable notes contain summaries rather than raw worker content or credentials.

The validator checks visibility against Git's tracked state and fails closed if it cannot determine
that state.

## Versioned state and migration

Current project state declares schema `1` and protocol `1.0.0`. Resume and status validate those
versions, the mechanically loaded state schema, lifecycle/review ordering, task dependencies, and
privacy.

Unversioned v0.2 project state uses the explicit migration commands from the project root (shown for
the default install location):

```bash
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py check .
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py apply .
```

For a custom `APHELOCOMA_ROOT`, replace `~/.aphelocoma` with that root. `check` is read-only. `apply`
validates staged state before replacement, retains a byte-for-byte backup, and restores the original
state if migration fails. Unsupported future state requires an Aphelocoma upgrade.

## Project layout

```text
references/                 # shared, installed Hamilton definition
├── PROTOCOL.md             # workflow and lifecycle rules
├── PARALLEL.md             # eligibility, single-writer contract, serialization
├── DISPATCH-CODEX.md       # Codex backend selection and worker mechanics
├── state.schema.json       # durable state contract
├── result.*.schema.json    # strict implementer/reviewer result contracts
├── validate.py             # project-state integrity checker
├── migrate.py              # backed-up state migration
├── sizes.yaml              # crew presets
└── roles/                  # 27 role definitions

<project>/.aphelocoma/
├── hamilton.json           # schema, protocol, project, crew, phase
├── settings.yaml           # visibility and optional dispatch/model settings
├── state/                  # brief, roadmap, conventions, tasks
├── specs/                  # one acceptance contract per task
├── ledger/                 # append-only events and per-role logs
└── dispatch/               # transient worker scratch; never commit
```

`examples/todo-solo/` is a bundled reference run. It is documentation, not live project state.

## Deployment and recovery

Use `aph deploy <claude|codex>` and `aph undeploy <claude|codex>` to manage host integration.
Deployment manifests record exact paths, digests, managed blocks, and collision backups. Undeploy
removes only clean manifest-owned content and restores verified collision backups. Modified generated
files or blocks are preserved and reported as drift.

`aph update` verifies the current installation, rolls back the previous tool and manifest on failure,
and records a recoverable previous tool on success. `aph uninstall` first undeploys both hosts and
stops before tool removal if deployment or PATH drift remains. Recovery backups are retained.

`aph doctor` reports installation, deployment, backup, host-version, legacy-artifact, state-version,
and privacy health with remediation; `aph doctor --json` provides the same checks in a stable
machine-readable shape.
