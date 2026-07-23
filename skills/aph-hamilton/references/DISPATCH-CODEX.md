# DISPATCH-CODEX — parallel dispatch on Codex via headless workers

Codex gives Hamilton two ways to run parallel Implementation. The **default is `codex exec` fan-out**
— one background worker per task, results collected from files — because it is stable, core CLI:
`--output-schema` enforces the result contract and `--sandbox read-only` enforces the reviewer's
scope. The experimental **collab tools** (`spawn_agent`/`wait_agent` — "Native collab backend" at the
end) are used ONLY per the selection order below — never improvise a dispatch through them just
because they appear in the toolbox. Everything else — the single-writer rule, the subagent contract,
collect + serialize, the scope check — is `PARALLEL.md`, unchanged.

All `.aphelocoma/dispatch/` content is transient regardless of project visibility. Raw prompts,
result files, and worker logs are never committed or copied into durable ledger notes; only compact
redacted result summaries are serialized.

## Backend selection (decide at Checkpoint 3, announce the choice + why)

In order, from `.aphelocoma/settings.yaml` `dispatch:` (absent = `auto`):

1. `sequential` → sequential single-role turns (PROTOCOL §3). Never dispatch.
2. `exec` → `codex exec` fan-out only; if its preflight fails → sequential.
3. `collab` → the collab tools (advisor's explicit opt-in); if the session doesn't have them →
   `codex exec` fan-out → sequential.
4. `auto` (the default) → `codex exec` fan-out if its preflight passes; **else**, if the session has
   the collab tools, use them as the fallback rung (say so — the advisor is choosing build style at
   CP3 anyway); else sequential.

Sequential (PROTOCOL §3) stays the guaranteed floor on every rung.

Two properties make this backend *stricter* than prompt-only discipline:

- `--output-schema` pins the worker's final message to the result schema (`result.implementer.schema.json`
  / `result.reviewer.schema.json`, beside this file) — the CLI enforces the JSON contract.
- Reviewer workers run with `--sandbox read-only` — "the reviewer writes nothing" is enforced by the
  sandbox, not by prose (the Codex analog of dropping `Write`/`Edit` on Claude Code).

## Preflight for `codex exec` fan-out (once, at Checkpoint 3)

1. **`codex` is runnable:** `codex --version` succeeds from the orchestrator's shell.
2. **Workers can reach the API.** If the orchestrator itself runs inside a Codex sandbox, a spawned
   `codex exec` inherits it and needs network to talk to the model. Either the user's
   `~/.codex/config.toml` has `[sandbox_workspace_write] network_access = true`, or run the fan-out
   command with escalated permissions (the orchestrator session is interactive — request approval for
   the one dispatch command). If neither is possible, preflight fails.

Report the preflight verdict in the CP3 options so the advisor knows which backend selection rung
applied and why.

## Dispatch (this replaces PARALLEL.md "The loop" step 2 on Codex)

For each task in the selected batch (disjoint `files touched`, inputs `done` — PARALLEL.md step 1):

1. **Assemble the worker prompt** at `.aphelocoma/dispatch/<task-id>--<role-id>/prompt.md`. Use
   `agent-template.md` exactly as `sync-agents` does, minus the Claude frontmatter: pick the
   **IMPLEMENTER** body (or **REVIEWER** body for a look-only role), fill `{{ROLE_ID}}`,
   `{{ROLE_TITLE}}`, `{{ROLE_BODY}}` (the verbatim role file), and append one line:
   `Your task: <task-id>.` Model/effort are NOT part of the prompt — they are flags (below).
   Assemble **on disk** (shell concatenation of the template body + role file), not by reading the
   role bodies into your own context — the workers' instructions shouldn't cost the orchestrator's
   window anything.

2. **Launch the worker in the background**, from the project root:

   ```bash
   mkdir -p .aphelocoma/dispatch/<task-id>--<role-id>
   codex exec \
     -C "$(pwd)" \
     --skip-git-repo-check \
     --sandbox workspace-write \
     --output-schema "<skill>/references/result.implementer.schema.json" \
     --output-last-message ".aphelocoma/dispatch/<task-id>--<role-id>/result.json" \
     "$(cat .aphelocoma/dispatch/<task-id>--<role-id>/prompt.md)" \
     > ".aphelocoma/dispatch/<task-id>--<role-id>/worker.log" 2>&1 &
   ```

   - **Model (per role):** if `.aphelocoma/settings.yaml` `models:` maps this role (or `default`), add
     `-m <model>`; otherwise omit — the worker uses the user's default. On Codex the map's values are
     **Codex model names** (the map is interpreted by whatever platform runs Hamilton).
   - **Effort (per role):** if `effort:` maps this role, add `-c model_reasoning_effort=<value>`,
     mapping Hamilton's scale onto Codex's (`low|medium|high`; `xhigh`/`max` → `high`).
   - **Reviewers:** use `--sandbox read-only` and `result.reviewer.schema.json` instead.

3. **Announce the batch (role visibility).** Exec workers are background processes — the UI shows
   command lines, not named agents — so the advisor's view of *who* is working comes from you. Before
   launching, print a **dispatch table**: `task → role → model → effort` (one row per worker; each
   worker is a full Codex session against the user's quota, so the table doubles as the cost notice).
   The role-tagged dispatch paths (`<task-id>--<role-id>`) keep the on-screen command lines readable
   too.

4. **Cap concurrency.** Launch at most `max_parallel` workers at once (settings key; default 4), `wait`
   for the slice, then launch the next.

5. **`wait`** for all workers in the batch. While waiting and when reporting, narrate by role and task
   ("backend-developer is building T-2"), never by process id or path alone.

## Collect (feeds PARALLEL.md step 4, verbatim)

For each task, read `.aphelocoma/dispatch/<task-id>--<role-id>/result.json`:

- **Present and valid** → validate it against the pinned schema and confirm its `task` and exact
  role/instance match the dispatch; for a reviewer also confirm the role/instance differs from the
  task builder. Hand it to the serialize loop
  (PARALLEL.md step 4: replay-safety check, append events with the next `seq`, update the board).
  Conditional schema rules reject contradictory results (`blocked` without its exact blocked
  lifecycle, `in_review` without its ordered work/artifact/handoff tuple and targets or with a blocked
  reason/event, reviewer
  `pass` with a blocking finding, or reviewer `fail` without one).
- **Missing, empty, or unparseable** (worker crashed, timed out, or died mid-run) → treat as
  `"status": "blocked"` with `blocked_reason` = a one-liner from the tail of `worker.log`, and a single
  `blocked` event. One dead worker never corrupts the batch (PARALLEL.md "Failure & honesty").

Then run the **scope check** exactly as PARALLEL.md step 4 defines it. It matters *more* on Codex:
implementer workers are only prompt-scoped to their spec's `files touched` (no per-role tool scoping),
so the post-batch `git diff` against the declared union is the enforcement backstop.

**Cleanup:** after the batch is serialized and committed (PROTOCOL §5.5), delete `.aphelocoma/dispatch/`
— it is transient scratch; the durable audit trail is the ledger. Never commit `dispatch/`.

## Reviewers at CP4 (PARALLEL.md step 5)

Per-task review parallelizes the same way: one `--sandbox read-only` worker per `in_review` task, the
REVIEWER prompt body, `result.reviewer.schema.json`. The orchestrator logs each `critique` (tier:
`subagent` — a dispatched fresh-context worker) plus `review_passed`/`review_failed`, and writes the
reviewer's ledger note itself, as always.

## Native collab backend (opt-in or fallback — NOT the default)

Some Codex sessions expose experimental in-session multi-agent tools — `spawn_agent`, `wait_agent`,
`send_message`, `close_agent` (the `multi_agent_v2`/`collab` feature). Hamilton uses them **only** on
the selection rungs above: `dispatch: collab` (the advisor opted in) or the `auto` fallback when the
`codex exec` preflight fails. **Do not dispatch through spawn tools outside those two cases**, even
though they may be visible in the session — they are experimental and their behavior can change
between Codex releases; `codex exec` is the supported default. When they ARE the chosen backend:
same PARALLEL.md contract, no process management, one shared session against quota.

Rules specific to this backend:

- **Always label the worker.** `aph deploy codex` generates the **named crew roles**: one
  `[agents.hamilton-<role-id>]` per role in `~/.codex/config.toml` (a managed block marked
  `# >>> aphelocoma hamilton crew >>>` … `# <<< aphelocoma hamilton crew <<<`) pointing at
  `~/.codex/agents/hamilton-<role-id>.toml` — display nickname (the role title) + the implementer or
  reviewer contract as `developer_instructions`, derived from `agent-template.md` like the Claude
  crew. Spawn with `agent_type: "hamilton-<role-id>"` so the thread carries the role name instead of
  a bare thread id. If the roles are missing (deploy not run), still make the **first line** of every
  spawn message a role tag the UI can surface in previews:
  `[hamilton:<role-id>] task <task-id> — <one-line title>`.
- **Per-role model/effort at spawn time.** Pass `model` / `reasoning_effort` as `spawn_agent` args
  from the project's `.aphelocoma/settings.yaml` maps (Codex model names; effort capped at `high`) —
  they are deliberately NOT baked into the generated role files, so per-project overrides apply
  without regenerating anything.
- **Fresh context only — never `fork_context`.** Spawn every worker with a clean thread (the default);
  a forked copy of the orchestrator's conversation would break worker independence (a CP4 reviewer
  that inherits the builder's context is not an independent reviewer) and bloats nothing for gain —
  workers read their spec and conventions from disk.
- **Narrate by role, never by thread id.** In your own status text say "waiting on the qa-engineer
  review of T-3", not "waiting for 019f47…". Keep a private thread-id → role map for the batch.
- **Contract enforcement is on you.** There is no `--output-schema` here: the generated role
  instructions demand the exact result JSON (the schemas beside this file are the source of truth) —
  validate each returned result yourself; invalid → one re-ask, then treat as `blocked`.
- **Reviewers are prompt-scoped only** (no read-only sandbox per spawn) — the REVIEWER body's
  "write nothing" rule plus the post-batch scope check are the guardrails.
- Tell every spawned worker it may NOT spawn agents itself, and `close_agent` each worker after its
  result is serialized.

(A session restart may be needed for Codex to pick up freshly generated roles; if the UI still shows
raw thread ids on spawn lines, that is the installed Codex version's rendering — updating Codex helps,
and the prompt-tag + role narration above keep the run readable regardless.)
