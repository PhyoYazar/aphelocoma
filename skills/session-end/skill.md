Detect when a work session is ending and offer to capture context before it's lost.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

## When to activate

Trigger when you notice signals that the session is wrapping up:
- User says "done", "that's it", "wrapping up", "thanks", "bye", or similar
- User asks for a summary of what was done
- A large task has just been completed with no follow-up
- The conversation has reached a natural stopping point

## What to do

1. Offer to create a journal entry for this session
2. If the user agrees, review the session:
   - Recent git history (`git log --oneline` for today)
   - What was discussed and implemented
   - Key decisions and their reasoning
   - Unfinished work or open threads
3. Write to `$APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md`
   - Create the month directory if it doesn't exist
   - If the file already exists, append (don't overwrite)
   - Use this format:

```
## HH:MM — [Project Name]

### What was done
- Bullet points of accomplishments

### Key decisions
- Any notable decisions and their reasoning

### Open threads
- Unfinished work or things to follow up on
```

4. Also check if `tasks.md` needs updating based on completed work

## Rules

- Don't be pushy — offer once, respect if the user declines
- Keep the journal entry concise — capture what matters, not every detail
- If no project record exists, still offer to journal (use the working directory name)
