Sync the current project with the aphelocoma second brain. Run this anytime to bring aphelocoma up to date.

Steps:

1. **Identify the project:**
   - Read $APHELOCOMA_HOME/core/projects/registry.json
   - Check if the current working directory (or any parent) matches a registered project
   - If not registered, offer to run `/project-init <project-name>` to set up the record

2. **Check for gaps and fix each one:**

   a. **Registry**: Is the current working directory registered? If not, offer to add it to registry.json.

   b. **local.md (local)**: Does the current project have a local context file (CLAUDE.local.md for Claude Code, or equivalent)? If not, offer to create one with the aphelocoma reference marker.

   c. **local.md (snapshot)**: Does `$APHELOCOMA_HOME/core/projects/<project-name>/local.md` exist? If the project has a local context file but aphelocoma doesn't have a snapshot, offer to copy it. If both exist, check for meaningful drift and offer to update the snapshot.

   d. **tasks.md**: Is `$APHELOCOMA_HOME/core/projects/<project-name>/tasks.md` empty or missing tasks? If there's a current plan, offer to add the plan's tasks under **Planned**. If work has been done this session, offer to move tasks to **Done**.

   e. **context.md**: Read `$APHELOCOMA_HOME/core/projects/<project-name>/context.md`. Is the Current State or Architecture section stale? If so, propose specific updates.

   f. **ADRs**: Were any significant decisions made in this session? If so, offer to create an ADR via `/adr <project-name> <title>`.

3. **Report what was synced** — summarize what was updated, what was already current, and what was skipped.

4. **Remind**: "Run `/journal` at the end of this session to capture your work."

Ask for confirmation before each write. Propose changes one at a time.
