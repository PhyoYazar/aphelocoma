One-command session wrap-up. Analyzes what happened, decides which recording steps are needed, and runs them.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

---

# Phase 1 — Analyze the Session

Gather context to decide what needs recording:

1. **Git history**: Run `git log --oneline` for commits made this session. Note what changed (new features, refactors, fixes, new files/patterns).
2. **Files changed**: Run `git diff --stat` against the starting point. Categorize: code, config, docs, skills, architecture.
3. **Conversation context**: Review what was discussed, decided, and learned during this session.
4. **Project registration**: Check `$APHELOCOMA_HOME/core/projects/registry.json` — is the current project registered?

---

# Phase 2 — Decide What to Record

Apply this decision matrix:

| Step | Run when | Skip when |
|------|----------|-----------|
| **Sync** | Project is registered in aphelocoma | No project record exists (offer `/project-init` instead) |
| **Session record** | Session had significant reasoning: design decisions, multi-step problem solving, trade-off analysis, debugging chains | Simple/mechanical changes only (typo fixes, version bumps, straightforward implementation) |
| **Journal** | Always | Never — every session gets an entry |
| **ADR** | Architectural or structural decisions were made: new patterns, library choices, convention changes, significant design changes | No meaningful decisions — just implementation of existing plans |
| **Capture** | Reusable knowledge emerged: tool quirks, framework behaviors, workflow patterns, techniques applicable beyond this project | Everything learned is project-specific or already documented |

**Present the plan to the user:**

```
## Wrap-up Plan

✅ Will run:
- [Step]: [one-line reason]
- [Step]: [one-line reason]

⏭️ Skipping:
- [Step]: [one-line reason why not needed]

Adjust? Or proceed?
```

Wait for user confirmation. If they want to add or remove steps, adjust.

---

# Phase 3 — Execute

Run each approved step in order. For each step, follow the existing skill's logic — do not reimplement.

## 1. Sync (if approved)

Follow the sync skill's logic:
- Check registry, tasks.md, context.md, local.md, ADR gaps
- Propose specific updates for each
- Ask confirmation before each write

Key paths:
- `$APHELOCOMA_HOME/core/projects/<project>/tasks.md`
- `$APHELOCOMA_HOME/core/projects/<project>/context.md`
- `$APHELOCOMA_HOME/core/projects/<project>/local.md`

## 2. Session Record (if approved)

Follow the session-record skill's logic:
- Review session for reasoning chains, decisions, key moments
- Generate structured record with metadata frontmatter
- Write to `$APHELOCOMA_HOME/core/sessions/YYYY-MM/YYYY-MM-DD-HHMMSS-<slug>.md`
- Update session index if one exists

## 3. Journal (always)

Follow the journal skill's logic:
- If session record was created in step 2: use session-referenced format (short summary + reference)
- If no session record: use full format (what was done, key decisions, open threads)
- Write to `$APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md`
- Append if file exists, create with frontmatter if new

## 4. ADR (if approved)

Follow the ADR skill's logic:
- Determine next ADR number from existing files in `$APHELOCOMA_HOME/core/projects/<project>/adrs/`
- Draft the ADR with Context, Decision, Consequences from session context
- Present draft for user review before writing

## 5. Capture (if approved)

Follow the capture skill's logic:
- Identify reusable knowledge from the session
- Check `$APHELOCOMA_HOME/core/knowledge/INDEX.md` to avoid duplicates
- Write focused knowledge file(s)
- Update the knowledge index

---

# Phase 4 — Report

After all steps complete, show a summary:

```
## Wrap-up Complete

✅ Synced: tasks.md (2 tasks → Done), context.md (updated Current State)
✅ Session record: core/sessions/2026-04/2026-04-16-143022-ux-guardian-skill.md
✅ Journal: core/journal/2026-04/2026-04-16.md
✅ ADR: core/projects/aphelocoma/adrs/0005-dual-mode-skill-pattern.md
⏭️ Capture: skipped (no cross-project knowledge)
```

---

# Rules

- **Delegate, don't duplicate**: Follow each skill's existing logic. If those skills evolve, wrap-up automatically benefits.
- **Confirm before writing**: Present the plan first. Never write without user approval.
- **One confirmation for the plan, individual confirms for writes**: User approves the overall plan once, then confirms each individual write as each sub-step executes.
- **Don't be redundant with session-end**: If `session-end` (background) already ran and created records, detect that and skip those steps. Check for existing journal entries and session records from today before creating new ones.
