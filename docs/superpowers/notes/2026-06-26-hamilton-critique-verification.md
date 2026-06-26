# Hamilton Critique Passes & Craft Bar — Verification Verdict

_Date: 2026-06-26 · Branch `hamilton-phase-1`_

Verifies the feature in `docs/superpowers/specs/2026-06-26-hamilton-critique-passes.md` (plan
`docs/superpowers/plans/2026-06-26-hamilton-critique-passes.md`). The gate is a **seeded-defect
catch-test**: for a critic, "the event fired" ≠ "it works" — the only proof is that an independent
reviewer applying the real rubric **catches planted defects** and **does not raise false alarms**.

## What was built (Tasks 1–4, all committed + reviewed)

- T1 `434c7f5` — `references/CRITIQUE.md` (rubric) + `references/CRAFT.md` (craft bar). Review ✅ Approved.
- T2 `4ac6b63` — `PROTOCOL.md` wiring (§1.5, §2 Phases 1/2/4/5, §5 `critique` event + `reviewer` actor,
  §7). Review ✅ Approved (1 deferred cosmetic Minor — see Residuals).
- T3 `35b10d6` — 9 role-file pointers (cto/architect/PM dispatch; **QA review IS the CP4 critique**;
  implementers/leads → craft bar). Controller-verified clean.
- T4 `1ba2842` — `skill.md` wording + definition file list. Controller-verified clean.

## Method

Three **fresh-context subagent reviewers** (sonnet — representative of the Claude Code `subagent` tier),
each told only that it is the Hamilton independent reviewer for one gate. Each **read the real rubric**
(`references/CRITIQUE.md`, plus `CRAFT.md` for CP4) and applied it to a **blind** planted artifact — the
fixtures carry **no labels** marking their defects, and the CP4 files were given neutral names
(`save.js`, `render.js`) so the names couldn't telegraph the answer. The answer key was withheld from
the critics. Findings written to `findings-cp{1,2,4}.md` in the scratch run dir (not committed).

## Results — all three gates PASS

### CP1 · Brainstorm critique — `brief.md` (a realtime collaborative editor)
Planted unstated assumptions: **(a)** no identity/auth model though "everyone / each other's cursors"
presupposes users; **(b)** no sync/conflict-resolution mechanism for simultaneous edits.
**Critique flagged BOTH** — `[should-fix] User identity / presence model undefined` and
`[blocking] Conflict resolution strategy absent` + `[should-fix] Sync transport mechanism not stated` —
plus real bonus findings (a Direction↔Goals cursor contradiction; undefined document model; absent
persistence). Verdict: 7 findings (2 blocking, 4 should-fix, 1 nit). **PASS.**

### CP2 · Plan critique — `roadmap.md` (todo app) — the net-new gap
Planted holes: **(a)** goal G2 ("mark a todo done") has **no implementing task**; **(b)** task T3 owner
is `___` (**unowned**).
**Critique flagged BOTH** — `[blocking] F1 G2 has no implementing task`, `[blocking] F2 T3 is unowned` —
plus the bonus `[blocking] F3 dependency inversion (T3 must precede T1/T2)` and `[nit] F4 implicit
traceability`. Verdict: 3 blocking — "plan is NOT clear to proceed." **PASS.**

### CP4 · Implementation critique — `save.js` + `render.js`
Planted: `save.js` has an **empty `catch` that swallows errors** (craft-bar violation); `render.js` is a
**clean inline helper used once with no pre-existing pattern** (the no-false-positive control).
**Critique flagged `save.js`** (`[blocking]` swallowed catch → violates CRAFT.md "don't swallow errors",
plus a bonus real defect: undeclared `db`) and **PASSED `render.js`** — it did **not** demand extraction
"for consistency/reuse." Verdict: save.js FAIL / render.js PASS (1 non-blocking nit). **PASS — and the
no-false-positive result empirically confirms the precedence + floor-not-ceiling design** that prevents
the simplicity-vs-consistency thrashing the spec set out to avoid.

### Ledger wiring
The `critique` event parses on the existing schema (`event:critique`, `actor:reviewer`, `task:null` at
CP1/CP2); `critique` is present in PROTOCOL §5's event-type list; the `reviewer` actor is defined as a
reserved actor with tier recorded. **PASS.**

## Overall verdict

**PASS.** The rubric catches planted defects at all three gates (CP1/CP2/CP4) and correctly passes clean
work without false "consistency" alarms. The independence mechanism (fresh subagent) and the
advisory-tier `critique` event are wired and loggable.

## Residuals / caveats (non-blocking)

1. **Manual residual (as with every prior Hamilton phase).** This drove the critic subagents directly —
   exactly how the real CP1/CP2/CP4 critique operates — but did not invoke the full protocol via a live
   interactive `/aph-hamilton` (manual skills aren't model-invocable; HANDOFF Phase-2 finding). One real
   interactive run remains the final human-loop confirmation. User-owned, like deploy/push.
2. **Tier tested = `subagent` only.** The persona-pass fallback (non-subagent platforms, ≈ checklist
   self-review strength) was not exercised here; it is honestly labeled in the rubric/ledger.
3. **Deferred Minor M1** (from T2 review): §2 Phase 2 "Plan critique" continuation lines sit at column 0
   vs. Phase 2's 3-space list indent (cosmetic, renders fine). Fix PROTOCOL.md indent **and** the plan's
   Step 4 block in the final-review fix wave.
4. **Test-validity fixes vs. the plan's Task 5 as written** (fold into the plan at final review): the
   plan's Step 2 roadmap and Step 4 brief contained giveaway labels (`<!-- planted hole -->`,
   "(assumes …)") that would have rigged a blind test, and used telegraphing filenames `bad.js`/`ok.js`.
   The executed test stripped the labels, made the assumptions implicit, and used neutral names — a
   stricter (correct) version of the plan's intent. Also fixed earlier: plan Task 1 Step 5 landing-check
   string `floor, not a ceiling` → `Floor, not ceiling` (`ebcd82d`).

> Scratch run dir (not committed):
> `…/scratchpad/critique-run/` — fixtures, the withheld `ANSWER-KEY.md`, and `findings-cp{1,2,4}.md`.
