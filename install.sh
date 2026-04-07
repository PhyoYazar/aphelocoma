#!/bin/bash
# Aphelocoma installer
# Usage: curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/main/install.sh | bash

set -e

APHELOCOMA_ROOT="$HOME/.aphelocoma"
TOOL_DIR="$APHELOCOMA_ROOT/tool"
DATA_DIR="$APHELOCOMA_ROOT/data"
REPO_URL="https://github.com/PhyoYazar/aphelocoma.git"

# Colors
BOLD='\033[1m'
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
RED='\033[31m'
RESET='\033[0m'

echo -e "${BOLD}Aphelocoma Installer${RESET}"
echo ""

# --- Check dependencies ---
if ! command -v git &>/dev/null; then
    echo -e "${RED}Error: git is required but not installed.${RESET}"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo -e "${YELLOW}Warning: python3 not found. Some features (status, view) require it.${RESET}"
fi

# --- Install or update tool ---
mkdir -p "$APHELOCOMA_ROOT"

if [ -d "$TOOL_DIR" ]; then
    echo -e "${CYAN}Updating tool...${RESET}"
    cd "$TOOL_DIR"
    git pull --ff-only 2>/dev/null || {
        echo -e "${RED}Error: git pull failed. Try: rm -rf $TOOL_DIR && re-run installer.${RESET}"
        exit 1
    }
    echo -e "${GREEN}Tool updated.${RESET}"
else
    echo -e "${CYAN}Cloning aphelocoma...${RESET}"
    git clone "$REPO_URL" "$TOOL_DIR"
    echo -e "${GREEN}Tool installed at $TOOL_DIR${RESET}"
fi

# --- Make aph executable ---
chmod +x "$TOOL_DIR/bin/aph"

# --- Add to PATH ---
SHELL_RC=""
if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

PATH_LINE='export PATH="$HOME/.aphelocoma/tool/bin:$PATH"'

if [ -n "$SHELL_RC" ]; then
    if ! grep -q '.aphelocoma/tool/bin' "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Aphelocoma" >> "$SHELL_RC"
        echo "$PATH_LINE" >> "$SHELL_RC"
        echo -e "${GREEN}Added to PATH in $SHELL_RC${RESET}"
    else
        echo -e "${DIM}PATH already configured in $SHELL_RC${RESET}"
    fi
else
    echo -e "${YELLOW}Could not detect shell config file. Add manually:${RESET}"
    echo "  $PATH_LINE"
fi

# --- Make aph available in current session ---
export PATH="$TOOL_DIR/bin:$PATH"

# --- Init data if needed ---
if [ -d "$DATA_DIR/core" ]; then
    echo ""
    echo -e "${GREEN}Existing data found at $DATA_DIR — preserved.${RESET}"
else
    echo ""
    "$TOOL_DIR/bin/aph" setup
fi

echo ""
echo -e "${BOLD}Installation complete!${RESET}"
echo ""
echo "Commands:"
echo "  aph help              Show all commands"
echo "  aph status            Dashboard of your second brain"
echo "  aph deploy claude     Deploy skills to Claude Code"
echo "  aph deploy cursor     Deploy rules to Cursor (in a project dir)"
echo ""
echo -e "${DIM}Restart your terminal or run: source $SHELL_RC${RESET}"
