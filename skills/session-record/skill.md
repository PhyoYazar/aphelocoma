Capture a structured session record for the current work session.

APHELOCOMA_HOME = ~/.aphelocoma/data (override by setting $APHELOCOMA_HOME env var).

A session record captures the reasoning chains, key findings, and decisions that journal entries summarize but do not preserve in full. It is the primary artifact of a work session — the journal becomes a short summary that references it.

## Steps

1. **Identify the project:**
   - Read $APHELOCOMA_HOME/core/projects/registry.json
   - Match the current working directory to a registered project
   - If no match, use the working directory basename as project name and note it is unregistered

2. **Review the session:**
   - Run `git log --oneline --since="8 hours ago"` to see recent commits
   - Review what was discussed, decided, and discovered in this conversation
   - Identify the significant decisions (typically 3–7 per session — not every micro-choice)

3. **Generate metadata:**
   - **id**: `session-YYYY-MM-DD-HHMMSS` using current date and time
   - **slug**: 2–4 word kebab-case summary of the session goal (e.g., `kb-api-binding`, `session-records-design`)
   - **time_start**: estimate from the earliest relevant git commit today, or from when the major work started; ask the user if genuinely unclear
   - **time_end**: current time
   - **tags**: technologies, tools, and concepts mentioned (e.g., `[react-query, s3, api-binding]`)
   - **outcome**: `completed` (goal fully met), `partial` (some done, some deferred), `abandoned` (approach changed mid-session), or `exploration` (learning session, no deliverable)
   - **scope**: `feature`, `bugfix`, `refactor`, `exploration`, `design`, or `devops`

4. **Write the session record:**
   - Path: `$APHELOCOMA_HOME/core/sessions/YYYY-MM/YYYY-MM-DD-HHMMSS-<slug>.md`
   - Create the month directory if it does not exist
   - Use the template at `${CLAUDE_SKILL_DIR}/templates/record.md`
   - Fill all frontmatter fields
   - Write each body section:
     - **Goal**: one sentence — what the session was trying to achieve
     - **Context**: 2–3 sentences on the project state at session start and relevant preconditions
     - **Reasoning Chain**: one `###` subsection per significant decision. Each subsection has four fields: Question, Considered, Decision, Why. Focus on decisions where the reasoning matters — where a different choice would have led somewhere else.
     - **Key Findings**: discoveries with relevance beyond this session (tool quirks, API behaviors, patterns, surprises). These are candidates for `/capture` knowledge files.
     - **Outcome**: concrete deliverables (files written, endpoints bound, features shipped)
     - **Open Threads**: `- [ ]` items with enough context to be picked up cold by a future session

5. **Update the session index:**
   - Read `$APHELOCOMA_HOME/core/sessions/INDEX.md`
   - Add an entry under the current month heading: `- **filename.md** — one-line summary [project-name]`
   - Create the month heading (`## YYYY-MM`) if it does not exist
   - Update the `updated` field in the INDEX frontmatter to today's date

6. **Offer to update today's journal:**
   - Check if `$APHELOCOMA_HOME/core/journal/YYYY-MM/YYYY-MM-DD.md` exists
   - If it exists: offer to append a one-line summary referencing this session
   - If it does not exist: offer to create a journal entry as a concise summary of the session record
   - Journal summary format:
     ```
     ## HH:MM — [Project Name]
     <1–2 sentence summary of what was done>. See: session-YYYY-MM-DD-HHMMSS
     ```

## Rules

- Reasoning Chain entries should capture *why*, not *what*. "We used S3-then-JSON because the API schema expects FileAttachment objects, not FormData" is a good entry. "We wrote the upload function" is not.
- Key Findings should be things a future session (or a different project) could use. Project-specific implementation details belong in Outcome, not Key Findings.
- Open Threads should have enough context that you (or another AI) can pick them up without reading the full session. Include file names, error messages, or API paths where relevant.
- For exploration sessions with no deliverable, set `outcome: exploration` and focus the Reasoning Chain on what approaches were tried and what was learned from each.
- Multi-project sessions: use the primary project in the `project:` field, list secondary projects in `tags`.
