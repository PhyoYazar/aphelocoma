# Aphelocoma — Brainstorms

A living document for the future of aphelocoma. Organized by theme.

**Vision**: A universal personal context layer for ALL AI tools — not locked to any single tool or company. Every AI you talk to should know who you are, what you're working on, and what you know. If a tool disappears tomorrow, your context stays.

---

## 1. Multi-Tool Architecture

The core problem: AI tools come and go. If your context lives inside one tool (Claude Code's memory, Cursor's rules, ChatGPT's history), switching tools means starting from zero. Aphelocoma should be the single source of truth that feeds ALL tools.

### 1.1 Three-Layer Design

```
Layer 1: Core Content (universal, tool-agnostic)
  ├── identity/      — who you are, preferences
  ├── knowledge/     — what you know
  ├── projects/      — what you're working on
  ├── journal/       — what you've done
  └── skills/        — how AI should help you

Layer 2: Adapters (tool-specific delivery)
  ├── claude-code/   — generates ~/.claude/skills/, CLAUDE.md
  ├── cursor/        — generates .cursorrules, .cursor/
  ├── codex/         — generates codex-compatible config
  ├── copilot/       — generates copilot instructions
  └── web-ai/        — generates pasteable context summaries

Layer 3: Access APIs (future)
  └── mcp-server/    — typed tool calls for any MCP-compatible tool
```

### 1.2 Adapter Strategy for AI Coding Tools

Each coding tool has its own config format. Adapters read from Layer 1 and generate tool-native configs:

| Tool | Config format | What to generate |
|---|---|---|
| Claude Code | `~/.claude/skills/*/SKILL.md`, `CLAUDE.md` | Skills with frontmatter, `!`command`` injection |
| Cursor | `.cursorrules`, `.cursor/rules/*.mdc` | Rules files from skills + project context |
| Codex | `AGENTS.md`, codex config | Agent instructions from skills |
| Copilot | `.github/copilot-instructions.md` | Instructions from identity + project context |
| Windsurf | `.windsurfrules` | Rules from skills + conventions |
| Aider | `.aider.conf.yml`, conventions | Convention files from knowledge |

**Key principle**: Write content once in Layer 1. Each adapter generates the tool-specific format. Switching tools = running a different adapter, not rewriting content.

### 1.3 `/generate-view` Command (Context for Web AI)

For tools that can't read local files (Claude.ai, ChatGPT, Gemini):

Generate a single markdown document that summarizes everything:
- Who you are (from identity/profile.md)
- Active projects and their state
- Open threads and plans
- Relevant domain expertise

Paste into Claude.ai Project instructions, ChatGPT custom instructions, or any web AI.

**Variants**:
- `/generate-view full` — everything (for Claude.ai Projects)
- `/generate-view brief` — 1-page summary (for ChatGPT custom instructions with char limits)
- `/generate-view project <name>` — context for one project only

Regenerate weekly or when things change significantly.

### 1.4 What "Single Source of Truth" Means in Practice

When you switch from Claude Code to Cursor mid-project:
1. Run `/deploy cursor` in aphelocoma
2. Cursor now has your project context, conventions, and skills
3. No knowledge lost, no manual copying

When you open ChatGPT for a non-coding question:
1. Your ChatGPT custom instructions already have your profile from `/generate-view`
2. ChatGPT knows your background, current projects, expertise areas
3. Answers are contextualized to YOU, not generic

---

## 2. Universal Skills

### 2.1 Canonical Skill Format

Skills should be tool-agnostic at the content level:

```
skills/
  sync/
    skill.md             # Universal instructions (pure markdown)
    metadata.yaml        # Name, description, invocation type
    templates/           # Structured output formats
    examples/            # Reference outputs
    scripts/             # Executable helpers
```

`metadata.yaml` uses a tool-agnostic schema:
```yaml
name: sync
description: Sync current project with the second brain
type: manual           # manual | auto | background
arguments: none
```

The Claude Code adapter converts `type: manual` → `disable-model-invocation: true`, `type: background` → `user-invocable: false`, etc.

### 2.2 Claude Code-Specific Enhancements

These only exist in the Claude Code adapter layer, not in the canonical skill:
- `!`command`` dynamic context injection (pre-load registry.json, INDEX.md)
- `context: fork` for running in subagents
- `allowed-tools` restrictions
- `paths` glob patterns for auto-triggering
- `effort` level tuning
- `hooks` scoped to skill lifecycle

### 2.3 Skills to Create/Migrate

| Current | Migrate to | Type | Notes |
|---|---|---|---|
| dist/commands/sync.md | skills/sync/ | manual | Add gap-checking script |
| dist/commands/status.md | skills/status/ | manual | Add dashboard script |
| dist/commands/journal.md | skills/journal/ | manual | Add entry template file |
| dist/commands/adr.md | skills/adr/ | manual | Add ADR template + examples |
| dist/commands/capture.md | skills/capture/ | manual | |
| dist/commands/reflect.md | skills/reflect/ | manual | Could run as Explore subagent |
| dist/commands/project-init.md | skills/project-init/ | manual | Add project templates |
| dist/commands/review.md | skills/review/ | manual | |
| dist/commands/debug.md | skills/debug/ | manual | |
| dist/skills/project-context.md | skills/project-context/ | background | Pre-inject registry.json |
| dist/skills/knowledge-lookup.md | skills/knowledge-lookup/ | background | Pre-inject INDEX.md |
| dist/commands/fetch-news.md | skills/fetch-news/ | manual | |
| dist/commands/morning-briefing.md | skills/morning-briefing/ | manual | |
| (new) | skills/generate-view/ | manual | Context generator for web AI |
| (new) | skills/deploy/ | manual | Multi-tool deploy |

---

## 3. Identity Layer

### 3.1 What's Missing Today

Aphelocoma knows your PROJECTS and KNOWLEDGE but not WHO YOU ARE. When you open any AI tool, it doesn't know:
- Your role and expertise level
- Your communication preferences
- Your current priorities across all projects
- How you like AI to behave

### 3.2 Proposed Files

```
core/identity/
  profile.md         # Role, skills, expertise areas, current focus
  preferences.md     # AI behavior preferences (concise, plan-first, etc.)
```

These feed into every adapter:
- Claude Code: merged into CLAUDE.md
- Cursor: merged into .cursorrules
- Web AI: included in /generate-view output
- Every tool gets the same "who is this person" context

### 3.3 Example profile.md

```markdown
# Profile

## Role
Software developer focused on React/TypeScript frontends.

## Current Focus
- magick-workforce-fed-vdb: collaborative workspace platform (refactoring phase)
- aphelocoma: personal knowledge system (multi-tool architecture)

## Expertise
- React 19, TypeScript, TanStack ecosystem
- System design and architecture
- Claude Code extension system

## Working Style
- Plan before implementing — show approach and get approval first
- Propose changes one at a time, confirm before writing
- Concise responses, no unnecessary summaries
- High-level task tracking, not fine-grained steps
```

---

## 4. Directory Restructure

### 4.1 Current → Future

```
CURRENT                          FUTURE
├── knowledge/                   ├── core/
├── projects/                    │   ├── identity/    (NEW)
├── journal/                     │   ├── knowledge/
├── dist/                        │   ├── projects/
│   ├── commands/                │   ├── journal/
│   ├── skills/                  │   └── decisions/   (cross-project ADRs)
│   ├── agents/                  ├── skills/           (universal, tool-agnostic)
│   └── CLAUDE.md                ├── adapters/
└── brainstorms.md               │   ├── claude-code/
                                 │   ├── cursor/
                                 │   └── web-ai/
                                 ├── views/            (generated context docs)
                                 └── brainstorms.md
```

### 4.2 Migration Questions

- **Break all paths or keep backward compat?** Moving knowledge/ → core/knowledge/ breaks $APHELOCOMA_HOME/knowledge/. Symlinks? Or update all references?
- **When to migrate?** Do it alongside the skills migration, or separately?
- **What about `dist/`?** Becomes `adapters/claude-code/` output. The `dist/` name no longer makes sense when there are multiple targets.
- **What about `dist/agents/`?** Claude Code agents (architect, reviewer) — these are Claude Code-specific personas. They stay in the Claude Code adapter.

---

## 5. Data & Search

### 5.1 Knowledge Index Evolution

Current: `knowledge/INDEX.md` (flat, manual-ish)
Future options:
- **YAML frontmatter** on knowledge files: tags, created, last-verified, related-projects
- **SQLite index**: structured queries, rebuilt from markdown on demand (`/reindex`)
- **Vector embeddings**: semantic search across all content (ChromaDB, LanceDB)

### 5.2 Vector Database Consideration

**What to embed**: Knowledge files, ADRs, context.md, journal entries
**Trade-off**: Breaks ADR-0001 (no dependencies) — is semantic search worth the complexity?
**Hybrid approach**: Markdown stays source of truth. Vector index is a derived cache, rebuilt on demand. Git stays the database.
**When**: Only when knowledge/ exceeds ~50 files and keyword search becomes insufficient

### 5.3 Journal Compression

After 30-90 days, summarize old entries into monthly digests (`journal/YYYY-MM/summary.md`). Originals stay in git history. `/reflect` reads summaries for older periods.

---

## 6. Automation & Workflows

### 6.1 Cross-Project Features
- **Knowledge linking**: projects reference relevant knowledge/ files in context.md
- **Inter-project dependencies**: track when one project informs another
- **Global search** (`/search <query>`): across all context, tasks, journal, knowledge

### 6.2 Review & Health
- **Weekly review** (`/weekly`): summarize all projects' activity over 7 days
- **Project health check**: flag stale context, overdue tasks, inactive projects
- **Journal → knowledge pipeline**: auto-draft knowledge files from patterns across journal entries

### 6.3 Project Lifecycle
- `status:` field in context.md (active / paused / archived)
- `/project-archive <name>` command
- Archived projects skipped by project-context skill

### 6.4 Git Integration
- Post-commit hook: auto-append one-liner to today's journal (commit message + project name)
- Auto-deploy hook: run deploy on commit within aphelocoma repo

### 6.5 Command Composition
- Formal convention for skills calling other skills
- `/reflect` → calls `/capture` for selected items
- Prevents duplication of logic across skills

---

## 7. Resolved (Already Implemented)

Items from previous brainstorms that are now done:

- [x] YAML frontmatter on all core files — `aph migrate-frontmatter` command migrates existing files; new files get frontmatter from skills (ADR-0015)
- [x] Structured session records — `core/sessions/` with `/session-record` skill; journal becomes summary layer referencing sessions (ADR-0015)
- [x] `$APHELOCOMA_HOME` env var (ADR-0009)
- [x] `projects/registry.json` for path-based detection (ADR-0009)
- [x] `knowledge/INDEX.md` for fast lookup (ADR-0009)
- [x] Instruction deduplication — triggers only in dist/CLAUDE.md (ADR-0009)
- [x] `/status` dashboard command (ADR-0009)
- [x] `/sync` command for per-project sync
- [x] CLAUDE.local.md as personal project layer (ADR-0008)
- [x] Plan-approval task capture (ADR-0008)
- [x] Full auto-sync: tasks + context + ADRs (ADR-0007)
- [x] Cross-OS portability via $APHELOCOMA_HOME

---

## 8. Open Questions

Questions that need answers before building.

### Architecture
- **Break paths or backward compat?** Moving to core/ structure breaks all existing $APHELOCOMA_HOME paths. Symlinks, gradual migration, or big bang?
- **`local.md` vs `CLAUDE.local.md`?** Tool-agnostic name is cleaner, but CLAUDE.local.md is what Claude Code natively recognizes. Keep both? Adapter handles the naming?

### Content
- **ADR granularity**: Where's the line between an ADR and a context.md update?
- **Cross-project knowledge**: Shared patterns — live in knowledge/ or duplicated per project?
- **Tasks granularity**: High-level epics or fine-grained steps?

### Operations
- **Journal utility**: Are journal entries being read? Worth the habit?
- **Stale detection**: Flag context.md if 60+ days old?
- **Claude Code memory vs aphelocoma**: Boundary between `~/.claude/.../memory/` (conversation preferences) and aphelocoma knowledge/ (domain expertise)?

### Multi-Tool
- **Adapter maintenance burden**: How much work to maintain adapters for 5+ tools? Is it sustainable solo?
- **Config format drift**: AI tools change their config formats frequently. How to handle adapter breakage?
- **MCP server timeline**: When does the programmatic access layer become worth the runtime dependency?

---

## 9. Priority Roadmap

What to build next, in rough order:

### Phase 1: Foundation (current stage → next)
- [ ] Migrate to universal skills format (skills/ with metadata.yaml)
- [ ] Create identity layer (profile.md, preferences.md)
- [ ] `/generate-view` command for web AI context
- [ ] Claude Code adapter (generates ~/.claude/ from skills/)

### Phase 2: Multi-Tool
- [ ] Cursor adapter
- [ ] Codex/Copilot adapter
- [ ] Directory restructure (core/, adapters/, views/)
- [ ] Project lifecycle (active/paused/archived)

### Phase 3: Intelligence
- [x] YAML frontmatter on all core files (expanded beyond knowledge files — all 38 files migrated)
- [x] Structured session records — reasoning chains, key findings, decisions (new core/sessions/ layer)
- [ ] Weekly review command
- [ ] Journal compression
- [ ] Global search across all content

### Phase 4: Public Release & Distribution
- [ ] Separate tool from data (aphelocoma repo = tool, ~/.aphelocoma = data)
- [ ] Install script (curl | bash)
- [ ] `aph init` bootstraps ~/.aphelocoma/data/ with starter structure
- [ ] `aph update` pulls latest tool without touching data
- [ ] Semver + git tags for releases
- [ ] CHANGELOG.md in tool repo
- [ ] Homebrew tap (when tool stabilizes)
- [ ] Data migration system (when new versions add/change data structure)
- [ ] `aph doctor` to verify installation health

### Phase 5: Multi-Device Sync
- [ ] Private git repo as sync backend (push/pull from aph CLI)
- [ ] Optional encryption via git-crypt (data encrypted at rest in remote)
- [ ] Syncthing as alternative (peer-to-peer, no cloud)
- [ ] iCloud/Dropbox + Cryptomator as alternative
- [ ] `aph sync` / `aph sync pull` commands
- [ ] Conflict resolution strategy for markdown files

### Phase 6: Security & Privacy
- [ ] No database — data stays as files on your machine
- [ ] git-crypt for encrypted remote storage
- [ ] Key management: keys live only on your devices
- [ ] Identity/profile.md encrypted in remote, plaintext locally
- [ ] Public tool repo contains zero user data

### Phase 7: Programmatic Access
- [ ] MCP server (typed tool calls for any MCP-compatible tool)
- [ ] Vector/semantic search (when knowledge > 50 files)
- [ ] REST API (for custom integrations)
