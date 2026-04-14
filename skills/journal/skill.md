Capture an end-of-session work journal entry.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

## Steps

1. **Check for session records today:**
   - Look in `$APHELOCOMA_HOME/core/sessions/YYYY-MM/` for files starting with today's date
   - If session records exist: generate the journal entry as a concise summary that references them (see Session-Referenced Format below)
   - If no session records exist: generate a full journal entry from git history and conversation context (see Full Format below)

2. **Write the entry:**
   - Path: `$APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md`
   - Use today's date. Create the month directory if it does not exist.
   - If the file already exists, append the new entry (do not overwrite previous entries from the same day)
   - Use the template at `${CLAUDE_SKILL_DIR}/templates/entry.md`

3. **Add frontmatter if this is a new file:**
   - New journal files get YAML frontmatter (see template)
   - If appending to an existing file that already has frontmatter, update the `projects` and `sessions` fields if needed

## Session-Referenced Format (when session records exist today)

```
## HH:MM — [Project Name]
<1–2 sentence summary of what was accomplished>. See: session-YYYY-MM-DD-HHMMSS
```

For multiple sessions in one day, add one block per session. The journal is the daily digest; the session record has the full detail.

## Full Format (when no session records exist)

Review what was accomplished by looking at recent git history, open files, and conversation context. Then write:

```
## HH:MM — [Project Name]

### What was done
- Bullet points of accomplishments

### Key decisions
- Any notable decisions and their reasoning

### Open threads
- Unfinished work or things to follow up on
```
