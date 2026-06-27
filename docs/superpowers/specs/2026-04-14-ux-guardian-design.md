# UX Guardian Skill — Design Spec

## Context

When AI tools vibe-code frontend features, UX quality often degrades — missing states, excessive taps, poor accessibility, no error recovery. There's no systematic check ensuring good UX during brainstorming, planning, or implementation. This skill acts as a senior product designer watching over all frontend work: reviewing existing codebases and guiding new development.

**Reference**: Inspired by [swanhtet1992/ux-reviewer](https://github.com/swanhtet1992/ux-reviewer) — adapted and expanded for aphelocoma's dual-mode (review + background guidance) approach.

## Skill Identity

- **Name**: `ux-guardian`
- **Role**: Senior product designer who reads code like a designer reads a prototype
- **Type**: `background` (auto-triggers on frontend work, also manually invocable)
- **Framework**: Agnostic — detects stack, works with React, Vue, Svelte, Django, Rails, Laravel, Flutter, etc.

## Structure

```
skills/ux-guardian/
├── skill.md                        # Full instructions for both modes
├── metadata.yaml                   # name, description, type
├── references/
│   ├── principles.md               # All 10 UX heuristics
│   └── framework-discovery.md      # Framework detection patterns
└── templates/
    └── review.md                   # Template for full review output (--full flag)
```

## Two Operating Modes

### Mode 1: Guardian Mode (Background)

**Trigger**: Auto-activates when AI works on frontend code — during brainstorming, planning, or implementation. Detects via file patterns (components, pages, routes, styles) or conversation context (discussing UI flows, layouts, user journeys).

**Behavior**: Lightweight, non-blocking. Surfaces issues as brief inline nudges.

**Nudge format**:
```
🎯 UX: [one-line issue]. [suggested fix].
```

**Planning/Brainstorming Checklist**:
- Does each screen have a clear primary action?
- Are empty, loading, and error states defined?
- Can user flow be reduced (fewer taps/screens)?
- Is information hierarchy clear?
- Are role-based differences accounted for?
- Mobile/responsive considered?
- Does flow match user's mental model of the task?

**Implementation Checklist**:
- Touch targets ≥44px
- Color contrast meets WCAG AA (4.5:1 text, 3:1 large text)
- Keyboard navigation works
- Form validation with clear, specific error messages
- Loading feedback on async actions
- Meaningful empty states (message + CTA, not blank)
- Consistent spacing and alignment
- Error recovery paths exist (undo, back, retry)
- No dead-end screens

### Mode 2: Review Mode (Manual)

**Trigger**: User invokes `/ux-guardian` or uses trigger phrases: "review UX", "audit UX", "design critique", "flow review", "screen audit", "evaluate app flow", "assess usability".

**Process**: 4 phases, adapted from ux-reviewer reference.

#### Phase 1 — Discovery

Dispatch Explore agent (thoroughness: very thorough) to scan:
1. All templates/components (full file contents)
2. All view/controller logic (data flows, redirects, permissions)
3. All route/URL definitions (complete navigation skeleton)
4. All client-side behavior (JS/TS interactions, forms, state management)
5. CSS/style layer (design system, breakpoints, touch targets)
6. Relevant data models (data shapes behind UI)

Use `references/framework-discovery.md` for framework-specific file patterns.

**Agent returns**: Screen inventory, navigation map, role-based differences, design system summary, interactive behaviors.

#### Phase 2 — Mapping

Build mental models (used for analysis, not all output):
- **Screen inventory**: Every screen, audience, purpose, available actions
- **Flow map per role**: Click-by-click journey for each role's primary task
- **Friction count**: Total taps, screens, decisions before productive work

#### Phase 3 — Analysis

Apply 10 UX principles from `references/principles.md`:

| # | Principle | Core Question |
|---|-----------|---------------|
| 1 | Elimination Test | Does this screen earn its existence? |
| 2 | Conveyor Belt | Do sequential tasks feel sequential? |
| 3 | Clear Next Action | Does every screen answer "what do I do next?" |
| 4 | Use Known State | Does the app act on what it already knows? |
| 5 | Mental Model Match | Does UI mirror how users think about their work? |
| 6 | Proportional Investment | Are primary workflows optimized proportionally? |
| 7 | Surface vs Structure | Are cosmetic and structural issues separated? |
| 8 | Error Recovery | Can users recover gracefully from mistakes? |
| 9 | Consistency | Are patterns consistent within the app? |
| 10 | Accessibility | Does it meet WCAG AA? Keyboard, contrast, screen reader? |

#### Phase 4 — Review Output

**Default (inline)**: 3-5 sentence summary with key insight + top priorities.

**With `--full` flag**: Write complete review to `docs/ux-review.md` using `templates/review.md`.

**Review structure**:
1. **What Works** — specific flows serving users well, with why
2. **Core Tension** — primary structural issue in 1-2 sentences (skip if none)
3. **User's Day** — per-role tap-by-tap narratives: current vs ideal experience, with the gap
4. **What to Cut** — screens/flows to remove + what replaces them
5. **What's Missing** — experiences that should exist but don't, framed as user needs
6. **Priorities** — ordered by user impact (most users × most frequent friction first)

**Language rule**: User-centric only. No file paths, function names, CSS selectors, or implementation details in review output. Describe experience, not code.

- ✗ "The `TaskList` component doesn't handle the empty array case"
- ✓ "Opening Tasks for the first time shows a blank screen — no guidance on what to do next"

## UX Principles (Summary)

Full definitions in `references/principles.md`.

1. **Elimination Test**: Screens that show what user already knows, lists with usually one item, or menus replaceable by smart routing → candidates for removal.
2. **Conveyor Belt**: Sequential workflows should feel sequential, not hub-and-spoke. No "back to list" as primary navigation after completing a sub-task.
3. **Clear Next Action**: ONE dominant primary action per screen. Forward-pointing CTAs. Empty states that tell users what to do, not just what's missing.
4. **Use Known State**: If app knows user role, active session, or next needed action — act on it. Don't show info users must manually filter.
5. **Mental Model Match**: UI should mirror how users describe their work, not backend data structures.
6. **Proportional Investment**: Screens users stare at for hours deserve 10x the attention of once-weekly screens.
7. **Surface vs Structure**: Don't mix cosmetic fixes with structural changes. They have different impact and priority.
8. **Error Recovery**: Undo, back, retry. Clear error messages that say what happened and what to do. No dead ends.
9. **Consistency**: Same action = same pattern everywhere. Consistent terminology, iconography, interaction patterns.
10. **Accessibility**: WCAG AA minimum. Keyboard navigable. Sufficient contrast. Screen reader compatible. Touch targets ≥44px.

## Adapter Considerations

- **Claude Code**: `type: background` in metadata → auto-triggers. Manual invocation via `/ux-guardian`. Adapter override may set `disable-model-invocation: false` to allow both modes.
- **Cursor**: `alwaysApply: true` (background type). Description triggers on frontend file globs.
- **Codex**: Similar to Claude Code pattern.

## Verification

After implementation:
1. Deploy to Claude Code with `/deploy claude`
2. Test guardian mode: start planning a frontend feature → verify UX nudges appear
3. Test review mode: run `/ux-guardian` on a project with frontend code → verify 4-phase process runs and produces structured output
4. Test `--full` flag: verify markdown file written to `docs/ux-review.md`
5. Verify framework detection works (try on React project, then on different framework)
