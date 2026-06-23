# Hamilton — Phase 1 (MVP, portable) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, recommended here — the rename/remap is delicate prose surgery that benefits from full repo context) for Tasks 1–7 & 9; the cold-start verification in **Task 8 MUST use a fresh, context-less subagent** (that *is* the test). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the relocated `company/`-vintage prototype under `skills/aph-hamilton/` into a Hamilton-branded, install-once / run-anywhere skill that reads its definition from beside its own `SKILL.md` and bootstraps a thin per-project `.aphelocoma/`, proven by an executed cold-start on Claude and a confirmed definition-reach on Codex.

**Architecture:** Two layers + a bridge. **Definition** (protocol, roles, sizes — read-only) ships inside the skill's `references/` and is read at runtime via the skill's own install dir. **Per-project state** (`.aphelocoma/{hamilton.json,state,ledger,specs}`) lives in the target project. The **bridge** is `skill.md`: it alone owns skill-dir resolution and points the agent at the definition (siblings in `references/`) and the project state (`./.aphelocoma/`). The product being built lives in the project proper (repo root or `./product`), never in `.aphelocoma/`.

**Tech Stack:** Markdown + YAML + JSONL. No build, no runtime, no deps. Git is the database. Verification tooling: `grep`, `jq`/`python3 -c`, and a real `codex exec` + a fresh Claude subagent for cold-start.

## Global Constraints

Every task implicitly includes this section.

- **Brand:** System = **Hamilton**. Command/skill = `/aph-hamilton`. The terms **"company" and "OS" are retired as brand labels.** Use "crew"/"roles"/"team" descriptively.
- **Skill identity (do not change):** `name: aph-hamilton`, `type: manual`, `arguments: "[start \"<brief>\" <solo|startup|mid|big|custom:[roles]> | resume | status | sync-agents]"`. `sync-agents` is Phase 2.
- **No vendored copies of the definition.** Projects record only the *version* they ran (`hamilton.json.definition_version`), never a copy of `references/`.
- **`references/VERSION` = `1.0.0`** — the Hamilton *definition* version. Independent of aphelocoma's own VERSION. Bump only on protocol/role changes.
- **Ledger schema (verbatim):** one JSON object per line in `.aphelocoma/ledger/events.jsonl`:
  `{"ts":"<iso>","seq":<int>,"event":"<type>","actor":"<role-id>","task":"<id|null>","to":"<role-id|null>","note":"<text>"}`. `seq` increases by exactly 1 per append (read last line for next). Append-only; corrections are new events.
- **Canonical phases (one set, in order):** `kickoff`, `discovery`, `planning`, `breakdown`, `implementation`, `review`, `integration`, `done`.
- **§7 coverage is mandatory and unprompted:** when a phase needs a function no active role fills (e.g. no QA in `solo`), the nearest senior/leadership role covers it and emits the covered role's events.
- **Locked vocabulary replacements** (per-occurrence judgment, never blind `sed` on the word "company"):
  | Old | New |
  |---|---|
  | "the company" / "this `company/` directory" / "a company" (the org) | "the crew" (the team of roles) **or** "Hamilton" (the system) — by sense |
  | "company size" / "company sizes" | "crew size" / "size preset" |
  | "companies" (e.g. "small companies") | "crews" / "teams" |
  | "the harness" / "the OS" / "operating system" (as brand) | "Hamilton" / "the Hamilton definition" / "the system" |
  | "company/" path prefix | (removed — see path-remap) |
  - Keep "crew/team/roles" as ordinary descriptive nouns. Do **not** rename event types, role IDs, phase names, or the word "product".
- **Locked path-remap** (the two-layer split):
  | Old (flat `company/`) | New |
  |---|---|
  | `state/…` | `.aphelocoma/state/…` |
  | `ledger/…` | `.aphelocoma/ledger/…` |
  | `specs/…` | `.aphelocoma/specs/…` |
  | `config/sizes.yaml` | `sizes.yaml` (sibling inside the definition) |
  | `config/roles.index.md` | `roles.index.md` (sibling) |
  | `config/settings.yaml` (optional live) | `.aphelocoma/settings.yaml` (optional, per-project; example at `references/settings.example.yaml`) |
  | `roles/<id>.md` | `roles/<id>.md` — **unchanged** (sibling inside the definition) |
  | `PROTOCOL.md` | `PROTOCOL.md` — **unchanged** (sibling) |
  | `product/` | `product/` — **kept as a defined term**: the product location in the *project* (repo root, or a `product/` subdir) |
- **Resolution idiom (skill.md only; the definition files never name a skill-dir variable):**
  > The Hamilton definition lives in the `references/` directory **beside this `SKILL.md`** (the skill's own install dir). **Claude Code:** `${CLAUDE_SKILL_DIR}/references/`. **Codex / other tools:** resolve it relative to *this* `SKILL.md`'s location — its parent directory's `references/` (the tool tells you this skill file's path; use its folder). Definition files (`PROTOCOL.md`, `roles/<id>.md`, `sizes.yaml`, `VERSION`) are siblings inside that `references/`. Per-project state (`.aphelocoma/…`) lives in the **current project**, not the definition.
  - **Why this works on both (verified 2026-06-23):** on Claude `${CLAUDE_SKILL_DIR}` resolves to the install dir; on Codex `CLAUDE_SKILL_DIR` is *unset*, but Codex injects this skill's `SKILL.md` absolute path into context, so the agent derives the dir via `dirname(SKILL.md)`. Deploy physically copies `references/` next to `SKILL.md` on **both** tools, so "the `references/` beside this file" is always true. No deploy-infra change and no hardcoded Codex path required.

---

## File Structure

**Definition (read-only, rebranded + remapped):**
- `skills/aph-hamilton/references/PROTOCOL.md` — the coordination protocol. Heaviest rewrite (mental model + path-remap + anchor note).
- `skills/aph-hamilton/references/ABOUT.md` — the definition's README. Rebrand; retire the "delete `_smoketest`" section; point at `examples/todo-solo/`.
- `skills/aph-hamilton/references/START.reference.md` — kickoff reference. Rebrand; defer to `/aph-hamilton` as the canonical entrypoint.
- `skills/aph-hamilton/references/roles.index.md` — role catalog. Rebrand the intro lines.
- `skills/aph-hamilton/references/sizes.yaml` — size presets. Rebrand comments.
- `skills/aph-hamilton/references/settings.example.yaml` — optional config example. Rebrand; fix `product_dir` default + settings path.
- `skills/aph-hamilton/references/roles/*.md` (27) — path-remap `state/`→`.aphelocoma/state/`, `specs/`→`.aphelocoma/specs/`; fix "small companies" in `cto.md`.
- `skills/aph-hamilton/references/VERSION` — already `1.0.0`; leave.

**Bridge:**
- `skills/aph-hamilton/skill.md` — finalize resolution idiom + start/resume/status + version-pin wording.
- `skills/aph-hamilton/metadata.yaml` — verify only.

**Per-project templates (rebranded):**
- `skills/aph-hamilton/templates/aphelocoma/state/brief.md` — rebrand stub; keep `status: no-active-project` resume signal.
- `skills/aph-hamilton/templates/aphelocoma/state/roadmap.md` — rebrand stub.
- `skills/aph-hamilton/templates/aphelocoma/state/tasks.json` — already clean; leave.
- `skills/aph-hamilton/templates/aphelocoma/ledger/events.jsonl` — ships **empty** (0 bytes); leave (seeding would break monotonic `seq`).
- `skills/aph-hamilton/templates/aphelocoma/hamilton.json` — finalize field comments to match what `start` writes.

**Example (refresh last, non-blocking):**
- `skills/aph-hamilton/examples/todo-solo/**` — historical flat-layout run; refresh from the Task 8 cold-start, rewrite `NOTE.md`.

**Out of scope for Phase 1:** `sync-agents` generation, `adapters/*/overrides/aph-hamilton.yaml` (only if Task 7 proves a tweak is needed), `core/projects/registry.json` tie-in.

---

## Task 0: Branch + verification helpers

**Files:** none (git + scratch).

- [ ] **Step 1: Create a feature branch** (we are on `main`, the default branch)

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
git checkout -b hamilton-phase-1
git status
```
Expected: `On branch hamilton-phase-1`; the untracked `skills/aph-hamilton/`, `docs/.../2026-06-23-hamilton-*.md`, `AGENTS.md`, `.omc/` still listed.

- [ ] **Step 2: Record the legacy-vocabulary baseline** (the "red" state the rename will clear)

```bash
grep -rinE "\b(compan(y|ies)|harness)\b|\bOS\b" skills/aph-hamilton/references skills/aph-hamilton/templates | grep -v 'examples/' | wc -l
```
Expected: a non-zero count (currently ~40+). Task 1–4 drive the non-example count to **0**.

---

## Task 1: Rewrite `PROTOCOL.md` (brand + two-layer remap + anchor note)

**Files:**
- Modify: `skills/aph-hamilton/references/PROTOCOL.md`

**Interfaces:**
- Consumes: the Global Constraints vocabulary + path-remap + phase list.
- Produces: the canonical protocol every role and the skill reference. Downstream tasks rely on these exact anchored paths: definition siblings named bare (`roles/<id>.md`, `sizes.yaml`); project state as `.aphelocoma/state/tasks.json`, `.aphelocoma/specs/<id>.md`, `.aphelocoma/ledger/events.jsonl`, `.aphelocoma/ledger/agents/<role>.md`; product as `product/` (defined term).

- [ ] **Step 1: Replace §title + §0 mental model.** Set the H1 to `# PROTOCOL — How the Hamilton crew runs` and rewrite §0 to the two-layer model. New §0 text:

```markdown
# PROTOCOL — How the Hamilton crew runs

This document is the operating manual for **Hamilton** — a portable, file-based crew of
role-agents. Any coding agent can run the crew by reading this file and following it. It
depends on **no platform-specific features** — only the ability to read and write files.

## 0. Mental model

- **Hamilton's definition** (this protocol, the `roles/`, and `sizes.yaml`) is installed
  once and read-only. Paths named bare below — `roles/<id>.md`, `sizes.yaml`,
  `roles.index.md` — are **siblings of this file inside the definition** (the skill's
  `references/`).
- **Per-project state** lives in a `.aphelocoma/` folder in the project you are building.
  Paths below that begin `.aphelocoma/…` are there.
- **The product** (the software being built) lives in the **project proper** — the repo
  root, or a `product/` subdirectory. Below, `product/` names that location.
- You, the running agent, **adopt one role at a time** (see `roles/`), do that role's
  work, record it, and hand off — exactly like an employee.
- Two records are kept and must never be conflated:
  - **Live state** — `.aphelocoma/state/tasks.json` (+ `.aphelocoma/state/roadmap.md`,
    `.aphelocoma/state/brief.md`): the *current* truth (what exists, who owns what, status).
  - **History** — `.aphelocoma/ledger/events.jsonl` (+ `.aphelocoma/ledger/agents/<role>.md`):
    an *append-only* record of what happened. See §5.
```

- [ ] **Step 2: Remap §1 execution model.** Replace the `config/settings.yaml` reference: parallel toggle now reads `.aphelocoma/settings.yaml` (optional; `parallel_dispatch: true`), and keep the "MUST remain fully runnable sequentially" rule. Mark parallel as available on platforms that can spawn subagents (Phase 2 enables generation).

- [ ] **Step 3: Remap §2 phases.** Change "Choose a company size (`config/sizes.yaml`)" → "Choose a **crew size** (`sizes.yaml`) or a custom role list". Change every `state/…`, `specs/…`, `product/…` reference to `.aphelocoma/state/…`, `.aphelocoma/specs/…`, `product/…`. Phase names unchanged.

- [ ] **Step 4: Remap §3–§8.** Apply the path-remap table to every `state/`, `ledger/`, `specs/` occurrence (→ `.aphelocoma/…`); leave `roles/<id>.md`, `product/`, event types, status lifecycle, and §7 coverage rules intact. In §7 "Stay in lane", change "Do not modify the harness's own role/protocol files" → "Do not modify Hamilton's own definition files (`references/`)".

- [ ] **Step 5: Verify — no legacy labels, correct anchors, all state paths namespaced**

```bash
grep -nE "\b(compan(y|ies)|harness)\b|\bOS\b|config/" skills/aph-hamilton/references/PROTOCOL.md   # expect: no output
grep -nE "(^|[^.])\b(state|ledger|specs)/" skills/aph-hamilton/references/PROTOCOL.md               # expect: no output (all are .aphelocoma/-prefixed)
grep -c "\.aphelocoma/" skills/aph-hamilton/references/PROTOCOL.md                                   # expect: a healthy count (>10)
```
Expected: first two commands print nothing; third prints a number > 10.

- [ ] **Step 6: Commit**

```bash
git add skills/aph-hamilton/references/PROTOCOL.md
git commit -m "Hamilton: rebrand + two-layer path remap in PROTOCOL.md"
```

---

## Task 2: Rebrand the definition support docs

**Files:**
- Modify: `skills/aph-hamilton/references/ABOUT.md`
- Modify: `skills/aph-hamilton/references/START.reference.md`
- Modify: `skills/aph-hamilton/references/roles.index.md`
- Modify: `skills/aph-hamilton/references/sizes.yaml`
- Modify: `skills/aph-hamilton/references/settings.example.yaml`

**Interfaces:**
- Consumes: Task 1's anchored path vocabulary.
- Produces: human-facing definition docs consistent with the skill entrypoint.

- [ ] **Step 1: Rewrite `ABOUT.md`** as the definition's README. H1 → `# Hamilton — a portable, file-based crew of role-agents`. Replace "This `company/` directory turns any coding agent into a small software organization" → Hamilton framing. Change "Company sizes" → "Crew sizes". Replace the **entire** "Note on the example run / delete `company/_smoketest`" section with:

```markdown
## Example run

`examples/todo-solo/` is a **real, executed reference run** — a fresh agent was handed only
the kickoff `/aph-hamilton start "a simple todo list app" solo` and ran it unaided. Browse it
to see exactly what gets written under `.aphelocoma/` and where the product lands. It ships
with the skill as a reference and is not part of any live project.
```
Update the directory map to show the two-layer split (definition `references/` vs project `.aphelocoma/`).

- [ ] **Step 2: Rewrite `START.reference.md`.** Replace the "paste this prompt into `company/PROTOCOL.md`" flow with the skill entrypoint as canonical:

```markdown
# START — kickoff reference

The canonical entrypoint is the **`/aph-hamilton`** skill:

    /aph-hamilton start "<what to build>" <solo | startup | mid | big | custom:[role-id, ...]>

`start` bootstraps `.aphelocoma/` in the current project, then runs the protocol
(Kickoff → Discovery → Plan & Roadmap → Breakdown & Assign → Implementation → Review/QA →
Integration), adopting one role at a time, building the product in the project, keeping
`.aphelocoma/state/tasks.json` current, and appending every action to `.aphelocoma/ledger/`.

To resume: `/aph-hamilton resume`.  To inspect: `/aph-hamilton status`.
```
Keep the crew-size menu table but retitle to "Crew size menu" and change "Company size:" → "Crew size:".

- [ ] **Step 3: Rebrand `roles.index.md`.** Change "Every role the harness can activate. A company **size preset**…" → "Every role Hamilton can activate. A **crew size preset** (see `sizes.yaml`)…". Leave the table, role IDs, and `../roles/<role-id>.md` reference intact.

- [ ] **Step 4: Rebrand `sizes.yaml` comments.** "Company-size presets" → "Crew-size presets"; "one agent wears all hats" stays; in the notes, "an active size lacks a role" stays; no key/value changes (presets and role IDs unchanged).

- [ ] **Step 5: Rebrand `settings.example.yaml`.** Fix the product-dir comment default from `./company/product` → `./product` (the project's product dir). Fix the parallel comment to reference `.aphelocoma/settings.yaml`. Keep the model-map example. Replace "the harness" → "Hamilton" throughout.

- [ ] **Step 6: Verify**

```bash
grep -rinE "\b(compan(y|ies)|harness)\b|\bOS\b|_smoketest|company/" \
  skills/aph-hamilton/references/ABOUT.md \
  skills/aph-hamilton/references/START.reference.md \
  skills/aph-hamilton/references/roles.index.md \
  skills/aph-hamilton/references/sizes.yaml \
  skills/aph-hamilton/references/settings.example.yaml
```
Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add skills/aph-hamilton/references/ABOUT.md skills/aph-hamilton/references/START.reference.md skills/aph-hamilton/references/roles.index.md skills/aph-hamilton/references/sizes.yaml skills/aph-hamilton/references/settings.example.yaml
git commit -m "Hamilton: rebrand definition support docs (ABOUT, START, index, sizes, settings)"
```

---

## Task 3: Path-remap the 27 role files

**Files:**
- Modify: `skills/aph-hamilton/references/roles/*.md` (all 27)

**Interfaces:**
- Consumes: Task 1's path-remap (state/ → .aphelocoma/state/, specs/ → .aphelocoma/specs/).
- Produces: role definitions whose Inputs/Outputs name the correct per-project paths.

- [ ] **Step 1: Apply the unambiguous path-prefix remap across all role files.** These prefixes only ever mean per-project state, so a bounded `sed` is safe (then verified). Run:

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
for f in skills/aph-hamilton/references/roles/*.md; do
  sed -i '' -E \
    -e 's@(^|[^./[:alnum:]])state/@\1.aphelocoma/state/@g' \
    -e 's@(^|[^./[:alnum:]])specs/@\1.aphelocoma/specs/@g' \
    -e 's@(^|[^./[:alnum:]])ledger/@\1.aphelocoma/ledger/@g' \
    "$f"
done
```

- [ ] **Step 2: Fix the one vocabulary occurrence (`cto.md`).** Change "In small companies (solo/startup)" → "In small crews (solo/startup)".

```bash
sed -i '' 's/In small companies/In small crews/' skills/aph-hamilton/references/roles/cto.md
```

- [ ] **Step 3: Verify — no double-prefix, no bare state/specs/ledger, no leftover vocab**

```bash
grep -rn "\.aphelocoma/\.aphelocoma/" skills/aph-hamilton/references/roles/                       # expect: nothing (no double-apply)
grep -rnE "(^|[^.])\b(state|specs|ledger)/" skills/aph-hamilton/references/roles/                  # expect: nothing (all namespaced)
grep -rinE "\b(compan(y|ies)|harness)\b" skills/aph-hamilton/references/roles/                     # expect: nothing
grep -rc "\.aphelocoma/state/" skills/aph-hamilton/references/roles/ | grep -v ':0' | wc -l        # expect: many files updated
```
Expected: first three print nothing; the fourth prints a count > 10. Spot-read `cto.md` and `software-architect.md` to confirm prose still reads correctly.

- [ ] **Step 4: Commit**

```bash
git add skills/aph-hamilton/references/roles/
git commit -m "Hamilton: remap per-project state paths in all 27 role files"
```

---

## Task 4: Rebrand the per-project templates

**Files:**
- Modify: `skills/aph-hamilton/templates/aphelocoma/state/brief.md`
- Modify: `skills/aph-hamilton/templates/aphelocoma/state/roadmap.md`
- Modify: `skills/aph-hamilton/templates/aphelocoma/hamilton.json`

**Interfaces:**
- Consumes: PROTOCOL §6 resume signal (`status: no-active-project`).
- Produces: the skeleton `start` copies into a project.

- [ ] **Step 1: Rewrite `brief.md` stub.** Keep `status: no-active-project` (the resume signal). Replace body:

```markdown
# Project Brief

> Stub — populated at runtime in Phase 0 (Kickoff). When a project starts, this file records
> the brief, the chosen crew size, the activated roles, and the start time. Hamilton treats a
> populated brief.md as the signal that a project is in progress (see PROTOCOL.md §6).

status: no-active-project

## Brief
_(none yet)_

## Crew size
_(none yet)_

## Activated roles
_(none yet)_
```

- [ ] **Step 2: Rewrite `roadmap.md` stub.**

```markdown
# Roadmap

> Stub — filled at runtime in Phase 2 (Plan & Roadmap) by leadership roles. Replace this
> file's contents with the milestone plan for the active project.

_No active project yet. Run `/aph-hamilton start "<brief>" <size>` to begin._
```

- [ ] **Step 3: Finalize `hamilton.json` comments** so the placeholders describe exactly what `start` writes (project slug, resolved size, active role IDs, `definition_version` copied from `references/VERSION`, ISO `created`, `phase: kickoff`). Keep it valid-on-its-face JSON-with-placeholders (it is a template, replaced wholesale at `start`).

- [ ] **Step 4: Verify**

```bash
grep -rinE "\b(compan(y|ies)|harness)\b|company/START" skills/aph-hamilton/templates/   # expect: nothing
test "$(wc -c < skills/aph-hamilton/templates/aphelocoma/ledger/events.jsonl)" -eq 0 && echo "events.jsonl empty OK"
python3 -c "import json;json.load(open('skills/aph-hamilton/templates/aphelocoma/state/tasks.json'));print('tasks.json valid')"
```
Expected: no grep output; "events.jsonl empty OK"; "tasks.json valid".

- [ ] **Step 5: Commit**

```bash
git add skills/aph-hamilton/templates/
git commit -m "Hamilton: rebrand per-project state templates"
```

---

## Task 5: Finalize `skill.md` (bridge: resolution + modes + version pin)

**Files:**
- Modify: `skills/aph-hamilton/skill.md`
- Verify: `skills/aph-hamilton/metadata.yaml`

**Interfaces:**
- Consumes: the resolution idiom + path model from Global Constraints; `references/VERSION` (1.0.0); the templates from Task 4.
- Produces: the runnable entrypoint a cold-start agent follows. Defines, for `start`: resolve size from `sizes.yaml`; copy `templates/aphelocoma/` → `./.aphelocoma/`; write `hamilton.json` with `definition_version` from `references/VERSION`; run PROTOCOL reading `roles/<id>.md`. For `resume`: compare `hamilton.json.definition_version` vs `references/VERSION`, warn on drift, continue per PROTOCOL §6. For `status`: phase + tasks + recent events.

- [ ] **Step 1: Remove the DRAFT banner** (lines beginning `> **STATUS: DRAFT seed (v0).**` …) — it is no longer a draft after this task.

- [ ] **Step 2: Replace the "Definitions install once" + add an explicit "Locating the definition" block** using the locked resolution idiom from Global Constraints (Claude `${CLAUDE_SKILL_DIR}/references/`; Codex/other = `references/` beside this SKILL.md via its injected path; definition files are siblings; state is `./.aphelocoma/`). This is the one place the skill-dir variable appears.

- [ ] **Step 3: Finalize the `start` steps** to read `sizes.yaml`/`VERSION`/`PROTOCOL.md`/`roles/<id>.md` from the resolved definition base, copy `templates/aphelocoma/` → `./.aphelocoma/`, and write `hamilton.json` (slug, size, roles, `definition_version` from `VERSION`, `created`, `phase: kickoff`). Keep `resume`/`status` aligned to `.aphelocoma/` paths; keep `sync-agents` as the Phase-2 stub (clearly marked).

- [ ] **Step 4: Verify the skill never leaks a bare/legacy path and states both-tool resolution**

```bash
grep -nE "\bcompany/|config/" skills/aph-hamilton/skill.md                       # expect: nothing
grep -c "CLAUDE_SKILL_DIR" skills/aph-hamilton/skill.md                          # expect: >=1 (Claude hint present)
grep -niE "codex|this SKILL.md|beside this" skills/aph-hamilton/skill.md         # expect: >=1 (Codex/self-locate hint present)
grep -c "\.aphelocoma/" skills/aph-hamilton/skill.md                             # expect: >=3
grep -nE "arguments:" skills/aph-hamilton/metadata.yaml                          # confirm hint matches modes
```
Expected: first prints nothing; the rest as noted.

- [ ] **Step 5: Commit**

```bash
git add skills/aph-hamilton/skill.md skills/aph-hamilton/metadata.yaml
git commit -m "Hamilton: finalize skill.md bridge — cross-tool resolution, start/resume/status, version pin"
```

---

## Task 6: Consistency sweep across the whole skill bundle

**Files:** read-only verification across `skills/aph-hamilton/` (excluding `examples/`, refreshed in Task 8/9).

**Interfaces:**
- Consumes: Tasks 1–5 output.
- Produces: a green "no legacy labels, no stray flat paths" gate before deploying.

- [ ] **Step 1: Full-bundle legacy-label + flat-path gate**

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
echo "--- legacy brand labels (expect none) ---"
grep -rinE "\b(compan(y|ies)|harness)\b|\bthe OS\b|operating system" skills/aph-hamilton --include='*.md' --include='*.yaml' --include='*.json' | grep -v '/examples/'
echo "--- flat (non-namespaced) state/ledger/specs refs (expect none) ---"
grep -rnE "(^|[^.a-zA-Z/])\b(state|ledger|specs)/" skills/aph-hamilton --include='*.md' | grep -v '/examples/' | grep -v '\.aphelocoma/'
echo "--- config/ refs (expect none) ---"
grep -rn "config/" skills/aph-hamilton --include='*.md' --include='*.yaml' | grep -v '/examples/'
```
Expected: all three sections print nothing.

- [ ] **Step 2: Definition-internal references resolve** (every `roles/<id>.md` named anywhere actually exists)

```bash
for id in $(grep -rhoE "roles/[a-z-]+\.md" skills/aph-hamilton/references | sort -u | sed -E 's@roles/@@; s@\.md@@'); do
  test -f "skills/aph-hamilton/references/roles/$id.md" || echo "MISSING: $id"
done; echo "(done — no MISSING lines above = OK)"
```
Expected: only "(done …)" prints.

- [ ] **Step 3: Commit** (only if Step 1/2 forced any fix; otherwise skip)

```bash
git add -A skills/aph-hamilton && git commit -m "Hamilton: consistency sweep fixes" || echo "nothing to fix"
```

---

## Task 7: Deploy to Claude + Codex; confirm definition-reach on **both** (the keystone gate)

**Files:** produces `~/.claude/skills/aph-hamilton/` and `~/.codex/skills/aph-hamilton/` (generated; not in repo).

**Interfaces:**
- Consumes: the finalized bundle.
- Produces: deployed skills proven to resolve their bundled `references/` on each tool. This gates Task 8.

- [ ] **Step 1: Deploy by running the `deploy` skill's documented steps with `APHELOCOMA_HOME`=this repo** (so the freshly-edited skill is the source; `~/.aphelocoma/data` is a separate dir and lacks aph-hamilton). For each tool, generate `SKILL.md` from `metadata.yaml` (`type: manual` → add `disable-model-invocation: true`; add `argument-hint` from `arguments`) with the `skill.md` body verbatim, and copy `references/`, `templates/`, `examples/` alongside:

```bash
REPO=/Users/phyoyarzar/Personal/codes/aphelocoma
for TOOL in claude codex; do
  DEST=~/.$TOOL/skills/aph-hamilton
  rm -rf "$DEST" && mkdir -p "$DEST"
  cp -R "$REPO/skills/aph-hamilton/references" "$REPO/skills/aph-hamilton/templates" "$REPO/skills/aph-hamilton/examples" "$DEST/"
done
# Generate SKILL.md (frontmatter from metadata.yaml + body from skill.md) for each tool:
python3 - <<'PY'
import os, pathlib
repo = pathlib.Path("/Users/phyoyarzar/Personal/codes/aphelocoma/skills/aph-hamilton")
meta = repo/"metadata.yaml"; body = (repo/"skill.md").read_text()
import re
m = {k.strip():v.strip() for k,v in (re.match(r'([^:]+):(.*)', l).groups() for l in meta.read_text().splitlines() if ':' in l and not l.startswith(' '))}
fm = f"---\nname: {m['name']}\ndescription: {m['description']}\ndisable-model-invocation: true\nargument-hint: {m.get('arguments','').strip(chr(34))}\n---\n\n"
for tool in ("claude","codex"):
    dest = pathlib.Path(os.path.expanduser(f"~/.{tool}/skills/aph-hamilton/SKILL.md"))
    dest.write_text(fm+body); print("wrote", dest)
PY
```
Expected: prints both `SKILL.md` paths. (If `/deploy` is preferred over manual steps, first sync `skills/aph-hamilton/` into `$APHELOCOMA_HOME/skills/`, then run the deploy skill — same result.)

- [ ] **Step 2: Confirm Claude can reach the definition.** `${CLAUDE_SKILL_DIR}` resolves to the install dir, and `references/` is beside `SKILL.md`:

```bash
test -f ~/.claude/skills/aph-hamilton/references/PROTOCOL.md && head -1 ~/.claude/skills/aph-hamilton/references/PROTOCOL.md
test -f ~/.claude/skills/aph-hamilton/references/VERSION && cat ~/.claude/skills/aph-hamilton/references/VERSION
```
Expected: the new `# PROTOCOL — How the Hamilton crew runs` line and `1.0.0`.

- [ ] **Step 3: Confirm **Codex** reaches the definition through the deployed skill — with a real `codex exec`** (the spec's non-deferrable cross-tool check). Run a fresh, read-only Codex agent that must self-locate the skill and read its bundled definition (no env var):

```bash
cd /private/tmp/claude-501/-Users-phyoyarzar-Personal-codes-aphelocoma/e96a03cb-f562-46c8-a36b-54d51c954888/scratchpad
codex exec -s read-only --skip-git-repo-check 'The skill `aph-hamilton` is installed at ~/.codex/skills/aph-hamilton/. WITHOUT relying on any CLAUDE_SKILL_DIR env var, locate its bundled definition the way its SKILL.md instructs (references/ beside SKILL.md), then: (1) print the first line of references/PROTOCOL.md, (2) print references/VERSION, (3) list references/roles/ count. Report the concrete absolute paths you used.'
```
Expected: Codex prints `# PROTOCOL — How the Hamilton crew runs`, `1.0.0`, `27`, and the absolute `~/.codex/skills/aph-hamilton/references/...` paths — proving definition-reach without the variable. **If Codex cannot resolve it**, add `adapters/codex/overrides/aph-hamilton.yaml` and a deploy-time `${CLAUDE_SKILL_DIR}`→concrete-path rewrite, re-deploy, and re-run this step before proceeding.

- [ ] **Step 4: Commit** (no repo changes expected unless Step 3 forced an override)

```bash
git add -A && git commit -m "Hamilton: deploy + cross-tool definition-reach verification" || echo "no repo changes"
```

---

## Task 8: Claude cold-start executed run (the acceptance gate)

**Files:** produces a throwaway project under the scratchpad; no repo changes (until optional Task 9 refresh).

**Interfaces:**
- Consumes: the deployed Claude skill from Task 7.
- Produces: an *executed* `.aphelocoma/` proving the five spec checks. **Authored artifacts do not count — only an executed cold-start does.**

- [ ] **Step 1: Create a throwaway project and confirm fresh-agent fidelity prerequisites.** The subagent must *auto-discover* `~/.claude/skills/aph-hamilton/` and resolve the definition itself — not be handed paths.

```bash
mkdir -p /private/tmp/claude-501/-Users-phyoyarzar-Personal-codes-aphelocoma/e96a03cb-f562-46c8-a36b-54d51c954888/scratchpad/cold-start-claude
ls ~/.claude/skills/aph-hamilton/SKILL.md   # must exist so the skill is discoverable
```

- [ ] **Step 2: Dispatch a fresh subagent given ONLY the user-level kickoff.** Use the Agent tool (`general-purpose`), working directory = the throwaway project, prompt = only:
  > `/aph-hamilton start "a simple todo list app" solo`
  Plus the minimum framing that it is a real run in the current empty directory and must use the installed `aph-hamilton` skill (no repo pointers, no path hand-feeding). The subagent must locate the definition itself.

- [ ] **Step 3: Assert the five spec checks against the produced `.aphelocoma/`** (a–e). Run:

```bash
P=/private/tmp/claude-501/-Users-phyoyarzar-Personal-codes-aphelocoma/e96a03cb-f562-46c8-a36b-54d51c954888/scratchpad/cold-start-claude
echo "a) bootstrapped .aphelocoma/?"; ls "$P/.aphelocoma/"{hamilton.json,state/tasks.json,ledger/events.jsonl} 2>&1
echo "b) read installed definition? (version pin present & matches)"; python3 -c "import json;print(json.load(open('$P/.aphelocoma/hamilton.json'))['definition_version'])"; cat ~/.claude/skills/aph-hamilton/references/VERSION
echo "c) ledger schema-valid + strictly monotonic seq?"; python3 - "$P/.aphelocoma/ledger/events.jsonl" <<'PY'
import json,sys
keys={"ts","seq","event","actor","task","to","note"}
prev=0; ok=True
for i,l in enumerate(open(sys.argv[1]),1):
    l=l.strip()
    if not l: continue
    e=json.loads(l)
    assert keys.issubset(e), f"line {i} missing keys: {keys-set(e)}"
    if e["seq"]!=prev+1: ok=False; print(f"SEQ BREAK at line {i}: {prev}->{e['seq']}")
    prev=e["seq"]
print("schema+seq OK through seq",prev) if ok else print("SEQ NOT MONOTONIC")
PY
echo "d) §7 coverage applied unprompted? (solo: a senior/leadership role emits a covered role's event, e.g. review_passed)"; grep -E '"event":"(review_passed|task_assigned)"' "$P/.aphelocoma/ledger/events.jsonl"
echo "e) reached phase done + project_completed?"; grep -E '"event":"project_completed"' "$P/.aphelocoma/ledger/events.jsonl"; python3 -c "import json;print('phase=',json.load(open('$P/.aphelocoma/state/tasks.json')).get('phase'))"
echo "product exists?"; ls "$P/" "$P/product/" 2>/dev/null
```
Expected (all must hold): (a) all three files exist; (b) `definition_version` == `1.0.0` == VERSION; (c) "schema+seq OK"; (d) a covering event present (a `solo` crew has no qa-engineer, so `cto` must emit `review_passed`); (e) a `project_completed` event and `phase=done`; a product file exists in the project (not under `.aphelocoma/`).

- [ ] **Step 4: Gate.** Only if **all** of a–e pass may the work be called working. If any fail, fix the responsible definition/skill file (Tasks 1/3/5), re-deploy (Task 7 Step 1), and re-run this task. **Do not** patch the produced run by hand. Record the verdict.

- [ ] **Step 5: Commit the passing verdict note** (a short `docs/superpowers/notes/2026-06-23-hamilton-coldstart.md` capturing the command outputs as evidence)

```bash
git add docs/superpowers/notes/2026-06-23-hamilton-coldstart.md && git commit -m "Hamilton: record passing Claude cold-start verification (a-e)"
```

---

## Task 9: Refresh the shipped example + finalize (non-blocking)

**Files:**
- Replace: `skills/aph-hamilton/examples/todo-solo/**` (from the Task 8 run)
- Modify: `skills/aph-hamilton/examples/todo-solo/NOTE.md`
- Modify: `core/projects/aphelocoma/tasks.md` (mark Phase 1 done); optional ADR in `core/projects/aphelocoma/adrs/`

**Interfaces:**
- Consumes: the passing Task 8 `.aphelocoma/` + product.
- Produces: a shipped example in the *new* two-layer layout, plus repo bookkeeping.

- [ ] **Step 1: Replace the flat-layout example with the executed new-layout run.** Copy the Task 8 throwaway's `.aphelocoma/` + product into `examples/todo-solo/` (preserving the real ledger), removing the old flat `state/`+`ledger/`+`specs/`+`product/` top-level dirs.

- [ ] **Step 2: Rewrite `NOTE.md`** to describe the new layout honestly (provenance: executed cold-start on <date>, solo, todo app; §7 coverage shown; ships as a reference, not deleted). No "delete `_smoketest`" wording.

- [ ] **Step 3: Verify the example is internally consistent** (re-run the Task 8 Step 3 schema+seq check against `examples/todo-solo/.aphelocoma/ledger/events.jsonl`). Expected: "schema+seq OK".

- [ ] **Step 4: Update aphelocoma bookkeeping** — mark Phase 1 complete in `core/projects/aphelocoma/tasks.md`; offer an ADR recording the thin+global-ref + cross-tool-resolution decision.

- [ ] **Step 5: Commit + finish the branch**

```bash
git add -A && git commit -m "Hamilton: refresh shipped example to new .aphelocoma/ layout; Phase 1 bookkeeping"
```
Then use **superpowers:finishing-a-development-branch** to choose merge/PR for `hamilton-phase-1`.

---

## Self-Review

**Spec coverage (Phasing §Phase 1):**
1. Rename company/OS → Hamilton across `references/` (+ ABOUT/START) → **Tasks 1, 2, 3** (and templates in Task 4). ✓
2. Finalize `skill.md` start/resume/status via skill-dir + thin `.aphelocoma/` → **Task 5**. ✓
3. `hamilton.json` + version-pin read/compare → **Task 4 (template) + Task 5 (write on start / compare on resume)**, asserted in **Task 8 (b)**. ✓
4. Cross-tool skill-dir resolution (Claude **and** Codex), overrides only if needed → **Task 7** (empirically, via real `codex exec`; the A-strategy was pre-validated 2026-06-23). ✓
5. Deploy + cold-start test → **Task 7 (deploy) + Task 8 (executed gate, checks a–e)**. ✓

**Verification rigor (spec §Verification a–e):** bootstraps `.aphelocoma/` (8a), reads installed definition (8b + 7), schema-valid + monotonic `seq` (8c), §7 coverage unprompted (8d), version pin recorded (8b). The run is a *fresh subagent given only the kickoff*, working in a throwaway dir, auto-discovering the installed skill — not spoon-fed (8 Step 1–2). Empty `events.jsonl` confirmed (Task 4 Step 4) so `seq` starts at 1.

**Placeholder scan:** path-remap and rename steps give exact `sed`/`grep` commands and the exact replacement prose; semantic rewrites (PROTOCOL §0, skill.md resolution, NOTE.md) show the actual new text. No TBD/TODO.

**Type/contract consistency:** ledger schema, phase names, event types, role IDs, and status lifecycle are unchanged from the verified prototype and used identically in PROTOCOL (Task 1), the verification (Task 8c/d/e), and the example check (Task 9). The resolution idiom is defined once (Global Constraints) and referenced by Task 5 and Task 7.

**Known risks / decisions:** (1) Branch `hamilton-phase-1` off `main` despite the repo's recent commit-to-main habit — safer for a multi-commit feature; integration via finishing-a-development-branch. (2) `product/` retained as a *defined term* rather than remapped, to avoid 27 files of prose surgery and to honor the spec's "repo root or ./product". (3) Deploy run with `APHELOCOMA_HOME`=repo rather than syncing into `~/.aphelocoma/data` first — fewer copies, repo stays source of truth.
