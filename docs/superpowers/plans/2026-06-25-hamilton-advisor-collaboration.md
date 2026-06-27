# Hamilton — Advisor Collaboration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline — the changes
> are tightly-coupled prose edits to one definition; full repo context prevents drift). Steps use
> checkbox (`- [ ]`). The executed gate (Task 7) supplies *scripted advisor picks* to test the
> autonomous machinery; the truly-interactive checkpoints ship a **manual test checklist** for the user.

**Goal:** Turn Hamilton from an autonomous crew into a **human-in-the-loop crew**: you advise (brief →
discuss → pick direction + size → approve plan → choose build style → review), the crew builds
autonomously — building at the **project root** (no `product/`), via an **interactive `/aph-hamilton`**
entry, on new **or existing** projects.

**Architecture:** Additive revision of the definition + bridge built on `hamilton-phase-1`. The
PROTOCOL gains an **advisor model** (4 checkpoints + the `advisor` actor + a `decision` ledger event);
the **leadership core** (`cto`/`software-architect`/`product-manager`) activates first and **crew size
is chosen after Discovery**; `product/` is removed (product lives beside `.aphelocoma/`); `skill.md`
gains the interactive wizard, the checkpoint pauses, the build-style prompt, and existing-project
survey/resume. All verified machinery (two-layer install, cross-tool self-location, ledger schema,
orchestrator-owned-state parallelism) is reused unchanged.

**Tech Stack:** Markdown + YAML + JSONL. No build. Verification: `grep`/`python3` structural+schema
checks, plus one executed run with scripted advisor picks.

## Global Constraints

(Every task implicitly includes these — verbatim from `2026-06-25-hamilton-advisor-collaboration.md`.)

- **One flow, no modes.** You advise (decisions); the crew builds (implementation). Always. The user never writes code.
- **Leadership-first; size after Discovery.** `cto` + `software-architect` + `product-manager` activate immediately and discuss the brief with the advisor. The crew **size/shape** (implementers + specialists) is chosen **after Discovery**, recommended by leadership, picked by the user — never guessed upfront.
- **Four checkpoints** (crew pauses, presents 2–3 options w/ trade-offs + a recommendation, waits for the user's pick / answer / "you decide"):
  1. **After Discovery** — pick the direction **and** the crew size.
  2. **After Plan & Roadmap** — approve / reorder / cut / add.
  3. **Before Implementation** — *subagents or one session?* (only when parallel is possible; **asked each build**).
  4. **At Review** — accept, or say what to fix / add.
- **Vague brief ⇒ interview, not guess.** Unknowns become questions; the crew must not fabricate scope.
- **"You decide" always allowed** — the crew proceeds with its recommendation and logs that the advisor delegated.
- **No `product/`.** `.aphelocoma/` is the only directory Hamilton owns; the product is built at the **project root, beside `.aphelocoma/`**, structured however fits.
- **Existing projects:** Discovery does a **codebase survey** first; the crew **edits/extends in place** following existing patterns; an existing `.aphelocoma/` triggers an **offer to `resume`**, not overwrite.
- **Ledger:** add ONE event type, **`decision`** (`actor: advisor`; `note` = the options offered + the pick/"delegated"). Line shape `{ts,seq,event,actor,task,to,note}` and monotonic `seq` are unchanged. The `advisor` actor = the human seat.
- **Interactive entry:** bare `/aph-hamilton` runs a short guided start; the typed fast path (`/aph-hamilton start "…" <size>`) still works (and skips the wizard).
- **Reuse, don't rebuild:** phases, role catalog, two-layer install, cross-tool self-location, `PARALLEL.md` single-writer model — all kept. Continue on branch `hamilton-phase-1`.

## File Structure

- `skills/aph-hamilton/references/PROTOCOL.md` — **heaviest change.** Add §1.5 "Advisor model"; rework §2 (leadership-first, Discovery interview, the 4 checkpoints, size-after-Discovery); add `decision` to §5 + the `advisor` actor; drop `product/` (→ "the project, beside `.aphelocoma/`").
- `skills/aph-hamilton/references/roles/*.md` (27) — drop `product/` → project-root phrasing; `cto`/`software-architect`/`product-manager` gain "present options to the advisor; recommend crew size after Discovery."
- `skills/aph-hamilton/skill.md` — interactive wizard; advisor-checkpoint pauses in `start`; build-style prompt; existing-project survey + `resume`-detection; leadership-first/size-after-Discovery; drop `product/`.
- `skills/aph-hamilton/references/sizes.yaml` — reframe: leadership core is always-on; presets are the **implementer/specialist** sets chosen after Discovery.
- `skills/aph-hamilton/references/{ABOUT.md,START.reference.md}` — update usage (interactive entry, advisor flow, no `product/`).
- `skills/aph-hamilton/templates/aphelocoma/state/brief.md` — add `Direction` + `Advisor` lines.
- `skills/aph-hamilton/references/PARALLEL.md` — one line: the build-style is **user-chosen at the checkpoint**, not a settings toggle.
- `skills/aph-hamilton/examples/todo-solo/**` — refresh to the no-`product/` layout (product at the example root).
- `docs/superpowers/notes/2026-06-25-hamilton-advisor-verification.md` — the executed-run verdict + the user's manual checklist.

**Out of scope (YAGNI):** remembering the build-style across builds; a separate non-interactive "autopilot" mode; auto-sizing heuristics beyond "leadership recommends, user picks."

---

## Task 1: PROTOCOL.md — advisor model, leadership-first, `decision` event, drop `product/`

**Files:** Modify `skills/aph-hamilton/references/PROTOCOL.md`.

**Interfaces:**
- Produces (downstream tasks + verification depend on these exact names): the **`advisor`** actor; the
  **`decision`** event type; checkpoint names; "leadership core" = `cto`,`software-architect`,
  `product-manager`; product location = "the project, beside `.aphelocoma/`" (no `product/`).

- [ ] **Step 1: §0 mental model — product location.** Replace the `product/` bullet with: "The product
  (the software being built) lives in the **project itself — at the repo root, beside `.aphelocoma/`**,
  structured however the work needs. `.aphelocoma/` is the only directory Hamilton owns."

- [ ] **Step 2: Add §1.5 "Advisor model"** after §1:

```markdown
## 1.5 Advisor model (human-in-the-loop)

A **human advisor** (the user) steers every decision; the crew does all the building. The advisor
occupies the top seat — ledger `actor: advisor`. The crew **pauses at four checkpoints**, each time
presenting 2–3 options with trade-offs (or targeted questions) and a recommendation, then waits:

1. **After Discovery** — the advisor picks the product **direction** AND the **crew size** (leadership
   recommends a size from what Discovery revealed; see §2).
2. **After Plan & Roadmap** — the advisor approves / reorders / cuts / adds.
3. **Before Implementation** — the advisor picks the build style (subagents vs one session; §1).
4. **At Review** — the advisor accepts, or says what to fix / add.

Record each as a `decision` event: `actor: advisor`, `note` = the options offered + the choice (or
"delegated" if the advisor says "you decide" — then proceed with the recommendation). Between
checkpoints the crew works autonomously; the advisor may interject at any time. Never fabricate scope:
an unknown becomes a question to the advisor, not an assumption.
```

- [ ] **Step 3: Rework §2 phases.** Phase 0 (Kickoff): activate only the **leadership core**
  (`cto`,`software-architect`,`product-manager`) — NOT a full size yet. Phase 1 (Discovery): for a
  vague brief, **interview the advisor** + (existing project) survey the codebase; end with checkpoint
  1 — present directions + a recommended crew size, advisor picks both; **then** activate the chosen
  implementer/specialist roles. Phase 2 (Plan & Roadmap): end with checkpoint 2. Phase 4
  (Implementation): begin with checkpoint 3 (build style); build at the project root. Phase 5 (Review):
  checkpoint 4. Keep the canonical `phase` values unchanged.

- [ ] **Step 4: §5 — add the event + actor.** Add `decision` to the event-type list. Add a line: "The
  **`advisor`** actor is the human; it appears on `decision` events (and any direction the human gives)."

- [ ] **Step 5: Drop `product/` everywhere in PROTOCOL** — replace `product/` with "the project (beside
  `.aphelocoma/`)" in §2.4, §3e, §4, §7 "Stay in lane".

- [ ] **Step 6: Verify**

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
grep -qi "Advisor model" skills/aph-hamilton/references/PROTOCOL.md && echo "§1.5 present"
grep -c "decision" skills/aph-hamilton/references/PROTOCOL.md          # event + checkpoints referenced
grep -qi "leadership core" skills/aph-hamilton/references/PROTOCOL.md && echo "leadership-first present"
grep -nE "\bproduct/" skills/aph-hamilton/references/PROTOCOL.md || echo "no product/ left ✓"
grep -nE "\b(compan(y|ies)|harness)\b" skills/aph-hamilton/references/PROTOCOL.md || echo "no brand regression ✓"
```
Expected: §1.5 + leadership-first present; `decision` referenced; no `product/`; no brand regression.

- [ ] **Step 7: Commit** — `git commit -m "Hamilton advisor: PROTOCOL — advisor model, leadership-first, decision event, drop product/"`.

---

## Task 2: Role files — drop `product/`; leadership roles advise + recommend size

**Files:** Modify `skills/aph-hamilton/references/roles/*.md`.

**Interfaces:** Consumes Task 1's "project beside `.aphelocoma/`" phrasing + `advisor` concept.

- [ ] **Step 1: Remap `product/` across all role files** (it only ever means "where the product is built"):

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
for f in skills/aph-hamilton/references/roles/*.md; do
  sed -i '' -E 's@(^|[^./[:alnum:]])product/@\1the project root (beside .aphelocoma/): @g; s@under the project root \(beside \.aphelocoma/\): @under the project root (beside .aphelocoma/) @g' "$f"
done
# NOTE: review output; the second sed tidies the common "under product/" phrasing. Hand-fix any awkward reads.
```
(If the sed produces awkward prose, prefer per-file hand edits — the rule is: "under `product/`" → "in the project (beside `.aphelocoma/`)".)

- [ ] **Step 2: Update the three leadership roles.** In `roles/cto.md`, `roles/software-architect.md`,
  `roles/product-manager.md`, add to Responsibilities: "In Discovery, **present 2–3 options with
  trade-offs to the advisor and ask the defining questions** rather than deciding alone; after the
  direction is chosen, **recommend a crew size/shape** for the advisor to pick (PROTOCOL §1.5, §2)."

- [ ] **Step 3: Verify**

```bash
grep -rnE "\bproduct/" skills/aph-hamilton/references/roles/ || echo "no product/ left in roles ✓"
grep -rl "advisor" skills/aph-hamilton/references/roles/cto.md skills/aph-hamilton/references/roles/software-architect.md skills/aph-hamilton/references/roles/product-manager.md | wc -l   # expect 3
grep -rnE "\.aphelocoma/\.aphelocoma/" skills/aph-hamilton/references/roles/ || echo "no double-path ✓"
```
Expected: no `product/`; 3 leadership files mention `advisor`; no double-paths. Spot-read `cto.md` + 1 implementer role for prose sanity.

- [ ] **Step 4: Commit** — `git commit -m "Hamilton advisor: roles — drop product/, leadership roles advise + recommend size"`.

---

## Task 3: skill.md — interactive entry, checkpoint pauses, build-style prompt, existing-project

**Files:** Modify `skills/aph-hamilton/skill.md`.

**Interfaces:** Consumes Task 1 (checkpoints, `decision`, leadership-first) + `PARALLEL.md`.

- [ ] **Step 1: Add a bare-invocation wizard** at the top of "Modes". When `$ARGUMENTS` is empty, run
  the guided start:

```markdown
### (no arguments) — guided start
1. Detect context: is there existing code here? an existing `./.aphelocoma/`? If `.aphelocoma/` exists,
   report the in-progress project and offer `resume` (don't overwrite).
2. Ask: "**New project, or work on this existing one?**" then "**What do you want to build / add / fix?**"
   (plain words; vague is fine).
3. Activate the **leadership core** (`cto`,`software-architect`,`product-manager`) and begin the
   protocol at Discovery. **Crew size is chosen after Discovery (checkpoint 1)** — do NOT ask size here.
The typed fast path `start "<brief>" <size>` skips this wizard.
```

- [ ] **Step 2: Make `start` advisor-aware.** Update the `start` steps: activate the leadership core
  first; run Discovery (interview + existing-codebase survey) → **checkpoint 1** (present directions +
  recommended size; advisor picks; log a `decision`); activate chosen roles; Plan & Roadmap →
  **checkpoint 2** (`decision`); **checkpoint 3** before Implementation (build style — only if parallel
  possible; `decision`); build **at the project root** (no `product/`); Review → **checkpoint 4**
  (`decision`). Each checkpoint: present 2–3 options w/ trade-offs, accept the pick or "you decide".

- [ ] **Step 3: `resume` detects existing state** (already version-free): if `.aphelocoma/` exists,
  report phase + open tasks and continue; if `start` is run where `.aphelocoma/` already exists,
  redirect to `resume` (don't clobber).

- [ ] **Step 4: Drop `product/` from skill.md** ("The product: the project proper — repo root, beside
  `.aphelocoma/`. Never inside `.aphelocoma/`.").

- [ ] **Step 5: Verify**

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
grep -qi "guided start\|no arguments" skills/aph-hamilton/skill.md && echo "wizard present"
grep -ci "checkpoint\|advisor\|decision" skills/aph-hamilton/skill.md       # advisor flow wired
grep -qi "after Discovery" skills/aph-hamilton/skill.md && echo "size-after-discovery present"
grep -qi "resume" skills/aph-hamilton/skill.md && echo "resume-on-existing present"
grep -nE "\bproduct/|\bcompany/|config/" skills/aph-hamilton/skill.md || echo "no product/ or legacy paths ✓"
```
Expected: wizard + advisor flow + size-after-discovery + resume present; no `product/`/legacy.

- [ ] **Step 6: Commit** — `git commit -m "Hamilton advisor: skill.md — interactive entry, checkpoints, build-style prompt, existing-project resume"`.

---

## Task 4: sizes.yaml + ABOUT + START + brief template

**Files:** Modify `references/sizes.yaml`, `references/ABOUT.md`, `references/START.reference.md`, `templates/aphelocoma/state/brief.md`.

- [ ] **Step 1: Reframe `sizes.yaml`.** Add a header note: "The **leadership core**
  (`cto`,`software-architect`,`product-manager`) is always active first (Discovery). These presets are
  the **implementer/specialist** team chosen **after Discovery** (PROTOCOL §1.5). `solo` = the
  leadership core wears all hats." Keep the preset role lists.

- [ ] **Step 2: Update `ABOUT.md` + `START.reference.md`** — "Start a project" now shows bare
  `/aph-hamilton` (guided) as primary; describe the advisor flow (you decide at 4 checkpoints, crew
  builds), no `product/` (build at the root), and existing-project support. Drop any `product/`.

- [ ] **Step 3: `brief.md` template** — add `## Direction` and `## Advisor` sections (stub: "_(picked at checkpoint 1)_" / "the human steering this project"). Keep `status: no-active-project`.

- [ ] **Step 4: Verify**

```bash
grep -rnE "\bproduct/" skills/aph-hamilton/references/ABOUT.md skills/aph-hamilton/references/START.reference.md skills/aph-hamilton/references/sizes.yaml || echo "no product/ in these ✓"
grep -qi "leadership core" skills/aph-hamilton/references/sizes.yaml && echo "sizes reframed ✓"
grep -qi "Direction" skills/aph-hamilton/templates/aphelocoma/state/brief.md && echo "brief has Direction ✓"
grep -rinE "\b(compan(y|ies)|harness)\b" skills/aph-hamilton/references/ABOUT.md skills/aph-hamilton/references/START.reference.md skills/aph-hamilton/references/sizes.yaml || echo "no brand regression ✓"
```
Expected: all present; no `product/`; no brand regression.

- [ ] **Step 5: Commit** — `git commit -m "Hamilton advisor: sizes/ABOUT/START/brief — leadership-core framing, interactive usage, no product/"`.

---

## Task 5: PARALLEL.md note + refresh the shipped example to no-`product/`

**Files:** Modify `references/PARALLEL.md`; restructure `examples/todo-solo/**`.

- [ ] **Step 1: `PARALLEL.md`** — change the enabling condition "(2) `.aphelocoma/settings.yaml` sets
  `parallel_dispatch: true`" to "(2) the **advisor chose 'subagents'** at the build-style checkpoint
  (PROTOCOL §1.5 checkpoint 3)". Keep the single-writer model unchanged.

- [ ] **Step 2: Refresh the example to build at the root.** Move the product beside `.aphelocoma/`:

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma/skills/aph-hamilton/examples/todo-solo
git mv product/todo.html ./todo.html 2>/dev/null || mv product/todo.html ./todo.html
rmdir product 2>/dev/null || rm -rf product
# fix the recorded artifact path in tasks.json
sed -i '' 's@product/todo.html@todo.html@g' .aphelocoma/state/tasks.json
sed -i '' 's@product/todo.html@todo.html@g' .aphelocoma/ledger/events.jsonl
```
Update `NOTE.md`: the product now sits at the example root (no `product/`); note this is the
new-layout reference.

- [ ] **Step 3: Verify the example is still schema-valid + path-consistent**

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
P=skills/aph-hamilton/examples/todo-solo
test -f "$P/todo.html" && test ! -d "$P/product" && echo "product at root ✓"
grep -rn "product/" "$P" || echo "no product/ refs in example ✓"
python3 - "$P/.aphelocoma/ledger/events.jsonl" <<'PY'
import json,sys
prev=0
for l in open(sys.argv[1]):
    l=l.strip()
    if not l: continue
    e=json.loads(l); assert e["seq"]==prev+1; prev=e["seq"]
print("example ledger seq 1..%d OK"%prev)
PY
```
Expected: product at root, no `product/` refs, ledger intact.

- [ ] **Step 4: Commit** — `git commit -m "Hamilton advisor: PARALLEL build-style via checkpoint; refresh example to no-product/ layout"`.

---

## Task 6: Full-bundle consistency sweep

**Files:** read-only checks across `skills/aph-hamilton/` (excl. HANDOFF, which is a build doc).

- [ ] **Step 1: Sweep**

```bash
cd /Users/phyoyarzar/Personal/codes/aphelocoma
echo "--- any product/ left in deployed content? (expect none) ---"
grep -rnE "\bproduct/" skills/aph-hamilton/references skills/aph-hamilton/skill.md skills/aph-hamilton/templates | grep -v '/examples/' || echo "(clean)"
echo "--- decision event in vocab + advisor actor defined? ---"
grep -q '`decision`' skills/aph-hamilton/references/PROTOCOL.md && grep -qi "advisor" skills/aph-hamilton/references/PROTOCOL.md && echo "decision+advisor ✓"
echo "--- legacy brand labels? (expect none) ---"
grep -rinE "\b(compan(y|ies)|harness)\b|\bthe OS\b" skills/aph-hamilton/references skills/aph-hamilton/skill.md | grep -v '/examples/' || echo "(clean)"
echo "--- every referenced role file exists? ---"
for id in $(grep -rhoE "roles/[a-z-]+\.md" skills/aph-hamilton/references | sort -u | sed -E 's@roles/@@;s@\.md@@'); do test -f "skills/aph-hamilton/references/roles/$id.md" || echo "MISSING $id"; done; echo "(role check done)"
```
Expected: no `product/`; `decision`+`advisor` present; no brand labels; no MISSING roles.

- [ ] **Step 2: Commit** any fixes — `git commit -m "Hamilton advisor: consistency sweep" || echo "nothing to fix"`.

---

## Task 7: Executed verification (scripted advisor) + manual checklist (the gate)

**Files:** throwaway project under scratchpad; produces `docs/superpowers/notes/2026-06-25-hamilton-advisor-verification.md`.

**The autonomous machinery is asserted by an executed run; the genuinely-interactive pauses ship as a
manual checklist (an interactive flow cannot be fully cold-started without a human).**

- [ ] **Step 1: Executed run with scripted picks.** In a throwaway project (test both: a NEW empty
  dir, and an EXISTING one with a stub file), dispatch a fresh agent given the kickoff PLUS the
  advisor's pre-decided answers for each checkpoint (e.g. `direction=lean, size=solo, build=one-session,
  review=accept`). Tell it: pause-points are pre-answered with these; otherwise follow the skill.

- [ ] **Step 2: Assert the advisor machinery mechanically:**

```bash
P=<throwaway>
echo "(a) leadership core ran first?"; grep -E '"event":"role_activated".*"(cto|software-architect|product-manager)"' "$P/.aphelocoma/ledger/events.jsonl" | head
echo "(b) decision events present, actor=advisor?"; grep -E '"event":"decision".*"actor":"advisor"' "$P/.aphelocoma/ledger/events.jsonl"
echo "(c) product built at ROOT, not in product/?"; ls "$P" | grep -v '^\.aphelocoma$'; test ! -d "$P/product" && echo "no product/ ✓"
echo "(d) ledger schema-valid + monotonic seq (incl. decision events)?"; python3 - "$P/.aphelocoma/ledger/events.jsonl" <<'PY'
import json,sys
keys={"ts","seq","event","actor","task","to","note"}; allowed={"role_activated","brainstorm_note","plan_created","roadmap_updated","task_created","task_assigned","work_started","artifact_written","task_completed","review_passed","review_failed","blocked","assumption_logged","handoff","phase_advanced","project_completed","decision"}
prev=0; ok=True
for i,l in enumerate(open(sys.argv[1]),1):
    l=l.strip()
    if not l: continue
    e=json.loads(l)
    if not keys.issubset(e) or e["event"] not in allowed or e["seq"]!=prev+1: ok=False; print("BAD line",i,e.get("event"))
    prev=e["seq"]
print("schema+seq", "OK 1..%d"%prev if ok else "FAIL")
PY
echo "(e) existing-project run: a survey brainstorm_note referencing existing files?"; grep -E '"event":"brainstorm_note".*(existing|survey|current)' "$P/.aphelocoma/ledger/events.jsonl" | head
```
Expected: (a) all three leadership roles activated before any implementer; (b) ≥1 `decision` by `advisor`; (c) product at root, no `product/`; (d) `schema+seq OK` with `decision` accepted; (e) the existing-project run logged a codebase survey.

- [ ] **Step 3: Write the manual checklist** (for the user to drive the real interactive pauses) into
  the verdict note: bare `/aph-hamilton` starts the wizard; the crew actually **stops** at each of the
  4 checkpoints and presents options; "you decide" works; a vague brief ("an ecommerce") triggers
  questions, not a guess; resume works on an in-progress `.aphelocoma/`.

- [ ] **Step 4: Gate.** Claim "works" only when Step 2 (a)–(e) pass. If any fail, fix the responsible
  definition/skill file and re-run — don't hand-patch the produced run. Record the verdict + checklist; **commit**.

- [ ] **Step 5: Update HANDOFF + finish.** Note advisor-collaboration done+verified; deploy + `git push`
  remain user-owned. Use **superpowers:finishing-a-development-branch** (the user owns integration).

---

## Self-Review

**Spec coverage:** one flow/no-modes → Global Constraints + Task 1 §1.5. Leadership-first + size-after-Discovery → Task 1 Step 3, Task 2 Step 2, Task 4 Step 1, asserted Task 7(a). Four checkpoints → Task 1 §1.5 + Task 3 Step 2. Vague-brief interview → Task 1 Step 3 + Task 3, asserted Task 7(e)/checklist. "You decide" → Task 1 §1.5. No `product/` → Tasks 1/2/3/4/5, asserted Task 6 + 7(c). Existing-project survey/resume → Task 1 Step 3, Task 3 Steps 1+3, asserted Task 7(e). `decision` event → Task 1 Step 4, asserted Task 7(b)/(d). Interactive entry → Task 3 Step 1. Build-style each build → Task 1 §1.5 + Task 3 Step 2 + Task 5 Step 1. ✓ all covered.

**Placeholder scan:** new PROTOCOL §1.5 + decision-event schema + wizard text are spelled out; mechanical remaps give exact `sed`+`grep`; the role-file sed is flagged "hand-fix awkward reads" (a real instruction, not a TODO). No TBD.

**Type/contract consistency:** `decision` event, `advisor` actor, the leadership-core trio, the 4 checkpoint names, and "project root beside `.aphelocoma/`" are defined once (Task 1) and reused identically in Tasks 2–7. Ledger line shape unchanged; `decision` added to the allowed set in both PROTOCOL §5 and the Task 7(d) validator.

**Risks / decisions:** (1) The role-file `product/` sed may read awkwardly — flagged for hand-fix; the safe rule is given. (2) The executed gate uses **scripted advisor picks** to test the autonomous machinery; the true interactive pauses are a **manual checklist** (honest — an interactive flow can't be unattended-cold-started). (3) Continues on `hamilton-phase-1`; deploy + push stay user-owned.
