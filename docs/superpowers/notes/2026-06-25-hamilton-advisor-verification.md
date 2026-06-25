# Hamilton — Advisor Collaboration Verification (verdict: PASS)

_Date: 2026-06-25. Branch: `hamilton-phase-1`._

Gate for the advisor-collaboration revision. An **interactive** flow can't be fully cold-started
without a human, so this splits into: (1) an **executed run** with *scripted advisor picks* that proves
the autonomous machinery + correct artifacts; (2) a **manual checklist** the user drives for the real
interactive pauses. Run against the **repo** definition (deploy is the user's).

## Method (executed run)

A throwaway **existing** project (`scratchpad/advisor-existing/` with a stub `index.html` + `README.md`)
was handed to a fresh agent running the Hamilton advisor flow (PROTOCOL §1.5), with the advisor's picks
pre-scripted at each checkpoint. Brief: *"Add a footer with '© 2026 Acme'."*

## Checks a–e — PASS (mechanical assertions on the produced `.aphelocoma/`)

- **(a) Leadership-first** — `role_activated` order was `cto` → `software-architect` → `product-manager`
  → (after Checkpoint 1) `fullstack-developer`. The implementer was hired only *after* Discovery.
- **(b) `decision` events** — exactly **4**, all `actor: advisor` (seq 5, 9, 15, 20 = the four
  checkpoints), each `note` carrying the options offered + the pick. One new ledger event type, working.
- **(c) Build-in-place at the project root** — the footer was added to the **existing** `index.html`
  in place; **no `product/` directory**; product files sit beside `.aphelocoma/`.
- **(d) Ledger integrity** — schema-valid `{ts,seq,event,actor,task,to,note}`, strictly monotonic
  `seq` 1..23 (no gaps), `decision` accepted in the vocabulary.
- **(e) Survey-first on the existing project** — Discovery logged a `brainstorm_note` that read the
  existing `index.html`/`README` *before* proposing — confirming "survey first, build in place".

Also: all three leadership roles wrote their own `ledger/agents/<role>.md` logs.

## Manual checklist (the user drives — the genuinely-interactive parts)

The scripted run can't prove the crew actually *stops and asks you*. After you deploy, verify by hand:

1. **Bare `/aph-hamilton`** opens the guided start (new-or-existing? what to build?), and does **not**
   ask crew size upfront.
2. **Vague brief** (e.g. `/aph-hamilton` then "an ecommerce") → the crew asks **clarifying questions**
   and proposes 2–3 directions with trade-offs, rather than guessing a product.
3. The crew **actually pauses** at the four checkpoints (direction+size, plan, build-style, review) and
   waits for your pick; **"you decide"** makes it proceed with its recommendation.
4. On an **existing** repo, it surveys your code first and **edits in place** (no `product/` folder).
5. `/aph-hamilton resume` on an in-progress `.aphelocoma/` continues without re-asking; running `start`
   where `.aphelocoma/` already exists offers `resume` instead of overwriting.

## Scope / honesty

- The executed run used **scripted advisor picks** (a subagent can't pause for a human) and the **repo**
  definition. It proves the flow produces correct artifacts — leadership-first, the 4 `decision`
  checkpoints, survey-first, build-in-place-at-root, schema-valid monotonic ledger. The *interactive
  stop-and-ask* behavior is the manual checklist above.
- State-integrity + parallel single-writer are unchanged from Phase 2 (the build-style checkpoint just
  replaces the old settings toggle); the ledger came out gap-free monotonic here too.

## Verdict

**PASS** — Hamilton's advisor-collaboration flow runs end-to-end: you advise at four checkpoints (each a
`decision`), the leadership core brainstorms first and the crew is sized after Discovery, the product
builds in place at the project root (no `product/`), and existing projects are surveyed before changes —
with a schema-valid, monotonic ledger. Interactive stop-and-ask verified via the manual checklist.
