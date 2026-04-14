# UX Principles

10 structural UX principles for evaluating and guiding frontend work. Apply during both guardian mode (lightweight nudges) and review mode (full analysis).

## 1. The Elimination Test

**Core question**: Does this screen earn its existence?

A screen fails the elimination test when:
- It shows information the user already knows
- It's a list where there's usually only one relevant item
- It's a menu that could be replaced by smart routing based on app state
- Users always click the same thing — the app could just take them there
- It exists only because the data model has a table for it

**What to do**: Remove the screen. Route users directly to where they need to be. If a list usually has one item, skip it and go straight to that item. If a dashboard just links to the one thing users always click, open that thing directly.

**Anti-pattern**: "But what if they need to see the list someday?" — Then make it accessible from a menu. Don't force everyone through it every time.

## 2. Conveyor Belt, Not Filing Cabinet

**Core question**: Do sequential tasks feel sequential?

Sequential workflows should carry users forward automatically, not dump them at a hub to manually find the next item.

Signs of filing cabinet structure:
- Landing pages with multiple equal-weight buttons
- Lists requiring scanning for the active/current item
- "Back to [list]" as primary post-completion navigation
- No auto-advance after completing a sub-task
- Hub-and-spoke instead of linear flow

**What to do**: After completing step N, automatically present step N+1. When a user finishes reviewing one item, show the next item — don't send them back to the list to hunt for it.

**Anti-pattern**: Dashboard → List → Item → [complete] → List → Item → [complete] → List. Should be: Dashboard → Item → [complete] → Next Item → [complete] → Done.

## 3. Clear Next Action

**Core question**: Does every screen answer "what do I do next?"

Every screen must have:
- ONE clear primary action with dominant visual weight
- Immediate presentation of the next step upon completion
- Empty states that explain what to do ("Create your first project"), not just what's missing ("No projects found")
- Forward-pointing CTAs after success ("Continue to settings"), not backward ("Back to list")

**What to do**: Identify the primary action for each screen. Make it visually dominant. After any action completes, point the user forward. Replace empty states with actionable guidance.

**Anti-pattern**: Success toast that disappears, leaving user on same screen with no indication of what to do next.

## 4. Use Known State

**Core question**: Does the app act on what it already knows?

If the app knows the user's role, current session, active task, or needed action — it should act on that knowledge rather than presenting it as information for the user to process.

**Ask**: What does the app know that the user must currently figure out manually?

Classic examples:
- App knows one active session exists, but shows a full list of sessions
- App knows user's role, but shows a generic dashboard with all options
- App knows which step is next in a workflow, but shows all steps equally

**What to do**: Use known state to pre-select, pre-filter, or skip entirely. If there's one active session, go to it. If the user's role means they only use 2 of 8 features, show those 2.

## 5. Mental Model Match

**Core question**: Does the UI mirror how users think about their work?

The UI should reflect users' mental model of their work, not the backend data structure or developer's model.

**Ask**: Would a non-technical person describe the same steps the app forces them through?

Examples of mismatches:
- User thinks "I need to count stock" → App requires: navigate to sessions, find active session, open it, select count mode
- User thinks "I want to reply" → App requires: open thread, scroll to bottom, click reply, select reply type, compose
- Organizing by database tables instead of user tasks

**What to do**: Name things the way users name them. Organize by user tasks, not data types. If users say "I need to do X," the app should let them do X in the fewest steps that match their thinking.

## 6. Proportional Investment

**Core question**: Are primary workflows optimized proportionally to their frequency?

The screen users stare at for hours deserves 10x the attention of a screen they visit once a week.

**Prioritize**:
- High-frequency screens → optimize for speed, keyboard shortcuts, minimal clicks
- Medium-frequency screens → clear and functional, reasonable flow
- Low-frequency screens → simple is fine, don't over-engineer

**What to do**: Identify which screens users spend the most time on. Invest heavily in those. Login pages and settings can be simple. The core workflow screen needs to be fast, forgiving, and designed for sustained use.

**Anti-pattern**: Spending equal effort on an admin settings page and the primary data-entry screen that users live in all day.

## 7. Surface vs Structure

**Core question**: Are cosmetic issues separated from structural issues?

Surface and structure have different goals and impact:
- **Surface**: styling, icons, spacing, alignment, color consistency, typography
- **Structure**: eliminating screens, merging steps, intelligent routing, flow redesign

**What to do**: Don't interleave surface and structural changes. Structural improvements (removing screens, changing flows) have fundamentally different impact than surface improvements (fixing alignment, updating colors). In reviews, separate them clearly. In implementation, structural changes first — they may make surface changes moot.

**Anti-pattern**: Mixing "change button color" and "eliminate this entire screen" in the same priority list as if they're comparable.

## 8. Error Recovery

**Core question**: Can users recover gracefully from mistakes?

Every destructive or significant action needs a recovery path:
- **Undo** for reversible actions
- **Confirmation** for destructive actions (delete, submit, send)
- **Back/cancel** that preserves work (not "discard and go back")
- **Retry** for failed operations with clear explanation of what went wrong
- **Clear error messages** that say what happened AND what to do about it

**What to do**: For each user action, ask "what if they didn't mean to do that?" and "what if it fails?" Ensure there's always a way forward or back. Never show a dead-end screen.

**Anti-pattern**: Error message: "Something went wrong." No retry button, no explanation, no way to recover entered data.

## 9. Consistency

**Core question**: Are patterns consistent within the app?

Same action should look and work the same everywhere:
- Consistent button placement (primary action always in same position)
- Consistent terminology (don't call it "projects" on one page and "workspaces" on another)
- Consistent iconography (same icon = same meaning)
- Consistent interaction patterns (if swipe-to-delete works in one list, it should work in all lists)
- Consistent feedback (if one form shows inline errors, all forms should)

**What to do**: Audit for terminology drift, inconsistent button placement, mixed interaction patterns. Pick one pattern and apply it everywhere. Consistency reduces cognitive load — users learn once, apply everywhere.

**Anti-pattern**: Save button on the left in settings, on the right in profile, and in a floating bar in the editor.

## 10. Accessibility

**Core question**: Does it meet WCAG AA? Can everyone use it?

Minimum requirements:
- **Color contrast**: 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold)
- **Touch targets**: ≥44×44px on mobile
- **Keyboard navigation**: All interactive elements focusable and operable via keyboard
- **Focus indicators**: Visible focus ring on all interactive elements
- **Screen readers**: Semantic HTML, ARIA labels where needed, meaningful alt text
- **Form labels**: Every input has an associated label (not just placeholder text)
- **Motion**: Respect `prefers-reduced-motion`
- **Responsive**: Usable at 320px viewport width minimum

**What to do**: Test with keyboard only (tab through the entire flow). Check contrast with a tool. Ensure all images have alt text. Use semantic HTML elements (`<button>`, `<nav>`, `<main>`) instead of generic `<div>` with click handlers.

**Anti-pattern**: Beautiful UI that's completely unusable without a mouse, or has light gray text on white background.
