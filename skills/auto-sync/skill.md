Proactively sync project context with the aphelocoma second brain as you work. Do these automatically — the user should not need to ask.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

## After a plan is approved or a task is started

1. Check if `$APHELOCOMA_HOME/core/projects/<project-name>/tasks.md` exists
2. If it does, read the plan's tasks and compare with existing tasks.md
3. Propose adding new tasks under **Planned** (not Done — not implemented yet)
4. Ask for confirmation before writing

## After completing an implementation

1. Check if the current project has a record at `$APHELOCOMA_HOME/core/projects/<project-name>/tasks.md`
2. If it does, read the current tasks and compare with what was just implemented
3. Propose specific updates:
   - Which in-progress or planned tasks to move to Done
   - Any new tasks discovered during implementation to add
4. Ask for confirmation before writing the changes

## After significant architectural or structural work

"Significant" = new integrations, stack decisions, changed patterns, new subsystems, or anything a future session should know.

1. Check if `$APHELOCOMA_HOME/core/projects/<project-name>/` exists
2. If it does:
   - Read `context.md` — assess if Current State or Architecture sections are stale relative to what was just built
   - Check `adrs/` — if the work involved a real decision (why X over Y, library choice, pattern tradeoff), propose a new ADR
   - Check if `local.md` in the project differs meaningfully from the snapshot in `$APHELOCOMA_HOME/core/projects/<project-name>/local.md` — if so, offer to update the snapshot
3. Propose minimal, targeted edits — not rewrites. Ask for confirmation before writing.

## Rules

- Always confirm with the user before writing any changes
- Do not dump context unprompted — act silently, propose changes when relevant
- If no project record exists for the current directory, do nothing
