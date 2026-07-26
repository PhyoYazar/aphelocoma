"""Versioned Hamilton project-state validation, migration, and doctor checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
import uuid

from .io import atomic_write_json, atomic_write_text


CURRENT_SCHEMA_VERSION = 1
CURRENT_PROTOCOL_VERSION = "1.0.0"
STATUS_REPORT_SCHEMA_VERSION = 1
LEGACY_HISTORY_SOURCE = "unversioned-v0.2"
VISIBILITIES = {"tracked", "local"}
STATUSES = {
    "pending",
    "assigned",
    "in_progress",
    "in_review",
    "done",
    "blocked",
}
PHASES = {
    "kickoff",
    "discovery",
    "planning",
    "breakdown",
    "implementation",
    "review",
    "integration",
    "done",
}
EVENT_TYPES = {
    "role_activated",
    "brainstorm_note",
    "plan_created",
    "roadmap_updated",
    "task_created",
    "task_assigned",
    "work_started",
    "artifact_written",
    "task_completed",
    "review_passed",
    "review_failed",
    "blocked",
    "assumption_logged",
    "handoff",
    "phase_advanced",
    "project_completed",
    "decision",
    "critique",
    "bug_reported",
    "scope_violation",
    "migration_baseline",
}
TASK_REQUIRED_EVENTS = {
    "task_created",
    "task_assigned",
    "work_started",
    "task_completed",
    "review_passed",
    "review_failed",
    "blocked",
    "handoff",
    "scope_violation",
}
TASK_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
TRANSIENT_PARTS = {"dispatch"}
TRANSIENT_NAMES = {"prompt.md", "result.json", "worker.log"}
TRANSIENT_SUFFIXES = {".tmp", ".bak", ".log"}
PRIVACY_CODES = {
    "missing_visibility",
    "invalid_visibility",
    "redaction_disabled",
    "tracked_transient",
    "tracked_local_state",
    "tracked_state_unknown",
    "transient_in_durable_state",
    "secret_material",
}
VERSION_CODES = {
    "migration_required",
    "unsupported_schema_version",
    "unsupported_protocol_version",
    "incompatible_protocol_version",
    "invalid_schema_version",
    "invalid_protocol_version",
}

GIT_TIMEOUT_SECONDS = 15
STATUS_PATH_REMEDIATION = (
    "Pass the project directory that contains .aphelocoma/, or run `aph status` "
    "from inside the project."
)
STATUS_START_REMEDIATION = (
    "Run `/aph-hamilton` in the project to start a Hamilton run, or pass the "
    "correct project directory."
)
STATUS_METADATA_REMEDIATION = (
    "Restore .aphelocoma/hamilton.json or recover it from a migration backup."
)
STATUS_BOARD_REMEDIATION = (
    "Repair .aphelocoma/state/tasks.json, then rerun the Hamilton validator "
    "(`python3 <skill>/references/validate.py <project-dir>`)."
)
STATUS_REPORT_FILENAME = "STATUS.md"
STATUS_WRITE_REMEDIATION = (
    "Make .aphelocoma/ writable, then rerun `aph status --write <project-dir>`."
)
STATUS_REFRESH_REMEDIATION = (
    "Run `aph status --write <project-dir>` to regenerate .aphelocoma/STATUS.md "
    "from current state."
)
STATUS_REPORT_FOOTER = (
    "This file is regenerated whole by `aph status --write`; edits to it are "
    "overwritten. `.aphelocoma/state/tasks.json` stays the source of truth."
)
# The stamp is written for a reader and parsed for the staleness check, so the
# writer below and this pattern must keep describing the same one line.
STATUS_STAMP_PATTERN = re.compile(
    r"(?m)^Generated (?P<generated>\S+) from ledger seq (?P<seq>\d+|unknown)\b"
)
REPO_ABSENT_SUMMARY = (
    "This project is not in a Git repository, so branch, commit, and "
    "working-tree details are unavailable."
)
REPO_UNAVAILABLE_SUMMARY = (
    "Git details are unavailable: the enclosing Git worktree could not be read."
)

SECRET_PATTERNS = (
    (
        "private key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "GitHub token",
        re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "OpenAI-style token",
        re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    ),
    (
        "assigned credential",
        re.compile(
            r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|"
            r"client[_-]?secret)\s*[:=]\s*[\"']?[^\s\"'#<>]{8,}"
        ),
    ),
)


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    path: str
    message: str
    remediation: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    project: str
    event_count: int
    task_count: int
    done_count: int
    errors: Tuple[ValidationIssue, ...]
    warnings: Tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> Dict[str, object]:
        return {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "project": self.project,
            "status": "ok" if self.ok else "invalid",
            "event_count": self.event_count,
            "task_count": self.task_count,
            "done_count": self.done_count,
            "errors": [issue.as_dict() for issue in self.errors],
            "warnings": [issue.as_dict() for issue in self.warnings],
        }


@dataclass(frozen=True)
class MigrationResult:
    status: str
    project: Path
    backup: Optional[Path]
    message: str


class MigrationError(RuntimeError):
    """A migration was refused or did not complete safely."""

    def __init__(self, message: str, backup: Optional[Path] = None) -> None:
        super().__init__(message)
        self.backup = backup


class StatusError(RuntimeError):
    """A progress board could not be rendered from the project's state."""

    def __init__(self, path: str, message: str, remediation: str) -> None:
        super().__init__(message)
        self.path = path
        self.remediation = remediation


@dataclass(frozen=True)
class TaskSummary:
    id: str
    title: str
    status: str
    owner: Optional[str]
    dependencies: Tuple[str, ...]

    def as_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class RepoSummary:
    """What Git could truthfully report; unknown fields stay ``None``."""

    state: str
    branch: Optional[str]
    detached: bool
    head: Optional[str]
    commits_since_start: Optional[int]
    clean: Optional[bool]
    changed_files: Optional[int]
    summary: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "branch": self.branch,
            "detached": self.detached,
            "head": self.head,
            "commits_since_start": self.commits_since_start,
            "clean": self.clean,
            "changed_files": self.changed_files,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class ProjectSummary:
    project: str
    phase: str
    schema_version: Optional[int]
    protocol_version: Optional[str]
    visibility: Optional[str]
    tasks: Tuple[TaskSummary, ...]
    blocked: Tuple[TaskSummary, ...]
    next_task: Optional[TaskSummary]
    repo: RepoSummary

    @property
    def total_count(self) -> int:
        return len(self.tasks)

    @property
    def done_count(self) -> int:
        return sum(1 for task in self.tasks if task.status == "done")

    def as_dict(self) -> Dict[str, object]:
        return {
            "schema_version": STATUS_REPORT_SCHEMA_VERSION,
            "status": "ok",
            "project": {
                "name": self.project,
                "phase": self.phase,
                "schema_version": self.schema_version,
                "protocol_version": self.protocol_version,
                "visibility": self.visibility,
            },
            "progress": {"done": self.done_count, "total": self.total_count},
            "tasks": [task.as_dict() for task in self.tasks],
            "blocked": [task.as_dict() for task in self.blocked],
            "next": None if self.next_task is None else self.next_task.as_dict(),
            "repo": self.repo.as_dict(),
        }


@dataclass(frozen=True)
class SchemaValidationError:
    keyword: str
    path: str
    message: str


def _json_type_matches(value: object, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def schema_validation_errors(
    instance: object,
    schema: Mapping[str, object],
) -> List[SchemaValidationError]:
    """Validate the JSON-Schema Draft 7 subset used by Hamilton contracts.

    The implementation is deliberately stdlib-only and supports the schema
    keywords used by ``state.schema.json`` and both Codex result schemas.
    """

    errors: List[SchemaValidationError] = []
    root_schema = schema

    def resolve(reference: str) -> Optional[Mapping[str, object]]:
        if not reference.startswith("#/"):
            return None
        current: object = root_schema
        for raw_part in reference[2:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current if isinstance(current, dict) else None

    def add(keyword: str, path: str, message: str) -> None:
        errors.append(SchemaValidationError(keyword, path, message))

    def check(value: object, node: object, path: str) -> None:
        if not isinstance(node, dict):
            add("schema", path, "Schema node must be an object.")
            return
        reference = node.get("$ref")
        if isinstance(reference, str):
            resolved = resolve(reference)
            if resolved is None:
                add("$ref", path, "Unresolvable schema reference %s." % reference)
            else:
                check(value, resolved, path)
            return

        expected = node.get("type")
        if isinstance(expected, str):
            expected_types = [expected]
        elif (
            isinstance(expected, list)
            and all(isinstance(item, str) for item in expected)
        ):
            expected_types = expected
        else:
            expected_types = []
        if expected_types and not any(
            _json_type_matches(value, item) for item in expected_types
        ):
            add(
                "type",
                path,
                "Expected %s." % " or ".join(expected_types),
            )
            return

        if "const" in node and value != node["const"]:
            add("const", path, "Value must equal %r." % node["const"])
        enum = node.get("enum")
        if isinstance(enum, list) and value not in enum:
            add("enum", path, "Value must be one of %r." % enum)

        all_of = node.get("allOf")
        if isinstance(all_of, list):
            for child in all_of:
                check(value, child, path)
        one_of = node.get("oneOf")
        if isinstance(one_of, list):
            matches = 0
            for child in one_of:
                before = len(errors)
                check(value, child, path)
                if len(errors) == before:
                    matches += 1
                else:
                    del errors[before:]
            if matches != 1:
                add("oneOf", path, "Value must match exactly one schema branch.")

        condition = node.get("if")
        if isinstance(condition, dict):
            before = len(errors)
            check(value, condition, path)
            matched = len(errors) == before
            del errors[before:]
            branch = node.get("then" if matched else "else")
            if isinstance(branch, dict):
                check(value, branch, path)

        if isinstance(value, dict):
            required = node.get("required")
            if isinstance(required, list):
                for key in required:
                    if isinstance(key, str) and key not in value:
                        add(
                            "required",
                            path,
                            "Missing required property %r." % key,
                        )
            properties = node.get("properties")
            property_map = properties if isinstance(properties, dict) else {}
            for key, child in property_map.items():
                if key in value:
                    check(value[key], child, "%s.%s" % (path, key))
            if node.get("additionalProperties") is False:
                for key in value:
                    if key not in property_map:
                        add(
                            "additionalProperties",
                            "%s.%s" % (path, key),
                            "Property %r is not allowed." % key,
                        )

        if isinstance(value, list):
            minimum_items = node.get("minItems")
            if isinstance(minimum_items, int) and len(value) < minimum_items:
                add(
                    "minItems",
                    path,
                    "Array must have at least %d item(s)." % minimum_items,
                )
            maximum_items = node.get("maxItems")
            if isinstance(maximum_items, int) and len(value) > maximum_items:
                add(
                    "maxItems",
                    path,
                    "Array must have at most %d item(s)." % maximum_items,
                )
            if node.get("uniqueItems") is True:
                encoded = [
                    json.dumps(item, sort_keys=True, separators=(",", ":"))
                    for item in value
                ]
                if len(encoded) != len(set(encoded)):
                    add("uniqueItems", path, "Array items must be unique.")
            item_schema = node.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(value):
                    check(item, item_schema, "%s[%d]" % (path, index))
            elif isinstance(item_schema, list):
                for index, child in enumerate(item_schema):
                    if index < len(value):
                        check(value[index], child, "%s[%d]" % (path, index))
                if len(value) > len(item_schema):
                    additional = node.get("additionalItems", {})
                    if additional is False:
                        add(
                            "additionalItems",
                            path,
                            "Array contains undeclared trailing items.",
                        )
                    elif isinstance(additional, dict):
                        for index in range(len(item_schema), len(value)):
                            check(
                                value[index],
                                additional,
                                "%s[%d]" % (path, index),
                            )
            contains = node.get("contains")
            if isinstance(contains, dict):
                matched = False
                for item in value:
                    before = len(errors)
                    check(item, contains, path)
                    if len(errors) == before:
                        matched = True
                    del errors[before:]
                    if matched:
                        break
                if not matched:
                    add("contains", path, "Array lacks a required matching item.")

        if isinstance(value, str):
            minimum_length = node.get("minLength")
            if isinstance(minimum_length, int) and len(value) < minimum_length:
                add(
                    "minLength",
                    path,
                    "String must have at least %d character(s)." % minimum_length,
                )
            pattern = node.get("pattern")
            if isinstance(pattern, str) and re.search(pattern, value) is None:
                add("pattern", path, "String does not match %s." % pattern)

        minimum = node.get("minimum")
        if (
            isinstance(minimum, (int, float))
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value < minimum
        ):
            add("minimum", path, "Number must be at least %s." % minimum)

    check(instance, schema, "$")
    return errors


class _Issues:
    def __init__(self) -> None:
        self.errors: List[ValidationIssue] = []
        self.warnings: List[ValidationIssue] = []

    def error(
        self,
        code: str,
        path: str,
        message: str,
        remediation: Optional[str] = None,
    ) -> None:
        self.errors.append(
            ValidationIssue("error", code, path, message, remediation)
        )

    def warning(
        self,
        code: str,
        path: str,
        message: str,
        remediation: Optional[str] = None,
    ) -> None:
        self.warnings.append(
            ValidationIssue("warning", code, path, message, remediation)
        )


def _load_json(path: Path, issues: _Issues, relative: str) -> Optional[object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.error(
            "missing_file",
            relative,
            "%s is missing." % relative,
            "Restore the Hamilton project state or recover it from a migration backup.",
        )
    except (OSError, UnicodeError) as error:
        issues.error(
            "unreadable_file",
            relative,
            "%s is unreadable: %s." % (relative, error),
            "Restore a readable UTF-8 copy of the file.",
        )
    except json.JSONDecodeError as error:
        issues.error(
            "invalid_json",
            relative,
            "%s contains invalid JSON at line %d: %s."
            % (relative, error.lineno, error.msg),
            "Repair the JSON without rewriting ledger history.",
        )
    return None


def _semver(value: object) -> Optional[Tuple[int, int, int]]:
    if not isinstance(value, str):
        return None
    match = SEMVER_PATTERN.fullmatch(value)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _validate_versions(
    hamilton: Optional[object], issues: _Issues
) -> Mapping[str, object]:
    if not isinstance(hamilton, dict):
        if hamilton is not None:
            issues.error(
                "invalid_hamilton_metadata",
                "hamilton.json",
                "hamilton.json must contain a JSON object.",
            )
        return {}

    schema = hamilton.get("schema_version")
    protocol = hamilton.get("protocol_version")
    if schema is None and protocol is None:
        issues.error(
            "migration_required",
            "hamilton.json",
            "This is unversioned Hamilton v0.2 project state.",
            "Run `python3 <skill>/references/migrate.py apply <project-dir>` "
            "with Aphelocoma v0.3 before resuming.",
        )
        return hamilton

    if isinstance(schema, bool) or not isinstance(schema, int):
        issues.error(
            "invalid_schema_version",
            "hamilton.json",
            "schema_version must be an integer.",
            "Recover a valid hamilton.json or migrate an unversioned v0.2 project.",
        )
    elif schema > CURRENT_SCHEMA_VERSION:
        issues.error(
            "unsupported_schema_version",
            "hamilton.json",
            "Project schema version %s is newer than supported version %s."
            % (schema, CURRENT_SCHEMA_VERSION),
            "Please upgrade Aphelocoma before opening this project; do not "
            "downgrade its state.",
        )
    elif schema < CURRENT_SCHEMA_VERSION:
        issues.error(
            "migration_required",
            "hamilton.json",
            "Project schema version %s requires migration to version %s."
            % (schema, CURRENT_SCHEMA_VERSION),
            "Run `python3 <skill>/references/migrate.py apply <project-dir>`.",
        )

    parsed_protocol = _semver(protocol)
    current_protocol = _semver(CURRENT_PROTOCOL_VERSION)
    if parsed_protocol is None:
        issues.error(
            "invalid_protocol_version",
            "hamilton.json",
            "protocol_version must be a semantic version such as %s."
            % CURRENT_PROTOCOL_VERSION,
            "Recover a valid hamilton.json or migrate an unversioned v0.2 project.",
        )
    elif current_protocol is not None and parsed_protocol > current_protocol:
        issues.error(
            "unsupported_protocol_version",
            "hamilton.json",
            "Project protocol version %s is newer than supported version %s."
            % (protocol, CURRENT_PROTOCOL_VERSION),
            "Upgrade Aphelocoma before resuming this project.",
        )
    elif current_protocol is not None and parsed_protocol < current_protocol:
        issues.error(
            "migration_required",
            "hamilton.json",
            "Project protocol version %s requires migration to %s."
            % (protocol, CURRENT_PROTOCOL_VERSION),
            "Run `python3 <skill>/references/migrate.py apply <project-dir>`.",
        )
    elif protocol != CURRENT_PROTOCOL_VERSION:
        issues.error(
            "incompatible_protocol_version",
            "hamilton.json",
            "Project protocol %s is not the exact supported contract %s."
            % (protocol, CURRENT_PROTOCOL_VERSION),
            "Use project state written for protocol %s; prerelease and "
            "build-tagged protocols are distinct contracts."
            % CURRENT_PROTOCOL_VERSION,
        )
    return hamilton


def _parse_settings(path: Path, issues: _Issues) -> Dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        issues.error(
            "missing_visibility",
            "settings.yaml",
            "settings.yaml is missing; Hamilton state visibility is not explicit.",
            "Create .aphelocoma/settings.yaml with `visibility: tracked` or "
            "`visibility: local`.",
        )
        return {}
    except (OSError, UnicodeError) as error:
        issues.error(
            "unreadable_file",
            "settings.yaml",
            "settings.yaml is unreadable: %s." % error,
        )
        return {}

    values: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or line[:1].isspace():
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match is None:
            continue
        raw = match.group(2).split(" #", 1)[0].strip()
        values[match.group(1)] = raw.strip("\"'")

    visibility = values.get("visibility")
    if visibility is None:
        issues.error(
            "missing_visibility",
            "settings.yaml",
            "Hamilton state visibility is not explicit.",
            "Add `visibility: tracked` or `visibility: local` to settings.yaml.",
        )
    elif visibility not in VISIBILITIES:
        issues.error(
            "invalid_visibility",
            "settings.yaml",
            "visibility must be `tracked` or `local`, not %r." % visibility,
            "Choose whether compact Hamilton state is committed (`tracked`) or "
            "kept out of version control (`local`).",
        )

    if values.get("redact_sensitive", "").lower() != "true":
        issues.error(
            "redaction_disabled",
            "settings.yaml",
            "redact_sensitive must be explicitly true for durable Hamilton state.",
            "Set `redact_sensitive: true`; never write prompts or credentials to "
            "durable state.",
        )
    return values


def _default_state_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "aph-hamilton"
        / "references"
        / "state.schema.json"
    )


def _validate_declared_state_schema(
    hamilton: object,
    settings: Mapping[str, str],
    board: object,
    events: Sequence[Mapping[str, object]],
    schema_path: Path,
    issues: _Issues,
) -> None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.error(
            "state_schema_missing",
            str(schema_path),
            "The declared Hamilton state schema is missing.",
            "Reinstall Aphelocoma to restore state.schema.json.",
        )
        return
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        issues.error(
            "state_schema_invalid",
            str(schema_path),
            "The declared Hamilton state schema is unreadable or invalid: %s."
            % error,
            "Reinstall Aphelocoma to restore state.schema.json.",
        )
        return
    if not isinstance(schema, dict):
        issues.error(
            "state_schema_invalid",
            str(schema_path),
            "state.schema.json must contain a JSON object.",
        )
        return

    normalized_settings: Dict[str, object] = {}
    if "visibility" in settings:
        normalized_settings["visibility"] = settings["visibility"]
    if "redact_sensitive" in settings:
        normalized_settings["redact_sensitive"] = (
            settings["redact_sensitive"].lower() == "true"
        )
    normalized = {
        "hamilton": hamilton,
        "settings": normalized_settings,
        "tasks": board,
        "events": list(events),
    }
    for violation in schema_validation_errors(normalized, schema):
        if violation.keyword == "required":
            code = "schema_required"
        elif violation.keyword == "additionalProperties":
            code = "schema_additional_property"
        else:
            code = "schema_violation"
        issues.error(
            code,
            violation.path,
            "state.schema.json: %s" % violation.message,
            "Repair the split .aphelocoma files to match state.schema.json.",
        )


def _validate_tasks(
    board: Optional[object],
    specs_dir: Path,
    issues: _Issues,
) -> Tuple[List[Mapping[str, object]], Dict[str, Mapping[str, object]]]:
    if not isinstance(board, dict):
        if board is not None:
            issues.error(
                "invalid_task_board",
                "state/tasks.json",
                "state/tasks.json must contain a JSON object.",
            )
        return [], {}
    raw_tasks = board.get("tasks")
    if not isinstance(raw_tasks, list):
        issues.error(
            "invalid_task_board",
            "state/tasks.json",
            "state/tasks.json must contain a tasks array.",
        )
        return [], {}

    tasks: List[Mapping[str, object]] = []
    by_id: Dict[str, Mapping[str, object]] = {}
    for index, raw_task in enumerate(raw_tasks):
        location = "state/tasks.json:tasks[%d]" % index
        if not isinstance(raw_task, dict):
            issues.error("invalid_task", location, "Each task must be an object.")
            continue
        task_id = raw_task.get("id")
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            issues.error(
                "invalid_task_id",
                location,
                "Task id must start with a letter and contain only letters, "
                "numbers, dot, underscore, or hyphen.",
            )
            continue
        if task_id in by_id:
            issues.error(
                "duplicate_task_id",
                location,
                "Task id %s occurs more than once." % task_id,
                "Give every task a stable unique id.",
            )
            continue
        tasks.append(raw_task)
        by_id[task_id] = raw_task

        status = raw_task.get("status")
        if status not in STATUSES:
            issues.error(
                "invalid_task_status",
                location,
                "Task %s has invalid status %r." % (task_id, status),
            )
            continue
        if status != "pending":
            owner = raw_task.get("owner")
            if not isinstance(owner, str) or not owner:
                issues.error(
                    "missing_task_owner",
                    location,
                    "Task %s is %s but has no owner." % (task_id, status),
                )
            spec = specs_dir / ("%s.md" % task_id)
            if not spec.is_file():
                issues.error(
                    "missing_task_spec",
                    "specs/%s.md" % task_id,
                    "Task %s is %s but has no handoff spec." % (task_id, status),
                    "Create the task spec before assigning work.",
                )
            else:
                try:
                    spec_text = spec.read_text(encoding="utf-8").lower()
                except (OSError, UnicodeError) as error:
                    issues.error(
                        "unreadable_file",
                        "specs/%s.md" % task_id,
                        "Task spec is unreadable: %s." % error,
                    )
                else:
                    if "acceptance criteria" not in spec_text:
                        issues.warning(
                            "missing_acceptance_criteria",
                            "specs/%s.md" % task_id,
                            "Task spec has no Acceptance criteria section.",
                        )

    for task_id, task in by_id.items():
        dependencies = task.get("dependencies", [])
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) for item in dependencies
        ):
            issues.error(
                "invalid_dependencies",
                "state/tasks.json",
                "Task %s dependencies must be an array of task ids." % task_id,
            )
            continue
        for dependency in dependencies:
            if dependency == task_id:
                issues.error(
                    "dependency_cycle",
                    "state/tasks.json",
                    "Task %s depends on itself." % task_id,
                )
            elif dependency not in by_id:
                issues.error(
                    "unknown_dependency",
                    "state/tasks.json",
                    "Task %s references missing dependency %s."
                    % (task_id, dependency),
                )
    _validate_dependency_cycles(by_id, issues)

    phase = board.get("phase")
    if phase not in PHASES:
        issues.error(
            "invalid_phase",
            "state/tasks.json",
            "Task-board phase %r is not a canonical Hamilton phase." % phase,
        )
    if phase in {"breakdown", "implementation", "review", "integration", "done"}:
        conventions = specs_dir.parent / "state" / "conventions.md"
        if not conventions.is_file():
            issues.warning(
                "missing_conventions",
                "state/conventions.md",
                "Project conventions are missing after planning.",
                "Write the binding project conventions before implementation.",
            )
        else:
            try:
                conventions_text = conventions.read_text(
                    encoding="utf-8"
                ).lower()
            except (OSError, UnicodeError) as error:
                issues.warning(
                    "missing_conventions",
                    "state/conventions.md",
                    "Project conventions are unreadable: %s." % error,
                )
            else:
                if (
                    "no active project yet" in conventions_text
                    or "stub —" in conventions_text
                ):
                    issues.warning(
                        "stub_conventions",
                        "state/conventions.md",
                        "Project conventions are still the template stub after planning.",
                        "Replace the stub with the project's binding conventions.",
                    )
    return tasks, by_id


def _validate_dependency_cycles(
    by_id: Mapping[str, Mapping[str, object]], issues: _Issues
) -> None:
    visited: Set[str] = set()
    visiting: Set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            issues.error(
                "dependency_cycle",
                "state/tasks.json",
                "Task dependency graph contains a cycle involving %s." % task_id,
            )
            return
        visiting.add(task_id)
        dependencies = by_id[task_id].get("dependencies", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if isinstance(dependency, str) and dependency in by_id:
                    visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for identifier in by_id:
        visit(identifier)


def _load_events(path: Path, issues: _Issues) -> List[Mapping[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        issues.error(
            "missing_file",
            "ledger/events.jsonl",
            "ledger/events.jsonl is missing.",
        )
        return []
    except (OSError, UnicodeError) as error:
        issues.error(
            "unreadable_file",
            "ledger/events.jsonl",
            "ledger/events.jsonl is unreadable: %s." % error,
        )
        return []

    events: List[Mapping[str, object]] = []
    expected_seq = 1
    previous: Optional[Mapping[str, object]] = None
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        location = "ledger/events.jsonl:%d" % line_number
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            issues.error(
                "invalid_event_json",
                location,
                "Ledger line is invalid JSON: %s." % error.msg,
                "Append a corrective event where possible; recover corrupt history "
                "from a known-good backup.",
            )
            continue
        if not isinstance(event, dict):
            issues.error(
                "invalid_event",
                location,
                "Each ledger line must be a JSON object.",
            )
            continue
        for field in ("ts", "seq", "event", "actor", "task", "to", "note"):
            if field not in event:
                issues.error(
                    "missing_event_field",
                    location,
                    "Ledger event is missing required field %r." % field,
                )
        seq = event.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int):
            issues.error(
                "invalid_event_sequence",
                location,
                "Ledger seq must be an integer.",
            )
        else:
            if seq != expected_seq:
                issues.error(
                    "invalid_event_sequence",
                    location,
                    "Ledger seq is %s; expected %s (gap-free from 1)."
                    % (seq, expected_seq),
                )
            expected_seq = seq + 1
        event_type = event.get("event")
        if event_type not in EVENT_TYPES:
            issues.error(
                "unknown_event_type",
                location,
                "Unknown Hamilton event type %r." % event_type,
            )
        actor = event.get("actor")
        if not isinstance(actor, str) or not actor:
            issues.error(
                "invalid_event_actor",
                location,
                "Ledger actor must be a non-empty role id or advisor.",
            )
        note = event.get("note")
        if not isinstance(note, str):
            issues.error(
                "invalid_event_note",
                location,
                "Ledger note must be a string.",
            )
        for optional_reference in ("task", "to"):
            value = event.get(optional_reference)
            if value is not None and not isinstance(value, str):
                issues.error(
                    "invalid_event_reference",
                    location,
                    "%s must be a string or null." % optional_reference,
                )
        if previous is not None and all(
            previous.get(key) == event.get(key)
            for key in ("event", "actor", "task", "to", "note")
        ):
            issues.warning(
                "duplicate_event",
                location,
                "Ledger event duplicates the previous event; replay may have "
                "double-appended it.",
            )
        previous = event
        events.append(event)
    return events


def _event_error(
    issues: _Issues,
    event: Mapping[str, object],
    code: str,
    message: str,
    remediation: Optional[str] = None,
) -> None:
    issues.error(
        code,
        "ledger/events.jsonl:seq=%s" % event.get("seq"),
        message,
        remediation,
    )


def _event_prefix_digest(
    events: Sequence[Mapping[str, object]],
    through_seq: int,
) -> str:
    digest = hashlib.sha256()
    for event in events:
        sequence = event.get("seq")
        if (
            isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence > through_seq
        ):
            continue
        digest.update(
            json.dumps(
                event,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    return digest.hexdigest()


def _task_states_digest(task_states: Sequence[object]) -> str:
    return hashlib.sha256(
        json.dumps(
            task_states,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    ).hexdigest()


def _migration_marker_note(
    through_seq: int,
    prefix_digest: str,
    task_states_digest: str,
) -> str:
    return (
        "Migrated unversioned v0.2 history through seq %d with event "
        "SHA-256 %s and task-state SHA-256 %s; strict replay begins after "
        "this marker."
        % (through_seq, prefix_digest, task_states_digest)
    )


def _legacy_history_baseline(
    metadata: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    by_id: Mapping[str, Mapping[str, object]],
    issues: _Issues,
) -> Tuple[int, Dict[str, str]]:
    raw = metadata.get("history_baseline")
    if raw is None:
        if any(
            event.get("event") == "migration_baseline"
            for event in events
        ):
            issues.error(
                "invalid_history_baseline",
                "ledger/events.jsonl",
                "A migration baseline marker requires matching Hamilton metadata.",
            )
        return 0, {}
    if not isinstance(raw, dict):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline must be an object.",
        )
        return 0, {}
    if raw.get("source") != LEGACY_HISTORY_SOURCE:
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline source must be %r." % LEGACY_HISTORY_SOURCE,
        )
        return 0, {}
    through_seq = raw.get("through_seq")
    if (
        isinstance(through_seq, bool)
        or not isinstance(through_seq, int)
        or through_seq < 0
    ):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline through_seq must be a non-negative integer.",
        )
        return 0, {}
    event_sequences = [
        event.get("seq")
        for event in events
        if isinstance(event.get("seq"), int)
        and not isinstance(event.get("seq"), bool)
    ]
    if through_seq > (max(event_sequences) if event_sequences else 0):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline through_seq exceeds the ledger sequence.",
        )
        return 0, {}
    prefix_digest = raw.get("prefix_digest")
    if (
        not isinstance(prefix_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", prefix_digest) is None
    ):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline prefix_digest must be a SHA-256 digest.",
        )
        return 0, {}
    actual_digest = _event_prefix_digest(events, through_seq)
    if prefix_digest != actual_digest:
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline digest does not match the declared ledger prefix.",
        )
        return 0, {}
    raw_states = raw.get("task_states")
    if not isinstance(raw_states, list):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline task_states must be an array.",
        )
        return 0, {}
    task_states_digest = raw.get("task_states_digest")
    if (
        not isinstance(task_states_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", task_states_digest) is None
    ):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline task_states_digest must be a SHA-256 digest.",
        )
        return 0, {}
    if task_states_digest != _task_states_digest(raw_states):
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "history_baseline digest does not match its task-state snapshot.",
        )
        return 0, {}
    markers = [
        event
        for event in events
        if event.get("event") == "migration_baseline"
    ]
    expected_note = _migration_marker_note(
        through_seq,
        prefix_digest,
        task_states_digest,
    )
    if (
        len(markers) != 1
        or markers[0].get("seq") != through_seq + 1
        or markers[0].get("actor") != "orchestrator"
        or markers[0].get("task") is not None
        or markers[0].get("to") is not None
        or markers[0].get("note") != expected_note
    ):
        issues.error(
            "invalid_history_baseline",
            "ledger/events.jsonl",
            "history_baseline requires one canonical marker immediately after "
            "the bound legacy prefix.",
        )
        return 0, {}

    states: Dict[str, str] = {}
    for index, item in enumerate(raw_states):
        location = "hamilton.json:history_baseline.task_states[%d]" % index
        if not isinstance(item, dict):
            issues.error(
                "invalid_history_baseline",
                location,
                "History baseline task state must be an object.",
            )
            continue
        task_id = item.get("id")
        status = item.get("status")
        if not isinstance(task_id, str) or task_id not in by_id:
            issues.error(
                "invalid_history_baseline",
                location,
                "History baseline references an unknown task %r." % task_id,
            )
            continue
        if task_id in states:
            issues.error(
                "invalid_history_baseline",
                location,
                "History baseline repeats task %s." % task_id,
            )
            continue
        if not isinstance(status, str) or status not in STATUSES:
            issues.error(
                "invalid_history_baseline",
                location,
                "History baseline has invalid status %r for task %s."
                % (status, task_id),
            )
            continue
        states[task_id] = status
    legacy_task_ids = {
        str(event["task"])
        for event in events
        if isinstance(event.get("seq"), int)
        and event["seq"] <= through_seq
        and isinstance(event.get("task"), str)
        and event["task"] in by_id
    }
    missing = sorted(legacy_task_ids - set(states))
    if missing:
        issues.error(
            "invalid_history_baseline",
            "hamilton.json",
            "History baseline omits legacy task(s): %s." % ", ".join(missing),
        )
        return 0, {}
    return through_seq, states


def _validate_event_protocol(
    events: Sequence[Mapping[str, object]],
    by_id: Mapping[str, Mapping[str, object]],
    issues: _Issues,
    *,
    baseline_seq: int = 0,
    baseline_states: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    states: Dict[str, str] = dict(baseline_states or {})
    builders: Dict[str, str] = {
        task_id: str(by_id[task_id].get("owner"))
        for task_id, status in states.items()
        if status in {"in_progress", "in_review"}
        and isinstance(by_id[task_id].get("owner"), str)
    }
    critiques: Dict[str, str] = {}

    for event in events:
        sequence = event.get("seq")
        if (
            isinstance(sequence, int)
            and not isinstance(sequence, bool)
            and sequence <= baseline_seq
        ):
            task_value = event.get("task")
            if isinstance(task_value, str) and task_value not in by_id:
                _event_error(
                    issues,
                    event,
                    "unknown_task_reference",
                    "Legacy event references missing task %s." % task_value,
                )
            continue
        event_type = event.get("event")
        task_value = event.get("task")
        task_id = task_value if isinstance(task_value, str) else None

        if event_type in TASK_REQUIRED_EVENTS and task_id is None:
            _event_error(
                issues,
                event,
                "missing_task_reference",
                "%s requires a task id." % event_type,
            )
            continue
        if task_id is not None and task_id not in by_id:
            _event_error(
                issues,
                event,
                "unknown_task_reference",
                "Event references missing task %s." % task_id,
            )
            continue
        if task_id is None:
            continue

        state = states.get(task_id)
        actor = event.get("actor")
        actor_id = actor if isinstance(actor, str) else ""
        if event_type == "task_created":
            if state is not None:
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s was created more than once." % task_id,
                )
            else:
                states[task_id] = "pending"
        elif event_type == "task_assigned":
            if state not in {"pending", "blocked", "assigned"}:
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s cannot be assigned from %s."
                    % (task_id, state or "no prior state"),
                )
            else:
                states[task_id] = "assigned"
                critiques.pop(task_id, None)
            expected_owner = by_id[task_id].get("owner")
            if (
                isinstance(expected_owner, str)
                and event.get("to") != expected_owner
            ):
                _event_error(
                    issues,
                    event,
                    "assignment_owner_mismatch",
                    "Task %s is owned by %s but assignment targets %r."
                    % (task_id, expected_owner, event.get("to")),
                )
        elif event_type == "work_started":
            if state != "assigned":
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s cannot start work from %s."
                    % (task_id, state or "no prior state"),
                )
            else:
                states[task_id] = "in_progress"
                builders[task_id] = actor_id
                critiques.pop(task_id, None)
            expected_owner = by_id[task_id].get("owner")
            if (
                isinstance(expected_owner, str)
                and expected_owner != actor_id
            ):
                _event_error(
                    issues,
                    event,
                    "builder_owner_mismatch",
                    "Task %s is owned by %s but work started as %s."
                    % (task_id, expected_owner, actor_id),
                )
        elif event_type == "artifact_written":
            if state not in {"in_progress", "in_review", "done"}:
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s cannot record an artifact from %s."
                    % (task_id, state or "no prior state"),
                )
        elif event_type == "handoff":
            if state != "in_progress":
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s cannot enter review from %s."
                    % (task_id, state or "no prior state"),
                )
            else:
                states[task_id] = "in_review"
                critiques.pop(task_id, None)
        elif event_type == "critique":
            if state != "in_review":
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s critique occurred before a valid review handoff."
                    % task_id,
                )
            builder = builders.get(task_id)
            if builder is None:
                owner = by_id[task_id].get("owner")
                builder = owner if isinstance(owner, str) else None
            if builder is not None and actor_id == builder:
                _event_error(
                    issues,
                    event,
                    "reviewer_is_builder",
                    "Task %s critique actor %s is also its builder."
                    % (task_id, actor_id),
                    "Dispatch a fresh reviewer whose role/instance differs from "
                    "the builder, then log a new critique.",
                )
            else:
                critiques[task_id] = actor_id
        elif event_type in {"review_passed", "review_failed"}:
            if state != "in_review":
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s cannot record %s from %s."
                    % (task_id, event_type, state or "no prior state"),
                )
            reviewer = critiques.get(task_id)
            if reviewer is None:
                _event_error(
                    issues,
                    event,
                    "review_before_critique",
                    "Task %s recorded %s before an independent critique."
                    % (task_id, event_type),
                    "Log the independent critique before its review verdict.",
                )
            elif actor_id != reviewer and reviewer != "reviewer":
                _event_error(
                    issues,
                    event,
                    "review_actor_mismatch",
                    "Task %s verdict actor %s differs from critique actor %s."
                    % (task_id, actor_id, reviewer),
                )
            builder = builders.get(task_id)
            if builder is None:
                owner = by_id[task_id].get("owner")
                builder = owner if isinstance(owner, str) else None
            if builder is not None and actor_id == builder:
                _event_error(
                    issues,
                    event,
                    "reviewer_is_builder",
                    "Task %s verdict actor %s is also its builder."
                    % (task_id, actor_id),
                )
                reviewer = None
            if state == "in_review" and reviewer is not None:
                states[task_id] = (
                    "done" if event_type == "review_passed" else "assigned"
                )
                if event_type == "review_failed":
                    critiques.pop(task_id, None)
        elif event_type == "blocked":
            if state is None:
                _event_error(
                    issues,
                    event,
                    "invalid_transition",
                    "Task %s was blocked before it was created." % task_id,
                )
            else:
                states[task_id] = "blocked"
                critiques.pop(task_id, None)
        elif event_type == "task_completed" and state != "done":
            _event_error(
                issues,
                event,
                "invalid_transition",
                "Task %s cannot be completed before independent review passes."
                % task_id,
            )

    for task_id, task in by_id.items():
        status = task.get("status")
        history_status = states.get(task_id)
        if status != history_status:
            issues.error(
                "lifecycle_status_mismatch",
                "state/tasks.json",
                "Task %s live status is %r but ordered lifecycle history "
                "resolves to %r." % (task_id, status, history_status),
                "Append the required created/assigned/work_started/handoff/"
                "review events through the orchestrator and update live state "
                "in the same serialization step.",
            )
        if status == "done" and history_status != "done":
            issues.error(
                "done_gate_missing",
                "state/tasks.json",
                "Task %s is done but its event history does not contain an "
                "ordered independent critique and review_passed verdict." % task_id,
                "Return the task to in_review and run an independent review.",
            )
    return states


def _tracked_paths_from_git(project_root: Path) -> Optional[List[str]]:
    """Return project-relative paths tracked by any enclosing worktree.

    ``git ls-files`` is the authority for index formats and extensions,
    including index v4 and split indexes. Every enclosing worktree is checked
    so a nested repository cannot hide paths already staged by an outer one.
    Returning ``None`` means Git context or tracked state is indeterminate.
    """

    contexts = _git_contexts(project_root)
    if contexts is None:
        return None
    tracked: Set[str] = set()
    for worktree_root, _ in contexts:
        try:
            project_prefix = project_root.resolve().relative_to(
                worktree_root.resolve()
            )
        except ValueError:
            return None
        try:
            completed = subprocess.run(
                ["git", "-C", str(worktree_root), "ls-files", "-z"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        try:
            paths = [
                raw.decode("utf-8", "surrogateescape")
                for raw in completed.stdout.split(b"\0")
                if raw
            ]
        except (AttributeError, UnicodeError):
            return None
        prefix = "" if str(project_prefix) == "." else project_prefix.as_posix()
        if not prefix:
            tracked.update(paths)
            continue
        prefix_with_slash = prefix.rstrip("/") + "/"
        tracked.update(
            path[len(prefix_with_slash):]
            for path in paths
            if path.startswith(prefix_with_slash)
        )
    return sorted(tracked)


def _is_transient(path: str) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    if "dispatch" in parts:
        return True
    name = parts[-1] if parts else ""
    return name in TRANSIENT_NAMES or Path(name).suffix.lower() in TRANSIENT_SUFFIXES


def _validate_tracking(
    project_root: Path,
    aph: Path,
    visibility: Optional[str],
    tracked_files: Optional[Iterable[str]],
    issues: _Issues,
) -> None:
    tracked = (
        list(tracked_files)
        if tracked_files is not None
        else _tracked_paths_from_git(project_root)
    )
    if tracked is None:
        issues.error(
            "tracked_state_unknown",
            ".git",
            "Git tracked-state privacy could not be determined.",
            "Restore access to the enclosing Git worktree and rerun "
            "`aph doctor` before continuing.",
        )
        return
    normalized = []
    for item in tracked:
        clean = item.replace("\\", "/")
        if clean.startswith("./"):
            clean = clean[2:]
        normalized.append(clean)
    aph_tracked = [item for item in normalized if item.startswith(".aphelocoma/")]
    for item in aph_tracked:
        if _is_transient(item):
            issues.error(
                "tracked_transient",
                item,
                "Transient Hamilton prompt/result/log content is tracked.",
                "Remove it from version control and keep `.aphelocoma/dispatch/`, "
                "`*.tmp`, `*.bak`, and `*.log` ignored.",
            )
    if visibility == "local" and aph_tracked:
        issues.error(
            "tracked_local_state",
            "settings.yaml",
            "visibility is local but Hamilton state is tracked: %s."
            % ", ".join(sorted(aph_tracked)[:5]),
            "Remove .aphelocoma/ from version control and ignore it at the "
            "project root, or choose `visibility: tracked`.",
        )

    for path in aph.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(aph).as_posix()
        if relative.startswith("dispatch/"):
            continue
        if _is_transient(relative):
            issues.error(
                "transient_in_durable_state",
                ".aphelocoma/%s" % relative,
                "Dispatch prompts, results, temporary files, and worker logs "
                "must live only under transient dispatch/.",
                "Move transient worker data under .aphelocoma/dispatch/ and "
                "delete it after serialization.",
            )


def _validate_status_report(aph: Path, issues: _Issues) -> None:
    """Warn when the written board is missing, unstamped, or off the ledger.

    Every finding here is a warning: a board that has fallen behind is a
    visibility miss, not corrupt state, and must never block a resume.

    The ledger's last ``seq`` is read through ``_last_ledger_seq`` — the same
    function the writer stamps with — so the writer and this check cannot
    disagree about what "last" means on a ledger that is not gap-free.
    """

    path = aph / STATUS_REPORT_FILENAME
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.warning(
            "missing_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md is missing, so the progress board cannot be read "
            "outside a terminal.",
            STATUS_REFRESH_REMEDIATION,
        )
        return
    except (OSError, UnicodeError) as error:
        issues.warning(
            "unreadable_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md is unreadable: %s." % error,
            STATUS_REFRESH_REMEDIATION,
        )
        return

    match = STATUS_STAMP_PATTERN.search(text)
    if match is None:
        issues.warning(
            "stale_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md carries no readable generated stamp, so it cannot be "
            "told apart from a stale board.",
            STATUS_REFRESH_REMEDIATION,
        )
        return
    if match.group("seq") == "unknown":
        # The stamp is there and readable; it just admits that the ledger could
        # not be read when the board was written, so there is nothing to compare.
        issues.warning(
            "unsequenced_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md was generated with no ledger seq, so how current it is "
            "cannot be established.",
            STATUS_REFRESH_REMEDIATION,
        )
        return

    last_seq = _last_ledger_seq(aph)
    if last_seq is None:
        # An unreadable ledger is already reported against the ledger itself;
        # do not repeat it as a second finding against the board.
        return
    stamped_seq = int(match.group("seq"))
    behind = last_seq - stamped_seq
    if behind > 0:
        issues.warning(
            "stale_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md was generated from ledger seq %d and is %d event(s) "
            "behind the ledger's seq %d."
            % (stamped_seq, behind, last_seq),
            STATUS_REFRESH_REMEDIATION,
        )
    elif behind < 0:
        # A board ahead of the ledger cannot have come from it: the ledger was
        # truncated or rolled back under it. Trusting the stamp here would
        # disable the staleness check for every event that follows.
        issues.warning(
            "inconsistent_status_report",
            STATUS_REPORT_FILENAME,
            "STATUS.md was generated from ledger seq %d, which is ahead of the "
            "ledger's last seq %d, so it does not describe this ledger."
            % (stamped_seq, last_seq),
            STATUS_REFRESH_REMEDIATION,
        )


def _scan_secrets(aph: Path, issues: _Issues) -> None:
    for path in aph.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(aph).as_posix()
        if relative.startswith("dispatch/"):
            continue
        if path.suffix.lower() not in {
            ".json",
            ".jsonl",
            ".yaml",
            ".yml",
            ".md",
            ".txt",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match is None:
                continue
            line = text.count("\n", 0, match.start()) + 1
            issues.error(
                "secret_material",
                ".aphelocoma/%s:%d" % (relative, line),
                "Durable Hamilton state appears to contain %s." % label,
                "Rotate any real credential, replace the durable value with a "
                "redacted summary, and keep raw prompts/results transient.",
            )
            break


def validate_project(
    project_root: Path,
    *,
    tracked_files: Optional[Iterable[str]] = None,
    state_schema_path: Optional[Path] = None,
) -> ValidationReport:
    """Validate one project's split Hamilton state without modifying it."""

    root = Path(project_root).resolve()
    aph = root / ".aphelocoma"
    issues = _Issues()
    if not aph.is_dir():
        issues.error(
            "missing_project_state",
            ".aphelocoma",
            "No .aphelocoma project state exists in %s." % root,
            "Run Hamilton start in the project, or pass the correct project directory.",
        )
        return ValidationReport(
            root.name, 0, 0, 0, tuple(issues.errors), tuple(issues.warnings)
        )

    hamilton = _load_json(aph / "hamilton.json", issues, "hamilton.json")
    metadata = _validate_versions(hamilton, issues)
    settings = _parse_settings(aph / "settings.yaml", issues)
    board = _load_json(
        aph / "state" / "tasks.json", issues, "state/tasks.json"
    )
    tasks, by_id = _validate_tasks(board, aph / "specs", issues)
    events = _load_events(aph / "ledger" / "events.jsonl", issues)
    _validate_declared_state_schema(
        hamilton,
        settings,
        board,
        events,
        (
            Path(state_schema_path)
            if state_schema_path is not None
            else _default_state_schema_path()
        ),
        issues,
    )
    baseline_seq, baseline_states = _legacy_history_baseline(
        metadata,
        events,
        by_id,
        issues,
    )
    _validate_event_protocol(
        events,
        by_id,
        issues,
        baseline_seq=baseline_seq,
        baseline_states=baseline_states,
    )
    _validate_tracking(
        root,
        aph,
        settings.get("visibility"),
        tracked_files,
        issues,
    )
    _validate_status_report(aph, issues)
    _scan_secrets(aph, issues)

    project = metadata.get("project")
    if not isinstance(project, str) or not project:
        project = root.name
        issues.error(
            "invalid_project_id",
            "hamilton.json",
            "Hamilton project must be a non-empty string.",
        )
    roles = metadata.get("roles")
    if not isinstance(roles, list) or not roles or any(
        not isinstance(role, str) or not role for role in roles
    ):
        issues.error(
            "invalid_roles",
            "hamilton.json",
            "Hamilton roles must be a non-empty array of role ids.",
        )
    phase = metadata.get("phase")
    if phase not in PHASES:
        issues.error(
            "invalid_phase",
            "hamilton.json",
            "Hamilton phase %r is not canonical." % phase,
        )
    if isinstance(board, dict) and board.get("phase") != phase:
        issues.error(
            "phase_mismatch",
            "state/tasks.json",
            "hamilton.json phase %r differs from tasks.json phase %r."
            % (phase, board.get("phase")),
            "Update both live-state phase fields together.",
        )

    done_count = sum(1 for task in tasks if task.get("status") == "done")
    return ValidationReport(
        str(project),
        len(events),
        len(tasks),
        done_count,
        tuple(issues.errors),
        tuple(issues.warnings),
    )


def _parse_timestamp(value: object) -> Optional[datetime]:
    """Parse an ISO-8601 instant, returning ``None`` when it is unusable.

    Python 3.9's ``fromisoformat`` rejects the ``Z`` suffix Hamilton writes, and a
    naive value is read as UTC so comparisons never raise.
    """

    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text[-1] in {"Z", "z"}:
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _git_output(worktree_root: Path, arguments: Sequence[str]) -> Optional[str]:
    """Run one read-only Git command. ``None`` means the answer is unknown."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(worktree_root), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    try:
        return completed.stdout.decode("utf-8", "surrogateescape")
    except (AttributeError, UnicodeError):
        return None


def _commits_since(
    worktree_root: Path,
    started_at: Optional[datetime],
) -> Tuple[Optional[int], str]:
    """Count commits recorded since the run began, or say why it is unknown.

    Every reachable commit is inspected rather than relying on Git's
    walk-stopping ``--since`` heuristic, which under-reports across merges. A
    single unreadable timestamp makes the whole count unknown: the board must
    never print a number it cannot stand behind.
    """

    if started_at is None:
        return None, (
            "commits since kickoff unknown (hamilton.json has no readable "
            "`created` timestamp)"
        )
    # `--no-show-signature` keeps a user's `log.showSignature` from interleaving
    # verification output that would turn a readable count into a false unknown.
    log = _git_output(
        worktree_root, ["log", "--no-show-signature", "--format=%cI", "HEAD"]
    )
    if log is None:
        return None, (
            "commits since kickoff unknown (the commit history could not be read)"
        )
    count = 0
    for line in log.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        committed = _parse_timestamp(stripped)
        if committed is None:
            return None, (
                "commits since kickoff unknown (a commit timestamp could not "
                "be read)"
            )
        if committed >= started_at:
            count += 1
    return count, "%d commit%s since kickoff" % (count, "" if count == 1 else "s")


def _summarize_repo(
    project_root: Path,
    started_at: Optional[datetime],
) -> RepoSummary:
    """Describe the enclosing repository, degrading instead of failing."""

    contexts = _git_contexts(project_root)
    if contexts is None:
        return RepoSummary(
            "unavailable",
            None,
            False,
            None,
            None,
            None,
            None,
            REPO_UNAVAILABLE_SUMMARY,
        )
    if not contexts:
        return RepoSummary(
            "absent", None, False, None, None, None, None, REPO_ABSENT_SUMMARY
        )

    worktree_root = contexts[0][0]
    branch_output = _git_output(
        worktree_root, ["symbolic-ref", "--quiet", "--short", "HEAD"]
    )
    branch = branch_output.strip() if branch_output else None
    head_output = _git_output(worktree_root, ["rev-parse", "--short", "HEAD"])
    head = head_output.strip() if head_output else None
    detached = branch is None and head is not None

    commits: Optional[int] = None
    commits_clause: Optional[str] = None
    if head is None:
        location = (
            "branch %s has no commits yet" % branch
            if branch
            else "HEAD names neither a branch nor a commit yet"
        )
    else:
        commits, commits_clause = _commits_since(worktree_root, started_at)
        location = (
            "detached HEAD at %s" % head
            if detached
            else "branch %s at %s" % (branch, head)
        )

    # `--untracked-files=normal` overrides a user's `status.showUntrackedFiles`,
    # which would otherwise let a repository full of untracked work report clean.
    porcelain = _git_output(
        worktree_root, ["status", "--porcelain", "--untracked-files=normal"]
    )
    if porcelain is None:
        clean: Optional[bool] = None
        changed: Optional[int] = None
        tree_clause = "working-tree state could not be read"
    else:
        changed = sum(1 for line in porcelain.splitlines() if line.strip())
        clean = changed == 0
        tree_clause = (
            "working tree clean"
            if clean
            else "%d uncommitted or untracked file%s"
            % (changed, "" if changed == 1 else "s")
        )

    clauses = [location]
    if commits_clause is not None:
        clauses.append(commits_clause)
    clauses.append(tree_clause)
    return RepoSummary(
        "ok",
        branch,
        detached,
        head,
        commits,
        clean,
        changed,
        ", ".join(clauses) + ".",
    )


def _status_tasks(board: object) -> Tuple[TaskSummary, ...]:
    """Read the task board for display, refusing state that cannot be trusted."""

    if not isinstance(board, dict) or not isinstance(board.get("tasks"), list):
        raise StatusError(
            "state/tasks.json",
            "state/tasks.json must contain a JSON object with a tasks array.",
            STATUS_BOARD_REMEDIATION,
        )
    summaries: List[TaskSummary] = []
    for index, raw_task in enumerate(board["tasks"]):
        if not isinstance(raw_task, dict):
            raise StatusError(
                "state/tasks.json",
                "state/tasks.json tasks[%d] is not a JSON object." % index,
                STATUS_BOARD_REMEDIATION,
            )
        task_id = raw_task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise StatusError(
                "state/tasks.json",
                "state/tasks.json tasks[%d] has no usable task id." % index,
                STATUS_BOARD_REMEDIATION,
            )
        title = raw_task.get("title")
        status = raw_task.get("status")
        owner = raw_task.get("owner")
        raw_dependencies = raw_task.get("dependencies")
        summaries.append(
            TaskSummary(
                task_id,
                title if isinstance(title, str) and title else "(untitled)",
                status if isinstance(status, str) and status else "unknown",
                owner if isinstance(owner, str) and owner else None,
                tuple(
                    item
                    for item in raw_dependencies
                    if isinstance(item, str)
                )
                if isinstance(raw_dependencies, list)
                else (),
            )
        )
    return tuple(summaries)


def _next_actionable(tasks: Sequence[TaskSummary]) -> Optional[TaskSummary]:
    """The first board-order task that is open and whose dependencies are done."""

    finished = {task.id for task in tasks if task.status == "done"}
    for task in tasks:
        if task.status in {"done", "blocked"}:
            continue
        if all(dependency in finished for dependency in task.dependencies):
            return task
    return None


def summarize_project(project_root: Path) -> ProjectSummary:
    """Summarize one project's Hamilton state and Git context, read-only.

    Nothing under ``.aphelocoma/`` is written and no ledger event is appended:
    rendering the board is looking, not acting (PROTOCOL §5.6). Unversioned or
    unsupported state is refused with the same remediation ``resume`` reports,
    rather than being interpreted on a guess.
    """

    root = Path(project_root)
    try:
        resolved = root.resolve()
    except (OSError, RuntimeError) as error:
        raise StatusError(
            str(root),
            "Project path %s could not be resolved: %s." % (root, error),
            STATUS_PATH_REMEDIATION,
        ) from error
    if not resolved.is_dir():
        raise StatusError(
            str(resolved),
            "%s is not a directory." % resolved,
            STATUS_PATH_REMEDIATION,
        )
    aph = resolved / ".aphelocoma"
    if not aph.is_dir():
        raise StatusError(
            ".aphelocoma",
            "No Hamilton project state exists in %s." % resolved,
            STATUS_START_REMEDIATION,
        )

    metadata_issues = _Issues()
    hamilton = _load_json(aph / "hamilton.json", metadata_issues, "hamilton.json")
    if metadata_issues.errors:
        first = metadata_issues.errors[0]
        raise StatusError(
            first.path,
            first.message,
            first.remediation or STATUS_METADATA_REMEDIATION,
        )
    if not isinstance(hamilton, dict):
        raise StatusError(
            "hamilton.json",
            "hamilton.json must contain a JSON object.",
            STATUS_METADATA_REMEDIATION,
        )

    # Only version findings refuse the board. Privacy and integrity findings
    # belong to `aph doctor` and the validator; looking must still work.
    version_issues = _Issues()
    _validate_versions(hamilton, version_issues)
    blocking = [
        issue for issue in version_issues.errors if issue.code in VERSION_CODES
    ]
    if blocking:
        raise StatusError(
            blocking[0].path,
            blocking[0].message,
            blocking[0].remediation
            or "Run the Hamilton validator against this project for details.",
        )

    board_issues = _Issues()
    board = _load_json(
        aph / "state" / "tasks.json", board_issues, "state/tasks.json"
    )
    if board_issues.errors:
        first = board_issues.errors[0]
        raise StatusError(
            first.path,
            first.message,
            first.remediation or STATUS_BOARD_REMEDIATION,
        )
    tasks = _status_tasks(board)

    settings = _parse_settings(aph / "settings.yaml", _Issues())
    visibility = settings.get("visibility")
    project = hamilton.get("project")
    phase = hamilton.get("phase")
    schema_version = hamilton.get("schema_version")
    protocol_version = hamilton.get("protocol_version")
    return ProjectSummary(
        project if isinstance(project, str) and project else resolved.name,
        phase if isinstance(phase, str) and phase else "unknown",
        schema_version
        if isinstance(schema_version, int) and not isinstance(schema_version, bool)
        else None,
        protocol_version if isinstance(protocol_version, str) else None,
        visibility if visibility in VISIBILITIES else None,
        tasks,
        tuple(task for task in tasks if task.status == "blocked"),
        _next_actionable(tasks),
        _summarize_repo(resolved, _parse_timestamp(hamilton.get("created"))),
    )


def _markdown_cell(value: object) -> str:
    """Keep one board value inside one table cell, whatever the source text is."""

    return " ".join(str(value).split()).replace("|", r"\|")


def _status_stamp(generated: datetime, ledger_seq: Optional[int]) -> str:
    """The one line a reader (and the validator) use to date the board."""

    return "Generated %s from ledger seq %s." % (
        generated.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "unknown" if ledger_seq is None else ledger_seq,
    )


def _last_ledger_seq(aph: Path) -> Optional[int]:
    """The ledger's last ``seq``; ``None`` when it cannot be read truthfully.

    The single definition of "the ledger's last seq": the writer stamps what
    this returns and ``_validate_status_report`` compares against what this
    returns. Two definitions would let a ledger that is not gap-free make a
    freshly written board look stale.
    """

    try:
        lines = (
            (aph / "ledger" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    except (OSError, UnicodeError):
        return None
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(event, dict):
            return None
        sequence = event.get("seq")
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            return None
        return sequence
    return None


def render_status_markdown(
    summary: ProjectSummary,
    generated: datetime,
    ledger_seq: Optional[int],
) -> str:
    """Render the §5.6 board as Markdown: the stage, and the task list.

    The same narrowed facts the terminal board prints, in the form the advisor
    can open later. Nothing is derived that ``tasks.json`` does not already say.
    """

    lines = [
        "# Hamilton progress — %s" % _markdown_cell(summary.project),
        "",
        "- Phase: %s" % _markdown_cell(summary.phase),
        "- Progress: %d of %d tasks done"
        % (summary.done_count, summary.total_count),
        "",
    ]
    if summary.tasks:
        lines.append("| Task | Status | Title |")
        lines.append("| --- | --- | --- |")
        for task in summary.tasks:
            lines.append(
                "| %s | %s | %s |"
                % (
                    _markdown_cell(task.id),
                    _markdown_cell(task.status),
                    _markdown_cell(task.title),
                )
            )
    else:
        lines.append("No tasks on the board yet.")
    lines.extend(
        ["", _status_stamp(generated, ledger_seq), "", STATUS_REPORT_FOOTER]
    )
    return "\n".join(lines) + "\n"


def write_status_report(
    project_root: Path,
    summary: ProjectSummary,
) -> Path:
    """Regenerate ``.aphelocoma/STATUS.md`` whole and return its path.

    The file is never appended to and never patched in place, so it cannot
    accumulate drift: it is only ever as stale as its last write, and the stamp
    says when that was. The replace is atomic, so a failed write leaves the
    previous board intact rather than a half-rendered one.
    """

    aph = Path(project_root).resolve() / ".aphelocoma"
    target = aph / STATUS_REPORT_FILENAME
    content = render_status_markdown(
        summary,
        datetime.now(timezone.utc),
        _last_ledger_seq(aph),
    )
    try:
        atomic_write_text(target, content)
    except OSError as error:
        raise StatusError(
            ".aphelocoma/%s" % STATUS_REPORT_FILENAME,
            "The Hamilton progress board could not be written to %s: %s."
            % (target, error),
            STATUS_WRITE_REMEDIATION,
        ) from error
    return target


def _migration_kind(project_root: Path) -> str:
    path = project_root / ".aphelocoma" / "hamilton.json"
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MigrationError("Cannot read Hamilton metadata: %s" % error)
    if not isinstance(metadata, dict):
        raise MigrationError("hamilton.json must contain an object")
    schema = metadata.get("schema_version")
    protocol = metadata.get("protocol_version")
    if schema is None and protocol is None:
        return "unversioned-v0.2"
    if schema == CURRENT_SCHEMA_VERSION and protocol == CURRENT_PROTOCOL_VERSION:
        return "current"
    if isinstance(schema, int) and schema > CURRENT_SCHEMA_VERSION:
        raise MigrationError(
            "Project schema version %s is newer than supported version %s; "
            "upgrade Aphelocoma." % (schema, CURRENT_SCHEMA_VERSION)
        )
    parsed = _semver(protocol)
    current = _semver(CURRENT_PROTOCOL_VERSION)
    if parsed is not None and current is not None and parsed > current:
        raise MigrationError(
            "Project protocol version %s is newer than supported version %s; "
            "upgrade Aphelocoma." % (protocol, CURRENT_PROTOCOL_VERSION)
        )
    raise MigrationError(
        "Only unversioned v0.2 Hamilton state can be migrated automatically."
    )


def _git_marker_directory(worktree_root: Path) -> Optional[Path]:
    """Resolve one worktree marker without treating a HEAD file as authority."""

    marker = worktree_root / ".git"
    if marker.is_dir():
        resolved = marker.resolve()
    elif marker.is_file():
        try:
            content = marker.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            return None
        if not content.startswith("gitdir:"):
            return None
        value = content.split(":", 1)[1].strip()
        if not value:
            return None
        raw_path = Path(value)
        if not raw_path.is_absolute():
            raw_path = worktree_root / raw_path
        resolved = raw_path.resolve()
    else:
        return None
    if not resolved.is_dir() or not (resolved / "HEAD").is_file():
        return None
    return resolved


def _git_context_is_authoritative(
    worktree_root: Path, git_directory: Path
) -> bool:
    """Verify Git itself agrees with the marker-derived worktree and gitdir."""

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(worktree_root),
                "rev-parse",
                "--show-toplevel",
                "--absolute-git-dir",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if completed.returncode != 0:
        return False
    try:
        lines = completed.stdout.decode(
            "utf-8", "surrogateescape"
        ).splitlines()
    except (AttributeError, UnicodeError):
        return False
    if len(lines) != 2:
        return False
    try:
        reported_worktree = Path(lines[0]).resolve()
        reported_gitdir = Path(lines[1]).resolve()
    except (OSError, RuntimeError):
        return False
    return (
        reported_worktree == worktree_root.resolve()
        and reported_gitdir == git_directory.resolve()
    )


def _git_contexts(
    project_root: Path,
) -> Optional[List[Tuple[Path, Path]]]:
    """Return all authoritative enclosing Git contexts, nearest first.

    ``None`` means at least one marker exists but cannot be authoritatively
    resolved. An empty list means no enclosing Git marker exists.
    """

    contexts: List[Tuple[Path, Path]] = []
    current = project_root.resolve()
    while True:
        marker = current / ".git"
        if marker.exists() or marker.is_symlink():
            git_directory = _git_marker_directory(current)
            if git_directory is None or not _git_context_is_authoritative(
                current, git_directory
            ):
                return None
            contexts.append((current, git_directory))
        if current.parent == current:
            return contexts
        current = current.parent


def _git_context(project_root: Path) -> Optional[Tuple[Path, Path]]:
    """Return the nearest authoritative context, preserving the private API."""

    contexts = _git_contexts(project_root)
    return contexts[0] if contexts else None


def _backup_path(project_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    contexts = _git_contexts(project_root)
    if contexts is None:
        raise MigrationError(
            "Git context could not be determined; refusing migration before "
            "creating a backup. Repair the nearest `.git` marker and retry."
        )
    if contexts:
        git_directory = contexts[0][1].resolve()
        backup_root = git_directory / "aphelocoma-backups"
        if backup_root.is_symlink():
            raise MigrationError(
                "Refusing migration because the Git backup path is symlinked."
            )
        try:
            backup_root.mkdir(exist_ok=True)
        except OSError as error:
            raise MigrationError(
                "Git backup directory could not be created safely: %s" % error
            ) from error
        if backup_root.is_symlink():
            raise MigrationError(
                "Refusing migration because the Git backup path is symlinked."
            )
        try:
            resolved_backup_root = backup_root.resolve(strict=True)
            resolved_backup_root.relative_to(git_directory)
        except (OSError, RuntimeError, ValueError) as error:
            raise MigrationError(
                "Git backup path escapes the authoritative Git directory."
            ) from error
        if resolved_backup_root != backup_root:
            raise MigrationError(
                "Refusing migration because the Git backup path contains "
                "symlinked components."
            )
        base = backup_root / ("v0.2-%s" % stamp)
    else:
        base = project_root / (".aphelocoma.backup-v0.2-%s" % stamp)
    candidate = base
    counter = 1
    while candidate.exists() or candidate.is_symlink():
        if candidate.is_symlink():
            raise MigrationError(
                "Refusing migration because a backup candidate is symlinked."
            )
        candidate = base.parent / ("%s-%d" % (base.name, counter))
        counter += 1
    if contexts:
        try:
            candidate.resolve(strict=False).relative_to(git_directory)
        except (OSError, RuntimeError, ValueError) as error:
            raise MigrationError(
                "Git backup candidate escapes the authoritative Git directory."
            ) from error
    return candidate


def _reject_tree_symlinks(root: Path) -> None:
    """Fail closed if any entry below ``root`` is a symbolic link."""

    pending = [root]
    try:
        while pending:
            directory = pending.pop()
            with os.scandir(str(directory)) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink():
                    relative = path.relative_to(root).as_posix()
                    raise MigrationError(
                        "Refusing migration because `.aphelocoma/%s` is a "
                        "symbolic link." % relative
                    )
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
    except OSError as error:
        raise MigrationError(
            "Could not safely inspect Hamilton state for symbolic links: %s"
            % error
        ) from error


def _append_setting(text: str, key: str, value: str) -> str:
    pattern = re.compile(r"(?m)^%s\s*:" % re.escape(key))
    if pattern.search(text):
        return text
    prefix = "%s: %s\n" % (key, value)
    return prefix + text.lstrip("\n")


def _migrate_staging(staging: Path) -> None:
    hamilton_path = staging / "hamilton.json"
    metadata = json.loads(hamilton_path.read_text(encoding="utf-8"))
    migrated: Dict[str, object] = {}
    for key, value in metadata.items():
        migrated[key] = value
        if key == "project":
            migrated["schema_version"] = CURRENT_SCHEMA_VERSION
            migrated["protocol_version"] = CURRENT_PROTOCOL_VERSION
    if "schema_version" not in migrated:
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
        migrated["protocol_version"] = CURRENT_PROTOCOL_VERSION
    settings_path = staging / "settings.yaml"
    try:
        settings = settings_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        settings = ""
    settings = _append_setting(settings, "redact_sensitive", "true")
    settings = _append_setting(settings, "visibility", "tracked")
    atomic_write_text(settings_path, settings)

    ignore_path = staging / ".gitignore"
    try:
        ignore_lines = ignore_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        ignore_lines = []
    for rule in ("dispatch/", "*.tmp", "*.bak", "*.log"):
        if rule not in ignore_lines:
            ignore_lines.append(rule)
    atomic_write_text(ignore_path, "\n".join(ignore_lines) + "\n")

    tasks_path = staging / "state" / "tasks.json"
    board = json.loads(tasks_path.read_text(encoding="utf-8"))
    missing_dependency_field = object()
    for task in board.get("tasks", []):
        if isinstance(task, dict):
            legacy_dependencies = task.pop(
                "depends_on",
                missing_dependency_field,
            )
            current_dependencies = task.get(
                "dependencies",
                missing_dependency_field,
            )
            if (
                legacy_dependencies is not missing_dependency_field
                and current_dependencies is not missing_dependency_field
                and legacy_dependencies != current_dependencies
            ):
                raise ValueError(
                    "Task %s has conflicting depends_on and dependencies."
                    % task.get("id")
                )
            if current_dependencies is missing_dependency_field:
                task["dependencies"] = (
                    []
                    if legacy_dependencies is missing_dependency_field
                    or legacy_dependencies is None
                    else legacy_dependencies
                )
    atomic_write_json(tasks_path, board)

    events_path = staging / "ledger" / "events.jsonl"
    event_lines = events_path.read_text(encoding="utf-8").splitlines()
    events: List[object] = []
    for line in event_lines:
        if not line.strip():
            continue
        event = json.loads(line)
        if isinstance(event, dict):
            event.setdefault("task", None)
            event.setdefault("to", None)
        events.append(event)
    through_seq = (
        events[-1].get("seq")
        if events and isinstance(events[-1], dict)
        else 0
    )
    digest_events = [
        event for event in events if isinstance(event, dict)
    ]
    prefix_digest = _event_prefix_digest(
        digest_events,
        through_seq if isinstance(through_seq, int) else 0,
    )
    task_states = [
        {"id": task.get("id"), "status": task.get("status")}
        for task in board.get("tasks", [])
        if isinstance(task, dict)
    ]
    task_states_digest = _task_states_digest(task_states)
    migrated["history_baseline"] = {
        "source": LEGACY_HISTORY_SOURCE,
        "through_seq": through_seq,
        "prefix_digest": prefix_digest,
        "task_states_digest": task_states_digest,
        "task_states": task_states,
    }
    marker_seq = (
        through_seq + 1
        if isinstance(through_seq, int)
        and not isinstance(through_seq, bool)
        else 1
    )
    events.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "seq": marker_seq,
            "event": "migration_baseline",
            "actor": "orchestrator",
            "task": None,
            "to": None,
            "note": _migration_marker_note(
                through_seq if isinstance(through_seq, int) else 0,
                prefix_digest,
                task_states_digest,
            ),
        }
    )
    atomic_write_text(
        events_path,
        "".join(
            json.dumps(event, separators=(",", ":")) + "\n"
            for event in events
        ),
    )
    atomic_write_json(hamilton_path, migrated)


def migrate_project(
    project_root: Path,
    *,
    apply: bool,
    inject_failure: Optional[str] = None,
) -> MigrationResult:
    """Check or transactionally migrate unversioned Hamilton v0.2 state.

    Migration operates on a staging copy. The original is not renamed until the
    staged state validates, and a persistent byte-for-byte backup is retained.
    """

    root = Path(project_root).resolve()
    aph = root / ".aphelocoma"
    if not aph.is_dir():
        raise MigrationError("No .aphelocoma project state exists in %s." % root)
    if aph.is_symlink():
        raise MigrationError(
            "Refusing to migrate a symlinked .aphelocoma directory."
        )
    _reject_tree_symlinks(aph)
    kind = _migration_kind(root)
    if kind == "current":
        return MigrationResult(
            "current", root, None, "Hamilton project state is already current."
        )
    if not apply:
        return MigrationResult(
            "migration_required",
            root,
            None,
            "Migration required for unversioned Hamilton v0.2 state.",
        )

    backup = _backup_path(root)
    staging = root / (".aphelocoma.migrate-%s" % uuid.uuid4().hex)
    retired = root / (".aphelocoma.original-%s" % uuid.uuid4().hex)
    original_moved = False
    try:
        shutil.copytree(aph, backup, symlinks=True)
        if inject_failure == "after_backup":
            raise RuntimeError("injected failure after backup")
        shutil.copytree(aph, staging, symlinks=True)
        _reject_tree_symlinks(staging)
        _migrate_staging(staging)
        if inject_failure == "after_write":
            raise RuntimeError("injected failure after staged write")

        validation_root = root / (".aphelocoma.validate-%s" % uuid.uuid4().hex)
        try:
            validation_root.mkdir()
            os.replace(str(staging), str(validation_root / ".aphelocoma"))
            report = validate_project(validation_root, tracked_files=[])
            os.replace(str(validation_root / ".aphelocoma"), str(staging))
        finally:
            if validation_root.exists():
                shutil.rmtree(validation_root)
        if not report.ok:
            detail = "; ".join(issue.message for issue in report.errors[:3])
            raise RuntimeError("migrated state failed validation: %s" % detail)
        if inject_failure == "after_validate":
            raise RuntimeError("injected failure after validation")

        os.replace(str(aph), str(retired))
        original_moved = True
        try:
            os.replace(str(staging), str(aph))
        except Exception:
            os.replace(str(retired), str(aph))
            original_moved = False
            raise
        report = validate_project(root)
        if not report.ok:
            detail = "; ".join(issue.message for issue in report.errors[:3])
            raise RuntimeError(
                "migrated project failed post-swap validation: %s" % detail
            )
        if inject_failure == "after_swap":
            raise RuntimeError("injected failure after swap")
        shutil.rmtree(retired)
        original_moved = False
    except Exception as error:
        if original_moved and retired.exists():
            if aph.exists():
                if staging.exists():
                    shutil.rmtree(staging)
                os.replace(str(aph), str(staging))
            os.replace(str(retired), str(aph))
            original_moved = False
        if staging.exists():
            shutil.rmtree(staging)
        if retired.exists():
            shutil.rmtree(retired)
        raise MigrationError(
            "Migration failed; original state was preserved: %s" % error,
            backup=backup if backup.exists() else None,
        ) from error

    return MigrationResult(
        "migrated",
        root,
        backup,
        "Migrated Hamilton v0.2 state to schema %s / protocol %s."
        % (CURRENT_SCHEMA_VERSION, CURRENT_PROTOCOL_VERSION),
    )


def _doctor_issue_summary(
    report: ValidationReport, codes: Set[str]
) -> Tuple[List[ValidationIssue], List[ValidationIssue]]:
    errors = [issue for issue in report.errors if issue.code in codes]
    warnings = [issue for issue in report.warnings if issue.code in codes]
    return errors, warnings


def register_doctor_checks(registry: object) -> None:
    """Register T2 diagnostics through T1's extension seam."""

    from .doctor import Diagnostic

    def no_state(check_id: str, context: object) -> Optional[Diagnostic]:
        cwd = Path(getattr(context, "cwd"))
        if not (cwd / ".aphelocoma").is_dir():
            return Diagnostic(
                check_id,
                "ok",
                "No Hamilton project state is present in the current directory.",
                None,
            )
        return None

    def version_check(context: object) -> Diagnostic:
        absent = no_state("hamilton-project-version", context)
        if absent is not None:
            return absent
        report = validate_project(Path(getattr(context, "cwd")))
        errors, _ = _doctor_issue_summary(report, VERSION_CODES)
        if errors:
            return Diagnostic(
                "hamilton-project-version",
                "error",
                errors[0].message,
                errors[0].remediation,
            )
        return Diagnostic(
            "hamilton-project-version",
            "ok",
            "Hamilton project schema %s and protocol %s are supported."
            % (CURRENT_SCHEMA_VERSION, CURRENT_PROTOCOL_VERSION),
            None,
        )

    def integrity_check(context: object) -> Diagnostic:
        absent = no_state("hamilton-project-integrity", context)
        if absent is not None:
            return absent
        report = validate_project(Path(getattr(context, "cwd")))
        errors = [
            issue
            for issue in report.errors
            if issue.code not in VERSION_CODES | PRIVACY_CODES
        ]
        if errors:
            return Diagnostic(
                "hamilton-project-integrity",
                "error",
                "%d Hamilton integrity error(s); first: %s"
                % (len(errors), errors[0].message),
                errors[0].remediation
                or "Run the Hamilton validator for details and append corrective events.",
            )
        return Diagnostic(
            "hamilton-project-integrity",
            "ok",
            "Hamilton project ledger and task state are internally consistent.",
            None,
        )

    def privacy_check(context: object) -> Diagnostic:
        absent = no_state("hamilton-project-privacy", context)
        if absent is not None:
            return absent
        report = validate_project(Path(getattr(context, "cwd")))
        errors, _ = _doctor_issue_summary(report, PRIVACY_CODES)
        if errors:
            return Diagnostic(
                "hamilton-project-privacy",
                "error",
                "%d Hamilton privacy error(s); first: %s"
                % (len(errors), errors[0].message),
                errors[0].remediation,
            )
        return Diagnostic(
            "hamilton-project-privacy",
            "ok",
            "Hamilton visibility, transient dispatch policy, and secret scan pass.",
            None,
        )

    register = getattr(registry, "register")
    register("hamilton-project-version", version_check)
    register("hamilton-project-integrity", integrity_check)
    register("hamilton-project-privacy", privacy_check)
