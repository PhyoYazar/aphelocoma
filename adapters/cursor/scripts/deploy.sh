#!/bin/bash
# Deploy aphelocoma skills and context to Cursor rules in the current project.
# Usage: ./deploy.sh [project-dir]
#
# Generates .cursor/rules/ with:
#   - aphelocoma-<skill-name>.mdc per skill (type-based alwaysApply)
#   - aphelocoma-context.mdc (identity + project context, always applied)
#   - aphelocoma-knowledge.mdc (knowledge index, always applied)

set -e

APHELOCOMA_HOME="${APHELOCOMA_HOME:-$HOME/.aphelocoma/data}"
APHELOCOMA_TOOL="${APHELOCOMA_TOOL:-$HOME/.aphelocoma/tool}"
PROJECT_DIR="${1:-.}"
RULES_DIR="$PROJECT_DIR/.cursor/rules"

# Colors
BOLD='\033[1m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

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
    echo -e "${YELLOW}WARNING: Current directory not found in aphelocoma registry.${RESET}"
    echo "Run 'aph add' to register this project first."
    PROJECT_NAME=""
}

# --- Create rules directory ---
mkdir -p "$RULES_DIR"

# --- Read a YAML field (simple single-line values only) ---
yaml_field() {
    local file="$1" field="$2"
    grep "^${field}:" "$file" 2>/dev/null | sed "s/^${field}:[[:space:]]*//"
}

# --- List all skills (data overrides tool) ---
list_all_skills() {
    local overridden=""
    if [ -d "$APHELOCOMA_HOME/skills" ]; then
        for d in "$APHELOCOMA_HOME"/skills/*/; do
            [ -d "$d" ] || continue
            local name=$(basename "$d")
            overridden="$overridden|$name|"
            echo "$d"
        done
    fi
    for d in "$APHELOCOMA_TOOL"/skills/*/; do
        [ -d "$d" ] || continue
        local name=$(basename "$d")
        echo "$overridden" | grep -q "|$name|" && continue
        echo "$d"
    done
}

# --- Generate per-skill .mdc files ---
skill_count=0

while IFS= read -r skill_dir; do
    skill_name=$(basename "$skill_dir")
    metadata="$skill_dir/metadata.yaml"
    skill_file="$skill_dir/skill.md"

    [ -f "$metadata" ] || continue
    [ -f "$skill_file" ] || continue

    # Read metadata
    description=$(yaml_field "$metadata" "description")
    skill_type=$(yaml_field "$metadata" "type")

    # Determine alwaysApply from type
    if [ "$skill_type" = "background" ]; then
        always_apply="true"
    else
        always_apply="false"
    fi

    # Check for cursor-specific overrides
    override_file="$APHELOCOMA_TOOL/adapters/cursor/overrides/${skill_name}.yaml"
    if [ -f "$override_file" ]; then
        override_always=$(yaml_field "$override_file" "alwaysApply")
        override_desc=$(yaml_field "$override_file" "description")
        override_globs=$(yaml_field "$override_file" "globs")
        override_skip=$(yaml_field "$override_file" "skip")

        [ "$override_skip" = "true" ] && continue
        [ -n "$override_always" ] && always_apply="$override_always"
        [ -n "$override_desc" ] && description="$override_desc"
    fi

    # Generate .mdc file
    output="$RULES_DIR/aphelocoma-${skill_name}.mdc"
    {
        echo "---"
        echo "description: \"$description\""
        echo "alwaysApply: $always_apply"
        [ -n "$override_globs" ] && echo "globs: $override_globs"
        echo "---"
        echo ""
        cat "$skill_file"

        # Inline templates if they exist
        if [ -d "$skill_dir/templates" ]; then
            echo ""
            echo "## Templates"
            echo ""
            for tpl in "$skill_dir"/templates/*.md; do
                [ -f "$tpl" ] || continue
                echo "### $(basename "$tpl" .md)"
                echo ""
                cat "$tpl"
                echo ""
            done
        fi
    } > "$output"

    skill_count=$((skill_count + 1))
done < <(list_all_skills)

echo -e "${GREEN}Deployed${RESET} $skill_count skills to $RULES_DIR/"

# --- Generate aphelocoma-context.mdc (identity + project data) ---
{
    echo "---"
    echo "description: \"Personal context and project info from aphelocoma second brain\""
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

    # Project context
    if [ -n "$PROJECT_NAME" ]; then
        PROJECT_PATH="$APHELOCOMA_HOME/core/projects/$PROJECT_NAME"

        if [ -f "$PROJECT_PATH/context.md" ]; then
            echo "---"
            echo ""
            sed '/^## Open Questions/,$d' "$PROJECT_PATH/context.md"
            echo ""
        fi

        if [ -f "$PROJECT_PATH/tasks.md" ]; then
            sed '/^## Done/,$d' "$PROJECT_PATH/tasks.md"
            echo ""
        fi
    fi
} > "$RULES_DIR/aphelocoma-context.mdc"

echo -e "${GREEN}Deployed${RESET} aphelocoma-context.mdc"

# --- Generate aphelocoma-knowledge.mdc ---
{
    echo "---"
    echo "description: \"Domain expertise from aphelocoma knowledge base\""
    echo "alwaysApply: true"
    echo "---"
    echo ""

    if [ -f "$APHELOCOMA_HOME/core/knowledge/INDEX.md" ]; then
        cat "$APHELOCOMA_HOME/core/knowledge/INDEX.md"
        echo ""

        find "$APHELOCOMA_HOME/core/knowledge" -name "*.md" ! -name "INDEX.md" -type f | sort | while read -r kfile; do
            echo "---"
            echo ""
            cat "$kfile"
            echo ""
        done
    fi
} > "$RULES_DIR/aphelocoma-knowledge.mdc"

echo -e "${GREEN}Deployed${RESET} aphelocoma-knowledge.mdc"

echo ""
echo -e "${BOLD}Cursor deploy complete.${RESET} ${PROJECT_NAME:+Project: $PROJECT_NAME}"
echo "Rules at: $RULES_DIR/"
