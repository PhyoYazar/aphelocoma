"""Detection and conservative cleanup for pre-v0.3 global artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
from typing import Dict, List, Set, Tuple

from .io import atomic_write_text
from .manifest import (
    ManifestError,
    first_symlink_component,
    is_within_resolved,
    paths_overlap_resolved,
)
from .paths import RuntimePaths


LEGACY_FILE_SIGNATURES = {
    (".claude", "agents", "architect.md"): (
        "5115301f10a6644722f1626417827be3d87bcaa212bf4b90103943a77e67e4a8",
    ),
    (".claude", "agents", "reviewer.md"): (
        "12ce14ee67db1a81f672a5eddbad7e6529bdc8e3bb8961e57f1c8cf556dd8cf0",
    ),
    (".claude", "CLAUDE.md"): (
        "fa1120e66e111b995d8dc2f3d0cbc7629380aeedc8d3bcfa55fe2b8326405b4d",
    ),
    (".claude", "settings.json"): (
        "42779411a0c19966c717273d9dd0e2a0dafe03a3b756b4b0aec0091e71f7f3c4",
    ),
    (".codex", "AGENTS.md"): (
        "0977f7229653ffc3856d6abcedd93db177d6ec88c3852257c23123b77785a809",
    ),
    (".codex", "hooks.json"): (
        "492a44db5464066c24bbdd88d1ccd5a15c4faf4e290b1314736f8680fbbcb205",
        "44be4c908f27c783beb29212454fc2c0f8240775a19cf1bd465895878ec0231e",
    ),
}
UNIQUE_LEGACY_FILE_PATHS = {
    (".claude", "agents", "architect.md"),
    (".claude", "agents", "reviewer.md"),
}
LEGACY_FILE_MARKERS = {
    (".claude", "CLAUDE.md"): (
        b"Aphelocoma Second Brain",
        b"APHELOCOMA_HOME",
    ),
    (".claude", "settings.json"): (
        b"Remember to run /journal to capture this session.",
    ),
    (".codex", "AGENTS.md"): (
        b"Aphelocoma Second Brain",
        b"APHELOCOMA_HOME",
    ),
    (".codex", "hooks.json"): (
        b"Remember to run /journal to capture this session.",
    ),
}
LEGACY_SKILL_NAMES = (
    "adr",
    "aph-status",
    "auto-sync",
    "capture",
    "deploy",
    "generate-view",
    "journal",
    "knowledge-lookup",
    "project-context",
    "project-init",
    "prompt-architect",
    "reflect",
    "session-end",
    "session-record",
    "sync",
    "ux-guardian",
    "wrap-up",
)
LEGACY_SKILL_BODY_DIGESTS = {
    "adr": ("61b8ea50519218adb5381f3c6b363e57218724e86e6365a3ac8d786178b9b949",),
    "aph-status": ("9b1ba31c88edb55eec08eb360ec1de852ee9d6e314c35df4221142210f80dff0",),
    "auto-sync": ("de6381fdbf9752978869e57164905ad76c3ee2d2c5189566d4b613c0093434c7",),
    "capture": ("0a0c9fb5bd0cf144bfb9b6e7f0eecc62fd3c5959e1a6ac46bfbf6f47aa5fb997",),
    "deploy": (
        "d4d5d586805fb17a83f1be908227e772cd28419572c1c5517b446fdef700662c",
        "df5d4e7a4e8f1b270d5c604e20d93c512cd886edd1f60d3ca3400c8d24b89f43",
    ),
    "generate-view": ("c56503d05e10ed11bab271f36b352e194220c7546eee7bf14527877d4a3ebd2b",),
    "journal": ("1a6523c353b9c922203d4dc7c7f108b885f63ca59b12f013bb3980f566748791",),
    "knowledge-lookup": ("d4c0381fc24fd0649ef44732e7811c667e7e36b188104f3388ed939c958b30d7",),
    "project-context": ("0578d983a7a9c5483ccf9001117fe36ed1a55f1510d944ab7da43ac517dc99a7",),
    "project-init": ("17bdd8a2b8c7115bd29c24bc658a47cf7c458f2be73e9dd63dfda44a5235a05f",),
    "prompt-architect": ("326dce9994102e4466e2fc972aaac399cc30e84b68288c5ce2c4c59400b14e3e",),
    "reflect": ("3b5ac6e7c4e4503a53836c624f96b9a10422c37891241a0ba57c384411cb4a8c",),
    "session-end": ("5b184e87fa53eb0b0608d206402b25678e4bd7c2d4cbbdffe6bd246dd124f8e2",),
    "session-record": ("3d35be6228fcdcc6d879671a62c2f9a9f84f8a5a31a5856818806ed5607aa754",),
    "sync": ("648644891b899b081a3f4d86f8aee27babee8ccd897b91476bb962b9eda0ecb8",),
    "ux-guardian": ("87922ec8d85aa9e8bbf88fa1369fe9bfd1be6387367cdd5887a788ed2e4dd966",),
    "wrap-up": ("a7e758984ad53f64cc159d5dd38b155b36b07045f2ac1cae7a7b125cd40f8160",),
}
LEGACY_SKILL_SUPPORT_DIGESTS = {
    "adr": {
        "templates/adr.md": "0433d75cd909055d6b7b7b0fb31ec00ece8911235283be8f616fb10f099c06c2",
    },
    "generate-view": {
        "templates/brief.md": "b117f1aeaff8bf613a54d6dbdf88a2cf05be00fe25340343f51aa0e4873d7a67",
        "templates/full.md": "6255a35f525a8b80c5319d391bc30e75d527607d50439d4128381837cf7bed78",
    },
    "journal": {
        "templates/entry.md": "d7fdb1e4f5a382008cf0ed7f61d9e4ecddd0f53ef3382f7c7f8ab2dd5d4602c3",
    },
    "project-init": {
        "templates/context.md": "6e81f4d39d804a96a6b3647f98e9edfc9a3532e8df37cd03e11bc8a10bf2dd86",
        "templates/tasks.md": "3b79ea9627ad20c1a56cf7c653167a447aa63fc36650526687d4c14486d4807e",
    },
    "session-record": {
        "templates/record.md": "16fdfd720c3f8a213e91bd912203f12ba465e80d26246886caada35be06b8733",
    },
    "ux-guardian": {
        "references/framework-discovery.md": "c7bce342952561c8603e926e54494e987547decaeff77462b59ac1f01ce3fdfb",
        "references/principles.md": "aae0df942c1c1261f4cd5d00260735d1d9a4dcea8358e946787f90261c51d4ee",
        "templates/review.md": "c6fd421aef66c9a1009587a368d97c58b430f62245290d7e7aeea499847f8640",
    },
}
LEGACY_SKILL_METADATA = {
    "adr": ("Create a numbered Architecture Decision Record for a project.", "manual", "<project> <title>"),
    "aph-status": ("Dashboard showing projects, knowledge files, journal activity, and open threads across the second brain.", "manual", None),
    "auto-sync": ("Proactively sync project context as you work", "background", None),
    "capture": ("Distill insights from journal entries or conversation into reusable knowledge files.", "manual", "[topic]"),
    "deploy": ("Deploy aphelocoma skills and context to AI tool configs (Claude Code, Cursor).", "manual", "[claude|cursor]"),
    "generate-view": ("Generate a context summary for web AI tools (Claude.ai, ChatGPT, Gemini) — paste-ready.", "manual", "[full|brief|project <name>]"),
    "journal": ("Capture an end-of-session work journal entry with accomplishments, decisions, and open threads.", "manual", None),
    "knowledge-lookup": ("Silently surfaces relevant knowledge base entries when the user asks about topics that match stored expertise.", "background", None),
    "project-context": ("Silently loads project context (architecture, tasks, decisions, recent work) when working in a known project directory.", "background", None),
    "project-init": ("Bootstrap a new project record in aphelocoma with context, tasks, and ADR directory.", "manual", "<name>"),
    "prompt-architect": ("Transform vague, broken, incomplete, or complex user requests into clear prompts, system prompts, or reusable prompt packages for other AI agents. Use when the user asks to rewrite a prompt, improve a prompt, create a system prompt, clarify intent, or architect instructions for another AI.", "manual", None),
    "reflect": ("End-of-session review that proposes knowledge captures from recent journal entries and work.", "manual", None),
    "session-end": ("Journal and sync at the end of a work session", "background", None),
    "session-record": ("Capture a structured session record with reasoning chains, findings, and outcomes", "manual", None),
    "sync": ("Sync current project with aphelocoma — checks for gaps in registry, tasks, context, ADRs, and proposes fixes one by one.", "manual", None),
    "ux-guardian": ("Senior product designer ensuring quality UX — reviews codebases and guides frontend development", "background", None),
    "wrap-up": ("One-command session wrap-up — analyzes changes and runs needed recording steps", "manual", None),
}
LEGACY_PATH_LINE = 'export PATH="$HOME/.aphelocoma/tool/bin:$PATH"'


@dataclass(frozen=True)
class LegacyArtifact:
    path: Path
    exact: bool
    kind: str


@dataclass(frozen=True)
class LegacyReport:
    protected_data: Tuple[Path, ...]
    artifacts: Tuple[LegacyArtifact, ...]
    safety_issues: Tuple[str, ...] = ()
    path_markers: Tuple[Path, ...] = ()


@dataclass(frozen=True)
class LegacyCleanupResult:
    ok: bool
    messages: Tuple[str, ...]


def _raw_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_scalar(value: str) -> str:
    stripped = value.strip()
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in ("'", '"')
    ):
        return stripped[1:-1]
    return stripped


def _skill_document_is_proven(path: Path, name: str) -> bool:
    data = path.read_bytes()
    body_digests = set(LEGACY_SKILL_BODY_DIGESTS[name])
    if hashlib.sha256(data).hexdigest() in body_digests:
        return True
    if not data.startswith(b"---\n"):
        return False
    frontmatter, separator, body = data[4:].partition(b"\n---\n\n")
    if not separator or hashlib.sha256(body).hexdigest() not in body_digests:
        return False
    try:
        lines = frontmatter.decode("utf-8").splitlines()
    except UnicodeError:
        return False
    fields: Dict[str, str] = {}
    for line in lines:
        key, separator, value = line.partition(":")
        if not separator or not key or key in fields:
            return False
        fields[key] = _normalized_scalar(value)
    description, skill_type, argument_hint = LEGACY_SKILL_METADATA[name]
    expected_required = {
        "name": name,
        "description": description,
        (
            "disable-model-invocation"
            if skill_type == "manual"
            else "user-invocable"
        ): "true" if skill_type == "manual" else "false",
    }
    for key, expected in expected_required.items():
        if fields.get(key) != expected:
            if not (
                name == "ux-guardian"
                and key == "user-invocable"
                and fields.get(key) == "true"
            ):
                return False
    allowed = set(expected_required)
    if argument_hint is not None:
        allowed.add("argument-hint")
        if (
            "argument-hint" in fields
            and fields["argument-hint"] != argument_hint
        ):
            return False
    return set(fields).issubset(allowed)


def _expected_support_directories(files: Set[str]) -> Set[str]:
    directories: Set[str] = set()
    for relative in files:
        parent = Path(relative).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def _skill_tree_is_proven(path: Path, name: str) -> bool:
    if path.is_symlink() or not path.is_dir():
        return False
    support = LEGACY_SKILL_SUPPORT_DIGESTS.get(name, {})
    expected_files = {"SKILL.md", *support}
    expected_directories = _expected_support_directories(set(support))
    actual_files: Set[str] = set()
    actual_directories: Set[str] = set()
    for child in path.rglob("*"):
        relative = child.relative_to(path).as_posix()
        if child.is_symlink():
            return False
        if child.is_file():
            actual_files.add(relative)
        elif child.is_dir():
            actual_directories.add(relative)
        else:
            return False
    if actual_files != expected_files or actual_directories != expected_directories:
        return False
    if not _skill_document_is_proven(path / "SKILL.md", name):
        return False
    return all(
        _raw_digest(path / relative) == expected_digest
        for relative, expected_digest in support.items()
    )


def _legacy_safety_issues(paths: RuntimePaths) -> Tuple[str, ...]:
    issues: List[str] = []
    if any(
        is_within_resolved(paths.root, protected)
        for protected in paths.protected_legacy_paths
    ):
        issues.append(
            f"Active root {paths.root} overlaps protected legacy data; "
            "legacy cleanup was refused."
        )
    current = paths.root
    while not current.exists() and not current.is_symlink():
        if current.parent == current:
            break
        current = current.parent
    if current.is_symlink():
        issues.append(
            f"Active root uses symlinked path component {current}; "
            "legacy cleanup was refused."
        )
    mutation_targets = [
        paths.home.joinpath(*relative)
        for relative in LEGACY_FILE_SIGNATURES
    ]
    mutation_targets.extend(
        paths.home / tool_home / "skills" / name
        for tool_home in (".claude", ".codex")
        for name in LEGACY_SKILL_NAMES
    )
    mutation_targets.extend(
        paths.home / shell_name
        for shell_name in (".zshrc", ".bashrc", ".bash_profile")
    )
    for candidate in mutation_targets:
        if any(
            paths_overlap_resolved(candidate, protected)
            for protected in paths.protected_legacy_paths
        ):
            issues.append(
                f"Legacy cleanup target overlaps protected legacy data: {candidate}."
            )
    for tool_home in (".claude", ".codex"):
        host = paths.home / tool_home
        for candidate in (host, host / "agents", host / "skills"):
            try:
                symlink = first_symlink_component(candidate, paths.home)
            except ManifestError as error:
                issues.append(str(error))
                break
            if symlink is not None:
                issues.append(
                    f"Legacy cleanup host path uses a symlink: {symlink}."
                )
                break
    for candidate in mutation_targets:
        try:
            symlink = first_symlink_component(candidate, paths.home)
        except ManifestError as error:
            issues.append(str(error))
            continue
        if symlink is not None:
            issues.append(
                f"Legacy cleanup target uses a symlink: {symlink}."
            )
    return tuple(dict.fromkeys(issues))


def inspect_legacy(paths: RuntimePaths) -> LegacyReport:
    """Inspect locations, never contents, under protected legacy data paths."""

    protected = tuple(
        location
        for location in paths.protected_legacy_paths
        if location.exists()
    )
    safety_issues = _legacy_safety_issues(paths)
    if safety_issues:
        return LegacyReport(protected, (), safety_issues)
    artifacts: List[LegacyArtifact] = []
    for relative, expected_digests in LEGACY_FILE_SIGNATURES.items():
        path = paths.home.joinpath(*relative)
        if path.is_symlink():
            if relative in UNIQUE_LEGACY_FILE_PATHS:
                artifacts.append(LegacyArtifact(path, False, "file"))
        elif path.is_file():
            exact = _raw_digest(path) in expected_digests
            markers = LEGACY_FILE_MARKERS.get(relative)
            recognizable = markers is not None and all(
                marker in path.read_bytes() for marker in markers
            )
            if exact or relative in UNIQUE_LEGACY_FILE_PATHS or recognizable:
                artifacts.append(LegacyArtifact(path, exact, "file"))
    for tool_home in (".claude", ".codex"):
        skill_root = paths.home / tool_home / "skills"
        for name in LEGACY_SKILL_NAMES:
            path = skill_root / name
            if path.exists() or path.is_symlink():
                artifacts.append(
                    LegacyArtifact(
                        path,
                        _skill_tree_is_proven(path, name),
                        "skill",
                    )
                )
    path_markers = []
    for shell_name in (".zshrc", ".bashrc", ".bash_profile"):
        shell_rc = paths.home / shell_name
        if shell_rc.is_symlink() or not shell_rc.is_file():
            continue
        try:
            lines = shell_rc.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        if LEGACY_PATH_LINE in lines:
            path_markers.append(shell_rc)
    return LegacyReport(
        protected,
        tuple(artifacts),
        (),
        tuple(path_markers),
    )


def _cleanup_old_path_line(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    changed = False
    kept = []
    for line in lines:
        if line == LEGACY_PATH_LINE:
            if kept and kept[-1] == "# Aphelocoma":
                kept.pop()
            changed = True
            continue
        kept.append(line)
    if changed:
        updated = "\n".join(kept)
        if content.endswith("\n") and updated:
            updated += "\n"
        atomic_write_text(path, updated)
    return changed


def cleanup_legacy_artifacts(paths: RuntimePaths) -> LegacyCleanupResult:
    """Remove only byte-exact legacy files; preserve every ambiguous artifact."""

    report = inspect_legacy(paths)
    if report.safety_issues:
        return LegacyCleanupResult(False, report.safety_issues)
    messages: List[str] = []
    ok = True
    for artifact in report.artifacts:
        if artifact.exact:
            if artifact.kind == "skill":
                shutil.rmtree(artifact.path)
            else:
                artifact.path.unlink()
            messages.append(f"Removed exact legacy artifact {artifact.path}.")
        else:
            ok = False
            messages.append(
                f"Modified or ambiguous legacy artifact preserved at {artifact.path}."
            )
    for shell_name in (".zshrc", ".bashrc", ".bash_profile"):
        shell_rc = paths.home / shell_name
        if _cleanup_old_path_line(shell_rc):
            messages.append(f"Removed exact v0.2 PATH line from {shell_rc}.")
    if report.protected_data:
        messages.append(
            "Protected legacy data left untouched: "
            + ", ".join(str(path) for path in report.protected_data)
            + "."
        )
    return LegacyCleanupResult(ok, tuple(messages))
