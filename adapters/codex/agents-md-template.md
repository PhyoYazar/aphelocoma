# Global Codex Instructions

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var). All paths below use $APHELOCOMA_HOME.

## Aphelocoma Second Brain

Context sync is handled by the `auto-sync` and `session-end` skills. They run in the background — no user action needed.

When working in a project directory registered with aphelocoma, you have access to:
- Project context, tasks, and ADRs at `$APHELOCOMA_HOME/core/projects/<project-name>/`
- Knowledge base at `$APHELOCOMA_HOME/core/knowledge/`
- Journal entries at `$APHELOCOMA_HOME/core/journal/`
- Identity and preferences at `$APHELOCOMA_HOME/core/identity/`
