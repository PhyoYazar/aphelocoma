# Aphelocoma

A universal personal context layer for AI tools.

Named after the [scrub-jay genus](https://en.wikipedia.org/wiki/Aphelocoma) — birds with remarkable episodic memory (they remember what they cached, where, and when).

---

## Why?

AI tools don't share context. Claude Code doesn't know what you told Cursor. ChatGPT doesn't know your project architecture. Every tool starts from zero.

Aphelocoma is your **single source of truth** — who you are, what you're working on, what you know — delivered to any AI tool.

**No vendor lock-in.** If any AI tool disappears tomorrow, your context stays.

---

## Quick Start

### 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/v0.0.2-alpha/install.sh | bash
```

This installs the tool to `~/.aphelocoma/tool/`, adds `aph` to your PATH, and runs first-time setup automatically.

### 2. Setup

```bash
aph setup
```

This creates your private data directory at `~/.aphelocoma/data/` with:
- `core/identity/profile.md` — edit this with your role and expertise
- `core/identity/preferences.md` — how you want AI to behave
- `core/knowledge/` — your domain expertise (grows over time)
- `core/projects/` — your project records
- `core/journal/` — your work session logs

### 3. Edit your profile

```bash
# Use any editor
nano ~/.aphelocoma/data/core/identity/profile.md
```

### 4. Add a project

```bash
cd ~/your-project
aph add
```

### 5. Deploy to your AI tool

```bash
# For Claude Code
aph deploy claude

# For Codex
aph deploy codex

# For Cursor (run inside a project directory)
cd ~/your-project
aph deploy cursor
```

### 6. Start working

Open your AI tool in the project. It now knows who you are, what you're working on, and your preferences.

In Claude Code or Codex, use `/sync` to keep aphelocoma updated as you work. Context syncs automatically via background skills (`auto-sync`, `session-end`).

---

## How It Works

```
~/.aphelocoma/
├── tool/              ← this repo (public, installable)
│   ├── bin/aph        # CLI
│   ├── skills/        # 13 built-in skills
│   └── adapters/      # Claude Code, Codex, Cursor generators
│
└── data/              ← your private data (never shared)
    └── core/
        ├── identity/  # who you are
        ├── knowledge/ # what you know
        ├── projects/  # what you're working on
        └── journal/   # what you've done
```

**The learning loop:**
```
Work on a project
  → /journal captures the session
  → /reflect proposes what's worth keeping
  → /capture distills insights into knowledge
  → Next session: AI knows your full context
```

---

## CLI Reference

```bash
aph setup                    # First-time setup
aph add [path]               # Add a project (default: current dir)
aph deploy claude            # Deploy to Claude Code
aph deploy codex             # Deploy to Codex
aph deploy cursor            # Deploy to Cursor (in project dir)
aph sync [path]              # Sync project context from git history
aph update                   # Update tool (data untouched)
aph status                   # Dashboard of your second brain
aph view full                # Generate context for web AI (Claude.ai, ChatGPT)
aph view brief               # Short version
aph projects                 # List registered projects
aph skills                   # List all skills
```

---

## Multi-Tool Support

| Tool | Command | What it does |
|------|---------|-------------|
| **Claude Code** | `aph deploy claude` | Deploys skills to `~/.claude/skills/`, CLAUDE.md, and agents |
| **Codex** | `aph deploy codex` | Deploys skills to `~/.codex/skills/`, AGENTS.md, and hooks |
| **Cursor** | `aph deploy cursor` | Generates `.cursor/rules/*.mdc` with your context |
| **Web AI** | `aph view full` | Generates a pasteable context summary for Claude.ai, ChatGPT, Gemini |

---

## Skills (in AI tools)

These skills are available inside AI tools after deploying:

| Skill | What it does |
|-------|-------------|
| `/sync` | Sync current project with aphelocoma |
| `/aph-status` | Dashboard of projects, knowledge, journal |
| `/journal` | Capture end-of-session work entry |
| `/reflect` | Propose knowledge captures from recent work |
| `/capture [topic]` | Distill insights into knowledge files |
| `/project-init <name>` | Bootstrap a new project record (alternative to `aph add`) |
| `/adr <project> <title>` | Create an Architecture Decision Record |
| `/deploy [tool]` | Deploy from inside an AI tool |
| `/generate-view [type]` | Generate context summary for web AI |

---

## Custom Skills

Create your own skills in `~/.aphelocoma/data/skills/`:

```
~/.aphelocoma/data/skills/my-skill/
├── skill.md           # Instructions
└── metadata.yaml      # name, description, type
```

Custom skills with the same name as a built-in skill will override it.

---

## Update

```bash
aph update
```

Updates the tool only. Your data is never touched.

---

## Uninstall

```bash
aph uninstall
# Your data at ~/.aphelocoma/data/ is preserved unless you delete it
```
