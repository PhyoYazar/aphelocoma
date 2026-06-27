Show a dashboard of the aphelocoma second brain's current state.

Steps:

1. **Projects:**
   - Read $APHELOCOMA_HOME/core/projects/registry.json
   - For each registered project, read its context.md and tasks.md
   - Show: project name, registered path, number of in-progress tasks, number of planned tasks, number of ADRs
   - Flag any project whose context.md hasn't been modified in 30+ days as "potentially stale"

2. **Knowledge base:**
   - Read $APHELOCOMA_HOME/core/knowledge/INDEX.md (or list knowledge/ if INDEX.md is missing)
   - Show: total topic count, total file count

3. **Journal:**
   - Find the most recent journal entry in $APHELOCOMA_HOME/core/journal/
   - Show: last journal date, number of entries in the current month

4. **Open threads:**
   - Scan the most recent journal entry's "Open threads" sections
   - List any unresolved items

5. **Format as a clean summary** — use a table or structured list. Keep it concise.
