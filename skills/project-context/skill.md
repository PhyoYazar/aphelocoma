Project context loader for aphelocoma second brain.

Activate silently on session start in any project directory, or when the user asks about project context, architecture, tasks, or decisions.

When activated:

1. Read $APHELOCOMA_HOME/core/projects/registry.json to find the current project
   - Check if the current working directory (or any parent) matches a registered project path
   - If no match, fall back to checking the last component of the path against project directory names
2. If a project is identified, read these files silently from $APHELOCOMA_HOME/core/projects/<project-name>/:
   - context.md — project overview, tech stack, architecture, current state
   - tasks.md — current task status
   - local.md — personal workflow preferences and local notes (if it exists)
   - The most recent ADR in adrs/ — latest architectural decisions
3. Also check today's journal entry at $APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md for any mentions of this project
4. Use this context to inform your responses — you now know what this project is, its architecture, what's in progress, and what was worked on recently

Do NOT dump all this context unprompted. Simply be aware of it. If the user asks "what was I working on?" or "what's the current state?", you have the answer ready.

If no project record exists, do nothing. Do not suggest creating one unless the user seems to be starting a new project.
