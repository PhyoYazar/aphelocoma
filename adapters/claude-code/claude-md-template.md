# Global Claude Code Instructions

## Plan Mode Rules

- When plan mode re-activates and a plan file already exists, check if it is relevant to the CURRENT user request. If not, overwrite it with a new plan for the current task. Never re-present a completed/stale plan.
- If the user asks for a simple action (commit, run a command, quick edit) and plan mode activates, exit immediately — write a one-line plan for the current action and call ExitPlanMode.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var). All paths below use $APHELOCOMA_HOME.

## Aphelocoma Second Brain

### After a plan is approved (ExitPlanMode)

1. Check if `$APHELOCOMA_HOME/core/projects/<project-name>/tasks.md` exists
2. If it does, read the plan's tasks and compare with existing tasks.md
3. Propose adding new tasks under **Planned** (not Done — not implemented yet)
4. Ask for confirmation before writing

### After completing an implementation from an approved plan

1. Check if the current project has a record at `$APHELOCOMA_HOME/core/projects/<project-name>/tasks.md`
2. If it does, read the current tasks and compare with what was just implemented
3. Propose specific updates:
   - Which in-progress or planned tasks to move to Done
   - Any new tasks discovered during implementation to add
4. Ask for confirmation before writing the changes

### After significant architectural or structural work

"Significant" = new integrations, stack decisions, changed patterns, new subsystems, or anything a future session should know.

1. Check if `$APHELOCOMA_HOME/core/projects/<project-name>/` exists
2. If it does:
   - Read `context.md` — assess if Current State or Architecture sections are stale relative to what was just built
   - Check `adrs/` — if the work involved a real decision (why X over Y, library choice, pattern tradeoff), propose a new ADR via `/adr <project-name> <title>`
   - Check if `local.md` in the project differs meaningfully from the snapshot in `$APHELOCOMA_HOME/core/projects/<project-name>/local.md` — if so, offer to update the snapshot
3. Propose minimal, targeted edits — not rewrites. Ask for confirmation before writing.

Do these proactively — the user should not need to ask.
