Detect when a work session is ending and offer to capture context before it's lost.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

## When to activate

Trigger when you notice signals that the session is wrapping up:
- User says "done", "that's it", "wrapping up", "thanks", "bye", or similar
- User asks for a summary of what was done
- A large task has just been completed with no follow-up
- The conversation has reached a natural stopping point

## What to do

1. **Check for existing session record today:**
   - Scan `$APHELOCOMA_HOME/core/sessions/YYYY-MM/` for files starting with today's date that match the current project
   - If a session record already exists: skip to step 3 (only offer journal update)

2. **Offer to create a session record (primary path):**
   - Offer: "Would you like to capture a session record? It preserves the reasoning behind your decisions for future reference."
   - If the user agrees: follow the session-record skill — review the session, generate metadata, write the full structured record to `core/sessions/YYYY-MM/`, update the session index, then proceed to step 3
   - If the user declines: proceed to step 3 with the lightweight journal offer

3. **Offer to update today's journal:**
   - If a session record was just created: offer to append a short summary line referencing it to `$APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md`
   - If no session record was created: offer to create a full journal entry (current behavior)
   - Journal format with session reference:
     ```
     ## HH:MM — [Project Name]
     <1–2 sentence summary>. See: session-YYYY-MM-DD-HHMMSS
     ```
   - Journal format without session record (full entry):
     ```
     ## HH:MM — [Project Name]

     ### What was done
     - Bullet points of accomplishments

     ### Key decisions
     - Any notable decisions and their reasoning

     ### Open threads
     - Unfinished work or things to follow up on
     ```

4. **Check tasks.md:**
   - Also check if `$APHELOCOMA_HOME/core/projects/<project>/tasks.md` needs updating based on completed work

## Rules

- Don't be pushy — offer once, respect if the user declines
- The session record is the richer option; the journal entry is the lightweight fallback — always offer session record first
- If no project record exists, still offer to capture context (use the working directory name as project)
- Keep journal entries concise — they are summaries, not replacements for the session record
