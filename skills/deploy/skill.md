Deploy aphelocoma skills and context to AI tool configs. Supports multiple tools via adapters.

Input: $ARGUMENTS (optional — tool name: "claude", "cursor", "codex". Default: "claude")

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
     - If metadata.yaml has `arguments`, add as `argument-hint` — **single-quote the value** so hints that start with `[` or contain `:` (e.g. `custom:[roles]`) stay valid YAML; an unquoted `[`-leading value parses as a flow sequence and breaks skill loading
   - Write the generated `SKILL.md` to `~/.claude/skills/<skill-name>/SKILL.md`
   - Copy any templates/, examples/, scripts/, references/ directories alongside the SKILL.md
2. Generate `~/.claude/CLAUDE.md` from `$APHELOCOMA_HOME/adapters/claude-code/claude-md-template.md`
3. Copy agents from `$APHELOCOMA_HOME/adapters/claude-code/agents/` to `~/.claude/agents/`
4. Generate the **Hamilton crew agents** (native parallel subagents). Run the generator:
   ```bash
   python3 "$APHELOCOMA_HOME/adapters/claude-code/scripts/gen-hamilton-crew.py" \
       "$HOME/.claude/skills/aph-hamilton/references" "$HOME/.claude/agents"
   ```
   It fills `agent-template.md` per role — the **implementer** body, or the read-only **reviewer** body for
   look-only roles like `qa-engineer` — applies `settings.default.yaml` model/effort (omitted → inherits
   the session, so the crew follows your best model automatically), writes `~/.claude/agents/hamilton-<role>.md`,
   and prints the `role → model → effort → scope` table. Derived — never hand-edit. These global agents load
   at every session start, so Hamilton dispatches native role agents with no per-run restart (a project that
   overrides models/effort re-runs `/aph-hamilton sync-agents` + restarts). Skip on non-Claude platforms.
5. Report what was deployed (include the crew agent count — it must equal the number of role files; if
   fewer, a role was skipped → regenerate)

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

## Codex

Deploy to `~/.codex/` so skills are available in all Codex sessions.

Steps:
1. For each skill folder:
   - Read `skill.md` and `metadata.yaml`
   - Check for a Codex-specific override at `$APHELOCOMA_HOME/adapters/codex/overrides/<skill-name>.yaml`
   - Generate `SKILL.md` with Codex frontmatter:
     - From metadata.yaml: `name`, `description`
     - Type mapping: `type: manual` → add `disable-model-invocation: true`; `type: background` → add `user-invocable: false`
     - Merge any fields from the override file
   - Write the generated `SKILL.md` to `~/.codex/skills/<skill-name>/SKILL.md`
   - Copy any templates/, examples/, scripts/, references/ directories alongside the SKILL.md
2. Generate `~/.codex/AGENTS.md` from `$APHELOCOMA_HOME/adapters/codex/agents-md-template.md`
3. Copy `hooks.json` from `$APHELOCOMA_HOME/adapters/codex/hooks.json` to `~/.codex/hooks.json`
4. Report what was deployed
