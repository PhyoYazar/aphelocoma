Create a new Architecture Decision Record (ADR) for a project.

Input: $ARGUMENTS
Format: `<project-name> <decision-title>`
Example: `/adr anime-pomodoro use-swiftui-for-widgets`

Steps:
1. Find the project directory at `$APHELOCOMA_HOME/core/projects/<project-name>/adrs/`
2. If the project doesn't exist, tell the user to run `/project-init <project-name>` first
3. Determine the next ADR number by checking existing files in the adrs/ directory
4. Create `adrs/NNNN-<decision-title>.md` using the template at `${CLAUDE_SKILL_DIR}/templates/adr.md`
5. Ask the user to fill in the Context, Decision, and Consequences — or offer to help draft them based on a brief description
