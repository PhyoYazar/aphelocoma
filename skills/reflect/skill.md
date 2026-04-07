End-of-session review that extracts reusable patterns and proposes knowledge base updates.

This closes the learning loop: work happened, journal captured it, now reflect on what is worth keeping permanently.

Steps:

1. **Review recent activity:**
   - Read today's journal entry from $APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md
   - If no entry exists for today, check the last 3 days
   - Read any "Key decisions" and "Open threads" sections carefully

2. **Scan for knowledge gaps:**
   - Read $APHELOCOMA_HOME/core/knowledge/INDEX.md to see existing topics
   - Compare what was worked on recently against what knowledge exists
   - Identify topics that came up in work but have no knowledge file yet

3. **Propose knowledge captures:**
   Present a numbered list of potential knowledge entries. For each:
   - Proposed file path: knowledge/<topic>/<name>.md
   - One-sentence summary of what it would capture
   - Source: which journal entry or decision it comes from

4. **Ask the user which ones to create.**
   Do not create all automatically. Let the user pick: "all", "1 and 3", or "none".

5. **Create the selected knowledge files** using the /capture format.

6. **Update project context if needed:**
   - If the session revealed new architectural decisions, offer to update the project's context.md
   - If tasks were completed, offer to update tasks.md

7. **Summary:** Report what was captured.
