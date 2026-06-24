# Hamilton — Phase 2 (native parallel agents) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) or
> superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax. The gate (Task 6)
> MUST be an executed parallel cold-start — authored artifacts don't count.

**Goal:** Make Hamilton optionally run implementer roles as **real parallel Claude subagents** for
context isolation, generated on demand from the canonical roles, with an **orchestrator-owned-state**
concurrency model that keeps the shared board and ledger race-free — while sequential file-based
role-play remains the guaranteed portable default.

**Architecture:** A `sync-agents` skill mode derives a project's `.claude/agents/<role>.md` from
`references/roles/<id>.md` (frontmatter + runner preamble + inlined role). During the Implementation
phase on Claude Code, the manager role dispatches each independent `assigned` task's owner as a
subagent **in parallel**; each subagent builds its `product/` artifacts, writes its own per-instance
`ledger/agents/<role>.md`, and **returns a structured result**; the **orchestrator is the single
writer** of `state/tasks.json` and `ledger/events.jsonl`, serializing those updates so `seq` stays
monotonic and no event is lost. Everything is additive: no agents generated / non-Claude / no
disjoint tasks ⇒ the Phase-1 sequential loop runs unchanged.

**Tech Stack:** Markdown + YAML + JSONL; Claude Code subagents (the Agent/Task mechanism). No build.

## Global Constraints

- **Additive & opt-in.** Phase 2 must NOT change Phase-1 behavior when parallelism is off/unavailable.
  Sequential single-agent role-play stays the guaranteed mode (PROTOCOL §1). Never *require* parallelism.
- **Portable default.** Generation + parallel dispatch are **Claude-Code-only**. On Codex/others,
  `sync-agents` is a no-op (warn) and the run is sequential. Definition files stay tool-neutral.
- **Derived, never hand-maintained.** Generated agents come only from `references/roles/<id>.md` via
  `sync-agents`; regenerating must reproduce them. No second source of truth for roles.
- **Single-writer invariant (the core safety rule):** ONLY the orchestrator writes
  `.aphelocoma/state/tasks.json` and `.aphelocoma/ledger/events.jsonl`. Dispatched subagents NEVER
  touch those two files. Subagents write only `product/` artifacts and their own per-instance
  `.aphelocoma/ledger/agents/<role-id[#N]>.md` (distinct files ⇒ no contention).
- **Ledger schema unchanged** from Phase 1: `{"ts","seq","event","actor","task","to","note"}`, `seq`
  +1 per append, append-only; event-type vocabulary unchanged (PROTOCOL §5).
- **Parallelize only disjoint work.** The manager may dispatch tasks in parallel ONLY when their spec
  `Interfaces / files touched` (§4) are disjoint; overlapping-file tasks are sequenced. Tasks with
  unmet dependencies are not dispatched until their inputs are `done`.
- **Definition version bumps to `1.1.0`** (protocol + role-consumption change; additive/backward-
  compatible). Projects pinned at `1.0.0` that `resume` under `1.1.0` get the existing drift warning.
- **Brand/paths** per Phase 1 (Hamilton; `.aphelocoma/…` state; `product/`; definition siblings in
  `references/`). No regression of the Phase-1 rename.

## File Structure

- `skills/aph-hamilton/references/PARALLEL.md` — **new** definition doc: the orchestrator-owned-state
  protocol, the subagent structured-result schema, parallelization rules. The single source the
  orchestrator and generated agents both cite. Shipped read-only in `references/`.
- `skills/aph-hamilton/references/PROTOCOL.md` — extend §1 (execution model) to point at `PARALLEL.md`
  for the concrete mechanism; add a short Implementation-phase note in §2.4. No path/brand regression.
- `skills/aph-hamilton/references/agent-template.md` — **new**: the exact `.claude/agents/<id>.md`
  generation template (frontmatter + runner preamble + inlined-role placeholder) that `sync-agents`
  fills per role. Keeps the generation contract out of the skill prose.
- `skills/aph-hamilton/skill.md` — implement `sync-agents` (generate agents) and wire the
  Implementation phase of `start`/`resume` to dispatch-in-parallel-then-serialize when enabled.
- `skills/aph-hamilton/references/VERSION` — `1.0.0` → `1.1.0`.
- `skills/aph-hamilton/references/settings.example.yaml` — document `parallel_dispatch` semantics for
  the per-project `.aphelocoma/settings.yaml` (default off; on ⇒ parallel when agents+platform allow).
- `docs/superpowers/notes/2026-06-24-hamilton-parallel-coldstart.md` — the executed parallel-run verdict.

**Out of scope (YAGNI):** cross-task locking beyond single-writer + disjoint-file rule; retry/backoff;
non-Claude parallelism; model-routing beyond the optional `models:` map already in settings.

---

## Task 1: Author `references/PARALLEL.md` (the concurrency contract)

**Files:** Create `skills/aph-hamilton/references/PARALLEL.md`.

**Interfaces:**
- Produces (cited by Tasks 2, 3, 6): the **structured-result schema** a subagent returns, and the
  **orchestrator loop** that serializes writes. Exact shape downstream tasks depend on:
  - Subagent returns JSON: `{"task":"<id>","role":"<role-id[#N]>","status":"in_review|blocked",
    "artifacts":["product/…"],"events":[{"event":"<type>","to":"<role-id|null>","note":"<text>"}],
    "blocked_reason":"<text|null>"}`.
  - Orchestrator, per result in ascending task-id order: append each `events[]` entry to
    `events.jsonl` with the next `seq`+`ts`+`actor=role`; then set the task's `status`/`artifacts`/
    `updated` in `tasks.json`. Subagent already wrote `product/` + its own `ledger/agents/<role[#N]>.md`.

- [ ] **Step 1: Write `PARALLEL.md`** covering, in order: (a) when to parallelize (independent
  `assigned` tasks with disjoint §4 `files touched`, deps satisfied); (b) the single-writer invariant
  verbatim from Global Constraints; (c) the dispatch step (manager sends N subagents in one batch);
  (d) the subagent contract (read your `specs/<id>.md`; build under `product/`; write your own
  `ledger/agents/<role-id[#N]>.md`; **do not touch `tasks.json`/`events.jsonl`**; return the JSON
  schema above); (e) the collect+serialize step (orchestrator loop above, deterministic order, one
  `seq` sequence); (f) failure handling (a `blocked` result → orchestrator logs `blocked`, leaves task
  `assigned`, continues others); (g) the explicit fallback (no agents / non-Claude / overlapping files
  ⇒ run sequentially per PROTOCOL §3).

- [ ] **Step 2: Verify** the doc is self-consistent and tool-neutral.

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
grep -nE "CLAUDE_SKILL_DIR|company/|config/" skills/aph-hamilton/references/PARALLEL.md || echo "(clean, tool-neutral)"
grep -c "tasks.json" skills/aph-hamilton/references/PARALLEL.md   # single-writer rule referenced
grep -qi "single writer\|single-writer" skills/aph-hamilton/references/PARALLEL.md && echo "single-writer rule present"
```
Expected: clean; `tasks.json` referenced; single-writer rule present.

- [ ] **Step 3: Commit** — `git add … && git commit -m "Hamilton P2: add PARALLEL.md concurrency contract"`.

---

## Task 2: Author `references/agent-template.md` + implement `sync-agents` generation

**Files:** Create `skills/aph-hamilton/references/agent-template.md`; modify `skills/aph-hamilton/skill.md`.

**Interfaces:**
- Consumes: `references/roles/<id>.md` (role content), `sizes.yaml` (active roles), `PARALLEL.md` (the
  subagent contract to embed).
- Produces: per active role, `./.claude/agents/hamilton-<role-id>.md` in the project, with Claude
  subagent frontmatter (`name: hamilton-<role-id>`, `description`, `tools`, optional `model`) and a
  body = runner preamble + the inlined canonical role text.

- [ ] **Step 1: Write `agent-template.md`** — the exact generation template, e.g.:

```markdown
---
name: hamilton-<role-id>
description: <role title> — Hamilton crew member. Builds assigned tasks under product/ and returns a structured result. Dispatched by the Hamilton orchestrator.
tools: Read, Write, Edit, Bash, Grep, Glob
# model: optional, from .aphelocoma/settings.yaml models map
---

You are **<role title>** (`<role-id>`), a member of the Hamilton crew, dispatched to build ONE task.

## Concurrency contract (Hamilton PARALLEL.md — do not violate)
- Read your task spec at `.aphelocoma/specs/<task-id>.md` (the orchestrator gives you `<task-id>`).
- Build your deliverable in the project under `product/`. Stay within your spec's `files touched`.
- Append your human-readable log to `.aphelocoma/ledger/agents/<role-id[#N]>.md` (your file only).
- DO NOT write `.aphelocoma/state/tasks.json` or `.aphelocoma/ledger/events.jsonl` — the orchestrator
  owns those. Instead, RETURN this exact JSON as your final message:
  {"task":"<id>","role":"<role-id[#N]>","status":"in_review|blocked","artifacts":["product/…"],
   "events":[{"event":"work_started","to":null,"note":"…"},{"event":"artifact_written","to":null,"note":"…"},
   {"event":"handoff","to":"<reviewer-role|null>","note":"…"}],"blocked_reason":null}

## Your role (canonical — from references/roles/<role-id>.md)
<INLINED ROLE FILE CONTENT>
```

- [ ] **Step 2: Implement the `sync-agents` mode in `skill.md`** (replace the Phase-1 stub) with exact
  generation steps: resolve active roles from `hamilton.json`; for each, read
  `<skill>/references/roles/<id>.md`, fill `<skill>/references/agent-template.md`, write
  `./.claude/agents/hamilton-<id>.md`; for multi-instance roles write one file per instance
  (`hamilton-<id>-1`, `-2`); apply the optional `models:` map from `.aphelocoma/settings.yaml`; on
  non-Claude platforms, print "sync-agents is Claude-Code-only; running sequentially" and write nothing.

- [ ] **Step 3: Verify** the skill documents generation + the no-op fallback and never lets agents
  write the owned files.

```bash
grep -niE "sync-agents|\.claude/agents|hamilton-" skills/aph-hamilton/skill.md | head
grep -qi "Claude-Code-only\|non-Claude" skills/aph-hamilton/skill.md && echo "fallback documented"
grep -qi "do not write .*tasks.json\|orchestrator owns" skills/aph-hamilton/references/agent-template.md && echo "single-writer embedded in template"
```
Expected: all present.

- [ ] **Step 4: Commit** — `git commit -m "Hamilton P2: agent-template + sync-agents generation"`.

---

## Task 3: Wire the orchestrator (parallel Implementation phase) into `skill.md` + PROTOCOL §1

**Files:** Modify `skills/aph-hamilton/skill.md` (the `start`/`resume` Implementation phase), 
`skills/aph-hamilton/references/PROTOCOL.md` (§1 + a §2.4 note), 
`skills/aph-hamilton/references/settings.example.yaml` (document `parallel_dispatch`).

**Interfaces:**
- Consumes: `PARALLEL.md` schema + loop (Task 1), generated agents (Task 2).
- Produces: the runtime behavior — manager parallelizes disjoint `assigned` tasks, collects results,
  serializes `tasks.json`+`events.jsonl` writes.

- [ ] **Step 1: Extend PROTOCOL §1** — replace the generic "optional acceleration" paragraph with a
  pointer: parallel implementer dispatch is defined in `PARALLEL.md`; it is opt-in
  (`.aphelocoma/settings.yaml: parallel_dispatch: true`), Claude-Code-only, and the system MUST remain
  runnable sequentially. Add one line to §2.4 (Implementation): "If parallel dispatch is enabled and
  ≥2 `assigned` tasks have disjoint file scopes, the manager dispatches them per `PARALLEL.md`;
  otherwise work them sequentially per §3."

- [ ] **Step 2: Wire `skill.md` Implementation phase** — document that when (Claude Code) AND
  (`parallel_dispatch: true`) AND (`.claude/agents/` present) AND (≥2 disjoint `assigned` tasks), the
  orchestrator: dispatches each owner's `hamilton-<role>` subagent in parallel with its `<task-id>`;
  awaits all structured results; then serially appends their `events[]` to `events.jsonl` (monotonic
  `seq`) and updates `tasks.json`. Note the proven fallback: if a generated agent isn't yet selectable
  as a subagent type, dispatch a generic subagent with the agent file's content injected (parallelism
  must not depend on registration timing). Otherwise run sequentially.

- [ ] **Step 3: Document `parallel_dispatch`** in `settings.example.yaml` (default `false`; effective
  only on Claude Code with generated agents).

- [ ] **Step 4: Verify** no Phase-1 regression + the single-writer wiring is explicit.

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
grep -nE "\b(compan(y|ies)|harness)\b" skills/aph-hamilton/references/PROTOCOL.md skills/aph-hamilton/skill.md || echo "(no brand regression)"
grep -qi "PARALLEL.md" skills/aph-hamilton/references/PROTOCOL.md && echo "PROTOCOL points to PARALLEL.md"
grep -qi "sequentially\|sequential" skills/aph-hamilton/skill.md && echo "sequential fallback retained"
```
Expected: all present.

- [ ] **Step 5: Commit** — `git commit -m "Hamilton P2: orchestrator-owned-state parallel Implementation wiring"`.

---

## Task 4: Version bump to 1.1.0 + redeploy

**Files:** Modify `skills/aph-hamilton/references/VERSION`.

- [ ] **Step 1: Bump** `VERSION` to `1.1.0`.

```bash
printf '1.1.0\n' > skills/aph-hamilton/references/VERSION
```

- [ ] **Step 2: Redeploy** both tools (same generator as Phase 1 — valid frontmatter; Claude gets the
  single-quoted `argument-hint`, Codex none) so the installed skill carries `PARALLEL.md`,
  `agent-template.md`, and `VERSION 1.1.0`.

- [ ] **Step 3: Verify** installed `VERSION` is `1.1.0` and the new references shipped.

```bash
cat ~/.claude/skills/aph-hamilton/references/VERSION
test -f ~/.claude/skills/aph-hamilton/references/PARALLEL.md && echo "PARALLEL.md shipped (claude)"
test -f ~/.codex/skills/aph-hamilton/references/PARALLEL.md && echo "PARALLEL.md shipped (codex)"
```
Expected: `1.1.0`; both shipped.

- [ ] **Step 4: Commit** — `git commit -m "Hamilton P2: bump definition version to 1.1.0"`.

---

## Task 5: Generation smoke test (structural, fast — before the full run)

**Files:** none (throwaway project under scratchpad).

- [ ] **Step 1:** In a fresh throwaway project, bootstrap a multi-implementer size and run
  `sync-agents`; confirm one well-formed `.claude/agents/hamilton-<role>.md` per active implementer
  (valid frontmatter, embedded single-writer contract, inlined role text). Assert the generated files
  do NOT instruct writing `tasks.json`/`events.jsonl`.

```bash
# after a `start … startup` + sync-agents in the throwaway project P:
for f in "$P"/.claude/agents/hamilton-*.md; do
  head -1 "$f" | grep -q '^---' && echo "FM ok: $(basename "$f")" || echo "FM MISSING: $f"
  grep -qi "do not write .*tasks.json\|orchestrator owns" "$f" || echo "  WARN no single-writer rule in $(basename "$f")"
done
```
Expected: each implementer role has a frontmattered agent file carrying the single-writer rule.

- [ ] **Step 2: Commit** any template fixes the smoke test forces.

---

## Task 6: Parallel cold-start verification (the gate — executed, not authored)

**Files:** throwaway project; produces `docs/superpowers/notes/2026-06-24-hamilton-parallel-coldstart.md`.

- [ ] **Step 1: Run an executed parallel cold-start.** Fresh agent, a size that yields ≥2 independent
  disjoint implementer tasks (e.g. `startup` building two non-overlapping product files), with
  `.aphelocoma/settings.yaml: parallel_dispatch: true`. The manager generates agents, dispatches ≥2
  implementers in parallel, collects results, serializes state. Keep products tiny.

- [ ] **Step 2: Assert state integrity (the Phase-2 spec check) mechanically:**

```bash
P=<throwaway>
# (i) ≥2 implementers actually ran in parallel — distinct actors did work_started close in time:
grep -E '"event":"work_started"' "$P/.aphelocoma/ledger/events.jsonl"
# (ii) ledger STILL schema-valid + strictly monotonic seq with NO duplicates and NO gaps:
python3 - "$P/.aphelocoma/ledger/events.jsonl" <<'PY'
import json,sys
seqs=[]; keys={"ts","seq","event","actor","task","to","note"}
for l in open(sys.argv[1]):
    l=l.strip()
    if not l: continue
    e=json.loads(l); assert keys.issubset(e), f"missing keys: {keys-set(e)}"; seqs.append(e["seq"])
ok = seqs==list(range(1,len(seqs)+1))
print("seq PASS" if ok else f"seq FAIL: {seqs}")
PY
# (iii) every task in tasks.json reached a terminal state and matches ledger (no lost updates):
python3 -c "import json;d=json.load(open('$P/.aphelocoma/state/tasks.json'));print('phases:',d['phase'],'tasks:',[(t['id'],t['status']) for t in d['tasks']])"
# (iv) single-writer honored: no event/task references a write by a dispatched subagent out of order
grep -c '"event":"project_completed"' "$P/.aphelocoma/ledger/events.jsonl"
```
Expected: ≥2 `work_started` by different actors; `seq PASS` (no dup/gap — proves no race corrupted the
append-only ledger); all tasks terminal; `project_completed` present; phase `done`.

- [ ] **Step 3: Gate.** Phase 2 is "working" ONLY if (a) ≥2 implementers ran as parallel subagents,
  (b) the ledger is schema-valid with strictly monotonic gap-free `seq`, (c) no task update was lost,
  (d) the sequential fallback still works when `parallel_dispatch` is off. If any fail, fix the
  responsible definition/skill file and re-run — do not hand-patch the run.

- [ ] **Step 4: Record the verdict** in the parallel-coldstart note (commands + outputs as evidence)
  and **commit**.

- [ ] **Step 5:** Use **superpowers:finishing-a-development-branch** to integrate.

---

## Self-Review

**Spec coverage (Phasing §Phase 2 + §Native agents):**
1. `sync-agents` generates `.claude/agents/<role>.md` derived from `references/roles/` → **Task 2**
   (template + generation), structural check **Task 5**. ✓
2. Orchestrator-owned-state parallelism (manager dispatches; single writer of `tasks.json`+
   `events.jsonl`; subagents return structured results + write own role log) → **Task 1** (contract)
   + **Task 3** (wiring). ✓
3. Fallback: non-Claude / off ⇒ sequential → Global Constraints + **Task 2 Step 2** + **Task 3 Step 2**. ✓
4. Cold-start test the parallel path; verify no state corruption (orchestrator-owned writes) →
   **Task 6** (executed gate with dup/gap-free `seq` assertion). ✓
5. Version pin reflects the definition change → **Task 4** (1.1.0). ✓

**Placeholder scan:** the structured-result schema, the agent template, and the orchestrator loop are
spelled out verbatim; verification steps give exact commands + expected output. The single
`<INLINED ROLE FILE CONTENT>` marker is an explicit generation substitution, not a TODO.

**Type/contract consistency:** the result JSON (`task`/`role`/`status`/`artifacts`/`events`/
`blocked_reason`) is defined once in Task 1 and reused identically in Task 2's template and Task 6's
assertions. `hamilton-<role-id>` naming, the single-writer invariant, and `parallel_dispatch` are used
consistently across Tasks 1–6.

**Risks / decisions:** (1) **Inline role content** into generated agents (vs path refs) — robust, no
skill-dir resolution needed inside a subagent (proven in Phase 1). (2) **Parallelism via prompt-
injection is the primary mechanism**; native `subagent_type` selection is a bonus, because Phase 1
showed registry entries can be stale within the generating session. (3) **Disjoint-file rule** reuses
the existing §4 `files touched` contract to avoid product-file write conflicts the orchestrator can't
serialize. (4) Bump **1.1.0** (additive) so `resume` drift-warns 1.0.0 projects — which also finally
exercises the version-drift path deferred from Phase 1.
