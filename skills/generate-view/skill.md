Generate a context summary for web-based AI tools (Claude.ai, ChatGPT, Gemini).

Input: $ARGUMENTS (optional — "full", "brief", or "project <name>". Default: "full")

The generated view is saved to `$APHELOCOMA_HOME/views/` and displayed for copy-paste.

## Full view (default)

Generate a comprehensive context document. Steps:

1. Read `$APHELOCOMA_HOME/core/identity/profile.md` and `preferences.md`
2. Read `$APHELOCOMA_HOME/core/projects/registry.json` and each active project's context.md and tasks.md
3. Read the most recent journal entry for open threads
4. Read `$APHELOCOMA_HOME/core/knowledge/INDEX.md` for expertise summary
5. Compose the view using the template at `${CLAUDE_SKILL_DIR}/templates/full.md`
6. Save to `$APHELOCOMA_HOME/views/full-context.md`
7. Display the content so the user can copy-paste it into Claude.ai Projects, ChatGPT custom instructions, or any web AI

## Brief view

Generate a condensed summary (under 2000 characters for tools with short limits like ChatGPT). Steps:

1. Read profile.md for role and current focus
2. List active projects (name + one-line summary only)
3. List open threads from the most recent journal
4. Compose using the template at `${CLAUDE_SKILL_DIR}/templates/brief.md`
5. Save to `$APHELOCOMA_HOME/views/brief-context.md`

## Project view

Generate context for a single project. Steps:

1. Read the specified project's context.md, tasks.md, and latest ADR
2. Include identity/profile.md for personal context
3. Save to `$APHELOCOMA_HOME/views/project-<name>.md`
