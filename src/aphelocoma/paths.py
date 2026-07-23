"""Runtime path resolution for the Hamilton-only Aphelocoma CLI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping, Optional, Tuple


def _absolute_path(value: str, home: Path) -> Path:
    if value == "~":
        path = home
    elif value.startswith("~/"):
        path = home / value[2:]
    else:
        path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    return Path(os.path.abspath(os.path.normpath(str(path))))


def _default_tool_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimePaths:
    """All CLI paths, including locations that must remain read-only."""

    root: Path
    tool_root: Path
    home: Path
    default_legacy_data: Path
    legacy_home_override: Optional[Path] = None

    @property
    def protected_legacy_paths(self) -> Tuple[Path, ...]:
        paths = [self.default_legacy_data]
        if (
            self.legacy_home_override is not None
            and self.legacy_home_override not in paths
        ):
            paths.append(self.legacy_home_override)
        return tuple(paths)

    def is_legacy_protected(self, candidate: Path) -> bool:
        """Return whether candidate is inside a protected legacy data path."""

        normalized = _absolute_path(str(candidate), self.home)
        for protected in self.protected_legacy_paths:
            try:
                normalized.relative_to(protected)
            except ValueError:
                continue
            return True
        return False


def resolve_paths(
    environ: Optional[Mapping[str, str]] = None,
    *,
    tool_root: Optional[Path] = None,
) -> RuntimePaths:
    """Resolve active and protected paths without creating or reading them."""

    env = os.environ if environ is None else environ
    home_value = env.get("HOME") or str(Path.home())
    home = _absolute_path(home_value, Path.home())

    root_value = env.get("APHELOCOMA_ROOT") or str(home / ".aphelocoma")
    root = _absolute_path(root_value, home)
    default_legacy = _absolute_path(str(home / ".aphelocoma" / "data"), home)

    legacy_value = env.get("APHELOCOMA_HOME")
    legacy_override = (
        _absolute_path(legacy_value, home) if legacy_value else None
    )
    resolved_tool_root = _absolute_path(
        str(tool_root if tool_root is not None else _default_tool_root()),
        home,
    )

    return RuntimePaths(
        root=root,
        tool_root=resolved_tool_root,
        home=home,
        default_legacy_data=default_legacy,
        legacy_home_override=legacy_override,
    )
