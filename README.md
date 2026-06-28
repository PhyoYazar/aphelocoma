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
curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/v0.1.1/install.sh | bash
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
│   ├── skills/        # 18 built-in skills
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

## Hamilton — an AI crew that builds your project

*New in v0.1.0.* Hamilton turns any coding agent into a small software org — CTO, architect, developers, QA, DevOps — that **brainstorms → plans → builds** software for a project, logging who-did-what to a file ledger. It's portable (just markdown + a written protocol, no dependencies), and **you stay in control** as the advisor.

It ships as a skill, so `aph deploy claude` / `aph deploy codex` installs it with the rest.

### Use it

Run it inside the project you want to build in (new or existing code):

```bash
/aph-hamilton                                          # guided start — it asks what to build
/aph-hamilton start "build a furniture store" startup  # fast path if you know the brief
/aph-hamilton resume                                   # continue where you left off
/aph-hamilton status                                   # phase + open tasks (read-only)
```

You're the **advisor**: the crew pauses at **4 checkpoints** for your call — direction + crew size, the plan, the build style, and review — and works on its own in between. Before checkpoints 1, 2, and 4 — and on **every task before it's marked done** — an independent reviewer (never the builder) double-checks the work and records its verdict to the ledger.

**Crew sizes** (chosen with you after Discovery): `solo` · `startup` · `mid` · `big` · `custom:[role,…]`.

Everything Hamilton tracks lives in your project under `.aphelocoma/` — the task board, the append-only history ledger, and one spec per task. The software itself is built at the project root.

### Parallel builds + per-role tuning (Claude Code)

`aph deploy claude` generates the **crew agents** (`~/.claude/agents/hamilton-<role>`), so on Claude Code the crew builds **in parallel by default** — independent tasks run at once, with the manager as the **single writer** of the board + ledger so concurrent work never corrupts history. The fleet view shows real role names (`hamilton-fullstack-developer`, …), and each role carries its own model, effort, and tool scope. Sequential is the automatic fallback and the only mode on other tools — parallel is the default where available, never required.

Defaults: the crew follows your **session model** (so it always uses your best, and upgrades itself when a better model ships); the technical-writer uses `sonnet`. Override per project in `.aphelocoma/settings.yaml`:
- **model** — map a role to a model (cheap ↔ smart); unlisted roles follow your session.
- **effort** — map a role to a reasoning level (`low`…`max`); unlisted roles follow your `/effort`.
- the reviewer runs **look-only** (no edit tools) by design.

Changed a project's models/effort? Re-run `/aph-hamilton sync-agents`, then **restart the session** so the new crew loads (Claude Code loads agents at startup). `/aph-hamilton status` prints the role → model → effort → tools table.

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
| `/aph-hamilton` | Spin up an AI crew (CTO, devs, QA…) that builds software for a project — see **Hamilton** above |
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
