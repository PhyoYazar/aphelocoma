Generate a git commit message and commit the staged/unstaged changes.

## Steps

1. Run `git status` to see all changes (untracked, staged, unstaged).
2. Run `git diff` and `git diff --cached` to see the actual code changes.
3. If there are no changes at all, tell the user and stop.
4. Stage all relevant changed files (use specific file names, not `git add -A`). Do NOT stage files that contain secrets (.env, credentials, etc).
5. Write a concise commit message that describes what was implemented or changed. Focus on the "what" and "why". Use imperative mood (e.g. "Add feature X", "Fix bug in Y", "Refactor Z").
6. Commit with that message. Do NOT append any co-author lines or attribution.
7. Show the user the commit hash and message when done.

## Commit message format

- First line: short summary under 72 characters
- If more detail is needed, add a blank line then bullet points describing key changes
- No co-author tags, no signatures, no metadata footers
