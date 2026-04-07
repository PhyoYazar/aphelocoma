#!/bin/bash
# Deploy aphelocoma context to Cursor rules in the current project.
# Usage: ./deploy.sh [project-dir]
#
# Generates .cursor/rules/ with:
#   - aphelocoma-context.mdc (identity + project context, always applied)
#   - aphelocoma-knowledge.mdc (knowledge index, always applied)

set -e

APHELOCOMA_HOME="${APHELOCOMA_HOME:-$HOME/.aphelocoma/data}"
PROJECT_DIR="${1:-.}"
RULES_DIR="$PROJECT_DIR/.cursor/rules"

# --- Detect project name from registry ---
detect_project() {
    local abs_dir
    abs_dir="$(cd "$PROJECT_DIR" && pwd)"

    if ! command -v python3 &>/dev/null; then
        echo "ERROR: python3 required for registry lookup" >&2
        exit 1
    fi

    python3 -c "
import json, os, sys
registry_path = os.path.expanduser('$APHELOCOMA_HOME/core/projects/registry.json')
if not os.path.exists(registry_path):
    sys.exit(1)
with open(registry_path) as f:
    registry = json.load(f)
target = '$abs_dir'
for name, config in registry.items():
    for path in config.get('paths', []):
        expanded = os.path.expanduser(path)
        if target.startswith(expanded) or expanded.startswith(target):
            print(name)
            sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

PROJECT_NAME=$(detect_project) || {
    echo "WARNING: Current directory not found in aphelocoma registry."
    echo "Run '/project-init' to register this project first."
    PROJECT_NAME=""
}

# --- Create rules directory ---
mkdir -p "$RULES_DIR"

# --- Generate aphelocoma-context.mdc ---
{
    echo "---"
    echo "description: Personal context and project info from aphelocoma second brain"
    echo "alwaysApply: true"
    echo "---"
    echo ""

    # Identity
    if [ -f "$APHELOCOMA_HOME/core/identity/profile.md" ]; then
        cat "$APHELOCOMA_HOME/core/identity/profile.md"
        echo ""
    fi

    if [ -f "$APHELOCOMA_HOME/core/identity/preferences.md" ]; then
        cat "$APHELOCOMA_HOME/core/identity/preferences.md"
        echo ""
    fi

    # Project context (concise — only overview, current state, and active tasks)
    if [ -n "$PROJECT_NAME" ]; then
        PROJECT_PATH="$APHELOCOMA_HOME/core/projects/$PROJECT_NAME"

        if [ -f "$PROJECT_PATH/context.md" ]; then
            echo "---"
            echo ""
            # Include only Overview, Tech Stack, Architecture, Current State (skip Open Questions)
            sed '/^## Open Questions/,$d' "$PROJECT_PATH/context.md"
            echo ""
        fi

        if [ -f "$PROJECT_PATH/tasks.md" ]; then
            # Include only In Progress and Planned sections, skip Done
            sed '/^## Done/,$d' "$PROJECT_PATH/tasks.md"
            echo ""
        fi
    fi
} > "$RULES_DIR/aphelocoma-context.mdc"

echo "Created $RULES_DIR/aphelocoma-context.mdc"

# --- Generate aphelocoma-knowledge.mdc ---
{
    echo "---"
    echo "description: Domain expertise from aphelocoma knowledge base"
    echo "alwaysApply: true"
    echo "---"
    echo ""

    if [ -f "$APHELOCOMA_HOME/core/knowledge/INDEX.md" ]; then
        cat "$APHELOCOMA_HOME/core/knowledge/INDEX.md"
        echo ""

        # Include actual knowledge file contents (they're small)
        find "$APHELOCOMA_HOME/core/knowledge" -name "*.md" ! -name "INDEX.md" -type f | sort | while read -r kfile; do
            echo "---"
            echo ""
            cat "$kfile"
            echo ""
        done
    fi
} > "$RULES_DIR/aphelocoma-knowledge.mdc"

echo "Created $RULES_DIR/aphelocoma-knowledge.mdc"

echo ""
echo "Cursor deploy complete. ${PROJECT_NAME:+Project: $PROJECT_NAME}"
echo "Rules at: $RULES_DIR/"
