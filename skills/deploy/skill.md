Deploy aphelocoma skills and context to AI tool configs. Supports multiple tools via adapters.

Input: $ARGUMENTS (optional — tool name: "claude", "cursor". Default: "claude")

## Claude Code (default)

Deploy to `~/.claude/` so skills are available in all Claude Code sessions.

Steps:
1. For each skill folder in `$APHELOCOMA_HOME/skills/`:
   - Read `skill.md` and `metadata.yaml`
   - Check for a Claude-specific override at `$APHELOCOMA_HOME/adapters/claude-code/overrides/<skill-name>.yaml`
   - Generate `SKILL.md` with Claude Code frontmatter:
     - From metadata.yaml: `name`, `description`
     - Type mapping: `type: manual` → add `disable-model-invocation: true`; `type: background` → add `user-invocable: false`
     - Merge any fields from the override file
     - If metadata.yaml has `arguments`, add as `argument-hint`
   - Write the generated `SKILL.md` to `~/.claude/skills/<skill-name>/SKILL.md`
   - Copy any templates/, examples/, scripts/ directories alongside the SKILL.md
2. Generate `~/.claude/CLAUDE.md` from `$APHELOCOMA_HOME/adapters/claude-code/claude-md-template.md`
3. Copy agents from `$APHELOCOMA_HOME/adapters/claude-code/agents/` to `~/.claude/agents/`
4. Report what was deployed

## Cursor

Deploy context and knowledge rules to the current project's `.cursor/rules/` directory.

Run the Cursor deploy script:

```bash
bash $APHELOCOMA_HOME/adapters/cursor/scripts/deploy.sh
```

This generates:
- `.cursor/rules/aphelocoma-context.mdc` — identity + project context + tasks + latest ADR (alwaysApply: true)
- `.cursor/rules/aphelocoma-knowledge.mdc` — full knowledge base content (alwaysApply: true)

The script auto-detects the project from registry.json. If the project isn't registered, it warns and skips project-specific content.

To deploy to a different project directory:
```bash
bash $APHELOCOMA_HOME/adapters/cursor/scripts/deploy.sh /path/to/project
```

Report what was deployed after the script completes.
