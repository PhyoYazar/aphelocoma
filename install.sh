#!/bin/bash
# Transactional Aphelocoma installer for macOS and GNU/Linux.

set -eu

APHELOCOMA_INSTALL_ROOT="${APHELOCOMA_ROOT:-$HOME/.aphelocoma}"
APHELOCOMA_REPOSITORY_URL="${APHELOCOMA_REPOSITORY:-https://github.com/PhyoYazar/aphelocoma.git}"
APHELOCOMA_INSTALL_WORK=""

cleanup() {
    if [ -n "$APHELOCOMA_INSTALL_WORK" ] && [ -d "$APHELOCOMA_INSTALL_WORK" ]; then
        rm -rf "$APHELOCOMA_INSTALL_WORK"
    fi
}
trap cleanup EXIT HUP INT TERM

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3.9 or newer is required." >&2
    exit 1
fi

if [ -n "${APHELOCOMA_INSTALL_SOURCE:-}" ]; then
    if [ ! -d "$APHELOCOMA_INSTALL_SOURCE" ]; then
        echo "Error: APHELOCOMA_INSTALL_SOURCE is not a directory: $APHELOCOMA_INSTALL_SOURCE" >&2
        exit 1
    fi
    APHELOCOMA_RELEASE_SOURCE="$APHELOCOMA_INSTALL_SOURCE"
else
    if ! command -v git >/dev/null 2>&1; then
        echo "Error: Git is required to download Aphelocoma." >&2
        exit 1
    fi
    APHELOCOMA_INSTALL_WORK="$(mktemp -d "${TMPDIR:-/tmp}/aphelocoma-install.XXXXXX")"
    APHELOCOMA_RELEASE_SOURCE="$APHELOCOMA_INSTALL_WORK/source"
    if ! git clone --depth 1 "$APHELOCOMA_REPOSITORY_URL" "$APHELOCOMA_RELEASE_SOURCE"; then
        echo "Error: download failed; the existing installation was not changed." >&2
        exit 1
    fi
fi

APHELOCOMA_SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    APHELOCOMA_SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    APHELOCOMA_SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    APHELOCOMA_SHELL_RC="$HOME/.bash_profile"
fi

APHELOCOMA_ROOT="$APHELOCOMA_INSTALL_ROOT" \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$APHELOCOMA_RELEASE_SOURCE/src" \
python3 - "$APHELOCOMA_RELEASE_SOURCE" "$APHELOCOMA_SHELL_RC" <<'PY'
import os
from pathlib import Path
import sys

from aphelocoma.lifecycle import (
    LifecycleError,
    activate_release,
)
from aphelocoma.paths import resolve_paths


source = Path(sys.argv[1])
shell_rc = Path(sys.argv[2]) if sys.argv[2] else None
paths = resolve_paths()
try:
    result = activate_release(
        source,
        paths,
        fail_at=os.environ.get("APHELOCOMA_FAIL_AT"),
        shell_rc=shell_rc,
    )
except LifecycleError as error:
    print(f"Error: {error}", file=sys.stderr)
    raise SystemExit(1)
for message in result.messages:
    print(message)
if shell_rc is None:
    print("Add %s to PATH manually." % (paths.root / "tool" / "bin"))
PY

echo "Installation complete."
echo "Next: aph deploy claude  # or: aph deploy codex"
