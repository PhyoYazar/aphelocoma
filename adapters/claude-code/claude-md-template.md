# Global Claude Code Instructions

## Plan Mode Rules

- When plan mode re-activates and a plan file already exists, check if it is relevant to the CURRENT user request. If not, overwrite it with a new plan for the current task. Never re-present a completed/stale plan.
- If the user asks for a simple action (commit, run a command, quick edit) and plan mode activates, exit immediately — write a one-line plan for the current action and call ExitPlanMode.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var). All paths below use $APHELOCOMA_HOME.

## Aphelocoma Second Brain

Context sync is handled by the `auto-sync` and `session-end` skills. They run in the background — no user action needed.
