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
4. Generate the **Hamilton crew roles** (named collab-tool agents — the Codex analog of Claude Code's
   crew agents). Run the generator:
   ```bash
   python3 "$APHELOCOMA_HOME/adapters/codex/scripts/gen-hamilton-crew-codex.py" \
       "$HOME/.codex/skills/aph-hamilton/references" "$HOME/.codex"
   ```
   It writes one `~/.codex/agents/hamilton-<role>.toml` per role (display nickname = role title;
   implementer or read-only reviewer contract as `developer_instructions`, from `agent-template.md`)
   and maintains a **managed block** in `~/.codex/config.toml` (between
   `# >>> aphelocoma hamilton crew >>>` / `# <<< ... <<<` markers — it never touches anything else,
   and re-runs replace the block idempotently). Hamilton then spawns workers with
   `agent_type: "hamilton-<role>"` so the UI shows the role, not a thread id. Per-role model/effort
   are passed at spawn time from a project's settings.yaml — not baked in. Derived — never hand-edit.
5. **Hamilton parallel readiness note.** Verify and report in one line:
   - `~/.codex/skills/aph-hamilton/references/` contains `DISPATCH-CODEX.md`,
     `result.implementer.schema.json`, `result.reviewer.schema.json` (they ride along with step 1's
     references/ copy — if missing, re-copy).
   - The crew role count from step 4 equals the number of role files (27); if fewer, regenerate.
   - For the `codex exec` fallback backend: if `~/.codex/config.toml` lacks
     `[sandbox_workspace_write] network_access = true`, mention that fan-out dispatch will ask for
     escalated permission at Checkpoint 3 (DISPATCH-CODEX.md preflight) — optional to add, never edit
     it beyond the step-4 managed block unprompted.
6. Report what was deployed
