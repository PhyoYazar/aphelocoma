Distill insights from journal entries or conversation into knowledge files.

Input: $ARGUMENTS (optional — a topic hint like "prisma" or "error-handling")

Steps:

1. **Gather source material:**
   - If a topic is provided, search $APHELOCOMA_HOME/core/journal/ and $APHELOCOMA_HOME/core/projects/ for entries mentioning it
   - If no topic, read the most recent journal entries (last 3 days) from $APHELOCOMA_HOME/core/journal/YYYY-MM/
   - Also consider the current conversation context

2. **Identify reusable knowledge:**
   Look for patterns useful beyond the original project:
   - Technical insights (tool quirks, framework behaviors)
   - Architectural patterns (design approaches that worked)
   - Workflow lessons (process improvements)
   - Tool-specific knowledge (CLI flags, config gotchas)

   Skip anything purely project-specific (that belongs in projects/).

3. **Check existing knowledge:**
   - Read $APHELOCOMA_HOME/core/knowledge/INDEX.md to see existing topics and files
   - If a relevant topic exists, read existing files to avoid duplication
   - Decide whether to create a new file or append to an existing one

4. **Write the knowledge file:**
   - Place it in $APHELOCOMA_HOME/core/knowledge/<topic>/<specific-thing>.md
   - Create the topic subdirectory if it does not exist
   - Format with: # Title, ## Key Points (concise bullets), ## Details (explanation with gotchas and "why"), ## Source (where this was learned)

5. **Update the knowledge index:**
   - Read $APHELOCOMA_HOME/core/knowledge/INDEX.md
   - Add a line for the new file under the appropriate topic heading
   - If the topic heading doesn't exist yet, create it
   - Format: `- **filename.md** — one-line description`

6. **Report what was captured** — show the file path and a one-line summary.

Prefer many small, focused knowledge files over one large file per topic.
