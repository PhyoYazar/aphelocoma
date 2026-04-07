Initialize a new project record in aphelocoma. The project name is: $ARGUMENTS

Steps:
1. Create the directory `$APHELOCOMA_HOME/core/projects/<project-name>/` (use kebab-case)
2. Copy the template files from `${CLAUDE_SKILL_DIR}/templates/`:
   - `context.md` — replace "Project Name" with the actual project name
   - `tasks.md` — start with empty sections
   - `adrs/` — create the directory (no initial ADR needed)
3. Ask the user for a brief overview of the project and fill in the context.md Overview section
4. If a local context file exists in the current working directory (e.g., CLAUDE.local.md, .cursorrules), ask:
   "Copy this project's local context into the aphelocoma record as a personal snapshot? (y/n)"
   If yes, copy it to `$APHELOCOMA_HOME/core/projects/<project-name>/local.md` and prepend:
   `<!-- Mirror of <project-name> local context as of YYYY-MM-DD. Not auto-synced. -->`
5. Register the project in `$APHELOCOMA_HOME/core/projects/registry.json`:
   - Read the existing registry (or create it if missing)
   - Add the project with the current working directory as its path
   - Format: `"<project-name>": {"paths": ["<current-working-directory>"]}`
6. Report what was created
