"""Base installation diagnostics and extension registry."""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import platform
from pathlib import Path
import re
import shutil
import sys
from typing import Callable, Dict, List, Optional, Tuple

from .paths import RuntimePaths


SUPPORTED_OS = ("Darwin", "Linux")
MINIMUM_PYTHON = (3, 9)
VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9][A-Za-z0-9.-]*)?$"
)
DEFINITION_ROOT_FILES = (
    "skills/aph-hamilton/skill.md",
    "skills/aph-hamilton/metadata.yaml",
)
DEFINITION_REFERENCE_FILES = (
    "ABOUT.md",
    "CRAFT.md",
    "CRITIQUE.md",
    "DISPATCH-CODEX.md",
    "FOUNDATIONS.md",
    "PARALLEL.md",
    "PROTOCOL.md",
    "START.reference.md",
    "agent-template.md",
    "migrate.py",
    "result.implementer.schema.json",
    "result.reviewer.schema.json",
    "roles.index.md",
    "settings.default.yaml",
    "settings.example.yaml",
    "sizes.yaml",
    "state.schema.json",
    "validate.py",
)
HAMILTON_ROLE_IDS = (
    "appsec-engineer",
    "automation-test-engineer",
    "backend-developer",
    "backend-lead",
    "business-analyst",
    "ceo",
    "cloud-engineer",
    "cto",
    "data-engineer",
    "data-scientist",
    "dba",
    "devops-engineer",
    "engineering-manager",
    "frontend-developer",
    "frontend-lead",
    "fullstack-developer",
    "ml-engineer",
    "mobile-developer",
    "product-manager",
    "qa-engineer",
    "security-engineer",
    "software-architect",
    "sre",
    "tech-support-engineer",
    "technical-writer",
    "uiux-designer",
    "vp-engineering",
)
DEFINITION_FILES = (
    DEFINITION_ROOT_FILES
    + tuple(
        f"skills/aph-hamilton/references/{name}"
        for name in DEFINITION_REFERENCE_FILES
    )
    + tuple(
        f"skills/aph-hamilton/references/roles/{role_id}.md"
        for role_id in HAMILTON_ROLE_IDS
    )
)
EXTENSION_MODULES = ("aphelocoma.hamilton_state",)


@dataclass(frozen=True)
class Diagnostic:
    id: str
    status: str
    message: str
    remediation: Optional[str]

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class DoctorContext:
    paths: RuntimePaths
    cwd: Path = field(default_factory=Path.cwd)


@dataclass(frozen=True)
class DoctorReport:
    checks: Tuple[Diagnostic, ...]

    @property
    def healthy(self) -> bool:
        return all(check.status == "ok" for check in self.checks)

    @property
    def exit_code(self) -> int:
        return 0 if self.healthy else 1

    def as_dict(self) -> Dict[str, object]:
        return {
            "schema_version": 1,
            "status": "healthy" if self.healthy else "action_required",
            "checks": [check.as_dict() for check in self.checks],
        }


Check = Callable[[DoctorContext], Diagnostic]


class CheckRegistry:
    """Ordered registry that later milestones can extend without CLI changes."""

    def __init__(self) -> None:
        self._checks: List[Tuple[str, Check]] = []

    def register(self, check_id: str, callback: Check) -> None:
        if check_id in self.ids():
            raise ValueError(f"doctor check id already registered: {check_id}")
        self._checks.append((check_id, callback))

    def ids(self) -> Tuple[str, ...]:
        return tuple(check_id for check_id, _ in self._checks)

    def callbacks(self) -> Tuple[Tuple[str, Check], ...]:
        return tuple(self._checks)


def _python_check(context: DoctorContext) -> Diagnostic:
    del context
    version = sys.version_info[:3]
    formatted = ".".join(str(component) for component in version)
    if version >= MINIMUM_PYTHON:
        return Diagnostic(
            "python",
            "ok",
            f"Python {formatted} is supported.",
            None,
        )
    return Diagnostic(
        "python",
        "error",
        f"Python {formatted} is unsupported; Python 3.9+ is required.",
        "Install Python 3.9 or newer and run aph doctor again.",
    )


def _git_check(context: DoctorContext) -> Diagnostic:
    del context
    executable = shutil.which("git")
    if executable:
        return Diagnostic("git", "ok", f"Git is available at {executable}.", None)
    return Diagnostic(
        "git",
        "error",
        "Git was not found on PATH.",
        "Install Git, ensure it is on PATH, and run aph doctor again.",
    )


def _os_check(context: DoctorContext) -> Diagnostic:
    del context
    current = platform.system() or "unknown"
    if current in SUPPORTED_OS:
        return Diagnostic("os", "ok", f"{current} is supported.", None)
    return Diagnostic(
        "os",
        "error",
        f"{current} is unsupported; macOS and Linux are supported.",
        "Run Aphelocoma on macOS or Linux.",
    )


def _version_check(context: DoctorContext) -> Diagnostic:
    version_file = context.paths.tool_root / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        return Diagnostic(
            "aphelocoma_version",
            "error",
            f"Aphelocoma version file is unreadable: {version_file} ({error}).",
            "Reinstall Aphelocoma to restore the VERSION file.",
        )
    if not VERSION_PATTERN.fullmatch(version):
        return Diagnostic(
            "aphelocoma_version",
            "error",
            f"Aphelocoma version is invalid in {version_file}.",
            "Reinstall Aphelocoma to restore a valid VERSION file.",
        )
    return Diagnostic(
        "aphelocoma_version",
        "ok",
        f"Aphelocoma version {version} is installed.",
        None,
    )


def _definition_check(context: DoctorContext) -> Diagnostic:
    missing = [
        relative
        for relative in DEFINITION_FILES
        if not (context.paths.tool_root / relative).is_file()
    ]
    if missing:
        return Diagnostic(
            "hamilton_definition",
            "error",
            "Hamilton definition is incomplete; missing: " + ", ".join(missing) + ".",
            "Reinstall Aphelocoma to restore the Hamilton definition.",
        )
    return Diagnostic(
        "hamilton_definition",
        "ok",
        "Hamilton definition is complete.",
        None,
    )


def base_registry() -> CheckRegistry:
    registry = CheckRegistry()
    registry.register("python", _python_check)
    registry.register("git", _git_check)
    registry.register("os", _os_check)
    registry.register("aphelocoma_version", _version_check)
    registry.register("hamilton_definition", _definition_check)
    return registry


def default_registry() -> CheckRegistry:
    """Build the base registry and load optional in-package doctor extensions."""

    registry = base_registry()
    for module_name in EXTENSION_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:
                continue
            raise
        register = getattr(module, "register_doctor_checks", None)
        if register is not None:
            register(registry)
    return registry


def run_checks(context: DoctorContext, registry: CheckRegistry) -> DoctorReport:
    diagnostics = []
    for expected_id, callback in registry.callbacks():
        diagnostic = callback(context)
        if diagnostic.id != expected_id:
            raise ValueError(
                f"doctor check {expected_id!r} returned id {diagnostic.id!r}"
            )
        if diagnostic.status not in ("ok", "error"):
            raise ValueError(
                f"doctor check {expected_id!r} returned invalid status "
                f"{diagnostic.status!r}"
            )
        diagnostics.append(diagnostic)
    return DoctorReport(tuple(diagnostics))
