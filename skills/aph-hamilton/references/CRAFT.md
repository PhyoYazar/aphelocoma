# CRAFT — the code-quality bar (read-only)

Hamilton's **always-on** standard for *how code is written*. It applies to every task's code on every
project, independent of the TDD toggle. Implementers write to it during Implementation (PROTOCOL §2
Phase 4); the CP4 critique enforces it (PROTOCOL §2 Phase 5; see `CRITIQUE.md`).

It is a **floor, not a ceiling** — the question is always *"is this below the bar?"* (a pass/fail
threshold), never *"could this be polished further?"*. Most code is already above the floor and passes
untouched.

## Precedence — when two principles pull against each other, the higher wins

> **correctness / error-handling  >  consistency-with-existing  >  simplicity (incl. YAGNI)**

The order is what keeps the bar from thrashing: a finding is only valid if a higher principle does not
already justify the code.

## The three principles

1. **Error handling** — handle every *plausible* failure path: validate inputs at boundaries, don't
   swallow errors, fail loudly or degrade deliberately, clean up resources. Do **not** handle
   *impossible* failures — that is the complexity simplicity catches. (This is the code-level cousin of
   the architectural **fault-tolerance** FOUNDATIONS topic, decided with the advisor at Discovery; this
   bar is per-function and always-on.)
2. **Consistency** — match the patterns and conventions that **already exist** in the codebase (naming,
   structure, error style, libraries); reuse what exists instead of duplicating. It is **never** a
   mandate to invent a new abstraction for hypothetical future reuse. _Escape hatch:_ when the prevailing
   pattern is clearly poor, or two existing patterns conflict, correctness/simplicity win and the
   divergence is noted — don't cement an anti-pattern.
3. **Simplicity (YAGNI)** — the simplest thing that works within the above: no premature abstraction, no
   dead code, no needless config or indirection, prefer the boring solution. "Might be reused later" is
   **not** a reason to abstract now.

## Why it converges (the conflict this resolves)

*Example:* an implementer writes a simple inline solution; could it be "made consistent / reusable"? One
question decides it — **does a shared pattern already exist?**
- **Yes** → reuse it (consistency says so, and reuse is also simpler — both agree).
- **No, it could only hypothetically be reused** → leave it inline (YAGNI; consistency is silent — there
  is nothing to match yet).

Deterministic, no oscillation. And because implementers and the reviewer read *this same file*, the
reviewer has nothing to re-litigate.
