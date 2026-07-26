"""Small, dependency-free file helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Optional


def atomic_write_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: Optional[int] = None,
) -> None:
    """Write text through a sibling temporary file and atomic replacement."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = None
    try:
        existing_mode = stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        pass

    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        selected_mode = mode if mode is not None else existing_mode
        if selected_mode is not None:
            os.fchmod(descriptor, selected_mode)
        with os.fdopen(descriptor, "w", encoding=encoding, newline="") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(target))
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path: Path, value: Any, *, mode: Optional[int] = None) -> None:
    """Serialize deterministic JSON and replace path atomically."""

    content = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    atomic_write_text(path, content + "\n", mode=mode)


def read_json(path: Path) -> Any:
    """Read UTF-8 JSON from path."""

    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)
