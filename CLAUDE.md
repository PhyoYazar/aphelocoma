# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## What is Aphelocoma?

A universal personal context layer for AI tools. Named after the scrub-jay genus — birds famous for episodic memory (they remember what they cached, where, and when).

Everything is markdown and YAML. No build step, no runtime, no dependencies. Git is the database. Works with any AI tool via adapters.

## Structure

- `core/` — Universal content (tool-agnostic)
  - `core/identity/` — Profile, preferences (who you are)
  - `core/knowledge/` — Domain expertise with INDEX.md for fast lookup
  - `core/projects/` — Per-project records (context.md, tasks.md, adrs/, local.md), with registry.json for path mapping
  - `core/journal/` — Work session logs (YYYY-MM/YYYY-MM-DD.md), short summaries referencing sessions
  - `core/sessions/` — Structured session records with reasoning chains (YYYY-MM/YYYY-MM-DD-HHMMSS-slug.md)
- `skills/` — Universal skills in folder format (skill.md + metadata.yaml + templates)
- `adapters/` — Tool-specific delivery
  - `adapters/claude-code/` — Claude Code config generation (agents, overrides, CLAUDE.md template)
  - `adapters/codex/` — Codex config generation (AGENTS.md template, overrides, hooks)
  - `adapters/cursor/` — Cursor .mdc rule generation
- `views/` — Generated context summaries for web AI (gitignored)
- `.claude/commands/` — Commands for working on aphelocoma itself

## Conventions

- All core files use YAML frontmatter (`---` block) with `type`, `date`/`updated`, and relevant metadata fields.
- Knowledge files: markdown with `# Title` and concise sections.
- Journal entries: `core/journal/YYYY-MM/YYYY-MM-DD.md`. Append, don't overwrite. Short summaries when session records exist.
- Session records: `core/sessions/YYYY-MM/YYYY-MM-DD-HHMMSS-<slug>.md`. Primary capture artifact — preserves reasoning chains.
- Project records: context.md, tasks.md, adrs/, local.md (personal notes snapshot).
- ADRs: `NNNN-kebab-case-title.md` with Status, Context, Decision, Consequences.
- Tasks: checkbox format `- [ ]` / `- [x]`, grouped under In Progress / Planned / Done.
- Skills: folder format with `skill.md` (instructions) + `metadata.yaml` (name, description, type).
- All paths use `$APHELOCOMA_HOME` (default: `~/.aphelocoma/data`).

## Skills (15)

| Skill | Type | Purpose |
|-------|------|---------|
| `project-context` | background | Loads project context on session start |
| `knowledge-lookup` | background | Surfaces relevant knowledge silently |
| `auto-sync` | background | Proactively syncs tasks, context, ADRs as you work |
| `session-end` | background | Offers session record or journal when session wraps up |
| `ux-guardian` | background | UX nudges during frontend work, full codebase UX audits on demand |
| `sync` | manual | Sync current project with aphelocoma |
| `status` | manual | Dashboard of projects, knowledge, journal, sessions |
| `journal` | manual | Capture end-of-session work entry (summary layer) |
| `session-record` | manual | Capture structured session record with reasoning chains |
| `adr` | manual | Create Architecture Decision Record |
| `capture` | manual | Distill insights into knowledge files |
| `reflect` | manual | Propose knowledge captures from recent work |
| `project-init` | manual | Bootstrap a new project record |
| `deploy` | manual | Deploy to AI tool configs (Claude Code, Codex, Cursor) |
| `generate-view` | manual | Context summary for web AI (Claude.ai, ChatGPT) |

## Working in this repo

After modifying `skills/`, `adapters/`, `core/`, or root files, proactively offer to:
- Create an ADR in `core/projects/aphelocoma/adrs/`
- Update `core/projects/aphelocoma/tasks.md`

## Deploy

Run `/deploy` or `/deploy claude` inside this repo to generate Claude Code configs at `~/.claude/`.
Run `/deploy codex` to generate Codex configs at `~/.codex/`.
Run `/deploy cursor` to generate Cursor rules in the current project.
