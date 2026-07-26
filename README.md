# Aphelocoma

Aphelocoma installs and operates Hamilton, a file-based agent crew for building software with Claude Code or Codex.

## First run

### 1. Install

Python 3.9 or newer and Git are required.

```bash
curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/main/install.sh | bash
```

The installer activates a verified release at `~/.aphelocoma/tool`. It adds one managed PATH block to
the first existing `.zshrc`, `.bashrc`, or `.bash_profile`; otherwise it prints the directory to add
manually. Open a new shell after the install if your shell file changed.

### 2. Deploy Hamilton

Choose one first-class host:

```bash
aph deploy claude
# or
aph deploy codex
```

Deployment installs the Hamilton skill and its 27 named crew roles. It preserves existing host
configuration and records the exact generated files, digests, managed blocks, and collision backups in
an ownership manifest.

### 3. Start a build

Open the selected host in the project you want Hamilton to build, then run:

```text
/aph-hamilton
```

The guided start asks whether this is a new or existing project and what you want to build. A fast path
is available when the brief is already clear:

```text
/aph-hamilton start "build a furniture store" startup
```

## How Hamilton works

Hamilton organizes an agent session as a software crew: leadership discovers and plans the work, task
owners implement it, and independent reviewers check it. You remain the advisor and decide at four
checkpoints:

1. product direction and crew size;
2. roadmap and task scope;
3. parallel or sequential implementation;
4. final acceptance.

The crew stores compact project state in `.aphelocoma/` beside the product it is building:

```text
<project>/
├── .aphelocoma/
│   ├── hamilton.json          # project, schema, protocol, phase
│   ├── settings.yaml          # privacy visibility and optional dispatch settings
│   ├── state/                 # brief, roadmap, conventions, live task board
│   ├── specs/                 # one acceptance contract per task
│   └── ledger/                # append-only events and per-role logs
└── ...                        # the product itself
```

Every task is committed by the orchestrator on the current branch only after an independent
task-specific critique passes. Hamilton does not create a branch or push.

Useful skill commands:

```text
/aph-hamilton resume       # validate and continue an existing run
/aph-hamilton status       # show phase, tasks, crew settings, and integrity
/aph-hamilton sync-agents  # Claude-only per-project crew override
```

## Execution and host support

Claude Code and Codex are the only first-class v0.3 deployment targets.

| Host | Minimum CLI | Tested CLI | Parallel backend |
| --- | ---: | ---: | --- |
| Claude Code | 2.1.0 | 2.1.217 | Native Hamilton crew agents |
| Codex | 0.145.0 | 0.145.0 | Headless `codex exec` workers |

Parallel implementation is selected when a usable host backend and its role definitions are available
and Hamilton has at least two dependency-ready tasks with disjoint file scopes. The advisor can choose
sequential work instead. When a host CLI or dispatch backend is unavailable, the same role workflow
runs sequentially.

`aph doctor` reports installed host versions and remediation. A detected host below its minimum is a
health failure; no detected host is not a failure because sequential execution remains available.

The supported installation platforms are current macOS and GNU/Linux with Bash. Python 3.9 or newer is
required for the CLI, and Git is required when the installer or updater downloads the repository.

## Project-state privacy

Each Hamilton project explicitly chooses one durable-state mode in `.aphelocoma/settings.yaml`:

- `visibility: tracked` permits compact, redacted plans, specs, task state, and ledger entries in
  version control.
- `visibility: local` requires every `.aphelocoma/` path to remain untracked.

Both modes require `redact_sensitive: true`. Raw worker prompts, results, and logs belong under
`.aphelocoma/dispatch/`; project-local temporary and backup files are transient too. None of these are
durable project history, and they must not be tracked.

Hamilton state declares schema `1` and protocol `1.0.0`. Run validation before resuming:

```bash
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/validate.py .
```

For unversioned v0.2 project state, use the explicit, backed-up migration:

```bash
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py check .
python3 ~/.aphelocoma/tool/skills/aph-hamilton/references/migrate.py apply .
```

`check` is read-only. `apply` validates staged state, retains a byte-for-byte backup, and restores the
original state if migration fails.

## CLI

```text
aph deploy <claude|codex>     Deploy Hamilton and record ownership.
aph undeploy <claude|codex>   Remove clean manifest-owned deployment artifacts.
aph doctor [--json]           Check health and print remediation.
aph status [path] [--json] [--write]
                              Show the Hamilton progress board for a project, and
                              with --write regenerate .aphelocoma/STATUS.md.
aph update                    Download, verify, and activate an update transactionally.
aph uninstall                 Undeploy hosts and remove the owned installation.
aph version                   Print the installed version.
aph help [command]            Show supported commands.
```

Commands return `0` on success, `1` for an actionable health or usage failure, and `2` for an
unexpected internal failure.

## Progress board

`aph status` prints where the project stands — the stage, and the tasks — for a Hamilton project,
defaulting to the current directory:

```text
Hamilton  aphelocoma-hamilton-reset
Phase     implementation
Progress  9 of 11 tasks done

Tasks
  [done]      T1   Build the tested Python CLI and base doctor
  [blocked]   T10  Correct the v0.3 documentation assertions
  [assigned]  T11  Reduce the board to stage and tasks
```

Every task line carries its status as a word, so a blocked task says so in its own row, and the output
uses no colour. Owners, dependencies, schema/protocol versions, visibility, the next actionable task,
and the repository's branch, short HEAD, commits since the run began, and working-tree cleanliness stay
in `--json` for tools that need them; facts Git cannot supply are reported there as unknown rather than
guessed.

Without `--write`, the command writes nothing under `.aphelocoma/` and appends no ledger event. A path
with no `.aphelocoma/`, or state whose schema or protocol version is unsupported, exits `1` and names
the remediation.

### `.aphelocoma/STATUS.md`

`aph status --write` regenerates `.aphelocoma/STATUS.md`, the same board as Markdown you can open any
time instead of scrolling back through a terminal. Hamilton writes it after each completed task, when
work is blocked, when a review sends work back, and at the top of every resume.

The file is regenerated **whole** on every write — never appended to, never patched — through a
temporary file and an atomic replace, so it cannot accumulate drift and a failed write leaves the
previous board intact. One stamp line names the UTC generation time and the ledger `seq` it came from,
so you can tell whether it is current. It is a derived view: `.aphelocoma/state/tasks.json` stays the
source of truth, and the Hamilton validator *warns* — never errors — when `STATUS.md` is missing or its
stamped `seq` is behind the ledger, so a stale board never blocks a resume.

Under `visibility: tracked` the file is committed with the project; under `visibility: local` it stays
untracked along with the rest of `.aphelocoma/`.

## Ownership, drift, and recovery

Aphelocoma treats its manifests as deletion authority:

- `deploy` generates into staging, backs up collisions under the active Aphelocoma root, then writes
  the host and ownership manifest as one transaction. A failed deploy rolls back host changes.
- `undeploy` removes a generated artifact only when its current digest still matches the manifest. It
  restores a recorded collision backup after clean removal.
- Modified generated files or managed blocks are preserved and reported as drift. The manifest remains
  so you can move or reconcile the edit and retry.
- `update` verifies the current installation before replacement. Failure restores the previous tool
  and manifest byte-for-byte; success records the previous tool under
  `~/.aphelocoma/backups/install/`.
- `uninstall` first undeploys Claude and Codex. Any unresolved deployment or PATH drift stops removal
  of the tool. Recovery backups remain available after uninstall.

Use `aph doctor` before recovery work. It checks the install manifest and digest, owned PATH block,
deployment inventories and backups, host versions, legacy artifacts, Hamilton state versions, and
project privacy.

## Breaking v0.3 transition

v0.3 is a breaking reset to Hamilton only. The former second-brain/context commands, Cursor target,
sync and journaling skills, registry, and generated context views are not part of the v0.3 runtime.

Legacy data is protected:

- the default legacy directory `~/.aphelocoma/data` is not read, modified, or deleted;
- a custom legacy path supplied through the retired `APHELOCOMA_HOME` variable is also not read,
  modified, or deleted;
- `APHELOCOMA_HOME` is ignored for active storage; use `APHELOCOMA_ROOT` to relocate the v0.3
  installation.

Install, update, and uninstall can clean up only exact or proven-owned legacy global artifacts from
earlier releases. Modified or unrelated Claude/Codex configuration is preserved and reported for
manual review.

See [the v0.3 migration guide](docs/migration-v0.3.md) before upgrading.

## Development

Run the standard-library test suite and Hamilton validator:

```bash
python3 -m unittest discover -s tests -v
python3 skills/aph-hamilton/references/validate.py .
```

Public behavior in this README is indexed in
[the v0.3 documentation assertions](docs/documentation-assertions-v0.3.md).
