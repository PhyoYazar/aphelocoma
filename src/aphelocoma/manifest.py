"""Deployment manifest, digest, and managed-block primitives."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Dict, Optional, Tuple

from .io import atomic_write_json


MANIFEST_SCHEMA_VERSION = 1
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(RuntimeError):
    """A deployment manifest or managed block is unsafe to interpret."""


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_path(path: Path) -> str:
    """Return a deterministic SHA-256 for a file, symlink, or directory tree."""

    target = Path(path)
    if target.is_symlink():
        payload = ("symlink\0" + os.readlink(str(target))).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
    if target.is_file():
        digest = hashlib.sha256()
        digest.update(b"file\0")
        digest.update(bytes.fromhex(_hash_file(target)))
        return digest.hexdigest()
    if target.is_dir():
        digest = hashlib.sha256()
        digest.update(b"tree\0")
        children = (
            child
            for child in target.rglob("*")
            if "__pycache__" not in child.relative_to(target).parts
            and child.suffix != ".pyc"
        )
        for child in sorted(children, key=lambda item: item.as_posix()):
            relative = child.relative_to(target).as_posix().encode("utf-8")
            if child.is_symlink():
                kind = b"link"
                child_digest = hashlib.sha256(
                    os.readlink(str(child)).encode("utf-8")
                ).digest()
            elif child.is_file():
                kind = b"file"
                child_digest = bytes.fromhex(_hash_file(child))
            elif child.is_dir():
                kind = b"dir"
                child_digest = b""
            else:
                kind = b"other"
                child_digest = b""
            digest.update(kind + b"\0" + relative + b"\0" + child_digest)
        return digest.hexdigest()
    raise FileNotFoundError(str(target))


def digest_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def manifest_path(root: Path, tool: str) -> Path:
    return Path(root) / "manifests" / f"{tool}.json"


def resolved_path(path: Path) -> Path:
    """Resolve existing symlinks while retaining nonexistent trailing components."""

    try:
        return Path(path).resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ManifestError(f"Cannot safely resolve path {path}: {error}") from error


def is_within_resolved(candidate: Path, boundary: Path) -> bool:
    try:
        resolved_path(candidate).relative_to(resolved_path(boundary))
    except ValueError:
        return False
    return True


def paths_overlap_resolved(left: Path, right: Path) -> bool:
    """Return whether either resolved path contains the other."""

    return is_within_resolved(left, right) or is_within_resolved(right, left)


def first_symlink_component(path: Path, anchor: Path) -> Optional[Path]:
    """Return the first symlink from anchor's children through path."""

    target = Path(os.path.abspath(os.path.normpath(str(path))))
    base = Path(os.path.abspath(os.path.normpath(str(anchor))))
    try:
        relative = target.relative_to(base)
    except ValueError as error:
        raise ManifestError(f"Path {target} is outside safety anchor {base}.") from error
    current = base
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            return current
    return None


def _validate_absolute_path(value: object, label: str) -> None:
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ManifestError(f"{label} must be an absolute path.")


def validate_manifest(value: object, expected_tool: Optional[str] = None) -> Dict[str, object]:
    if not isinstance(value, dict):
        raise ManifestError("Deployment manifest must be a JSON object.")
    if value.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ManifestError(
            "Unsupported deployment manifest schema; redeploy with this Aphelocoma version."
        )
    tool = value.get("tool")
    if tool not in ("claude", "codex"):
        raise ManifestError("Deployment manifest has an invalid tool.")
    if expected_tool is not None and tool != expected_tool:
        raise ManifestError(
            f"Deployment manifest is for {tool}, expected {expected_tool}."
        )
    if value.get("state") not in ("complete", "partial"):
        raise ManifestError("Deployment manifest has an invalid ownership state.")
    artifacts = value.get("artifacts")
    blocks = value.get("managed_blocks")
    collisions = value.get("collisions")
    if (
        not isinstance(artifacts, list)
        or not isinstance(blocks, list)
        or not isinstance(collisions, list)
    ):
        raise ManifestError(
            "Deployment manifest requires artifacts, managed_blocks, and collisions arrays."
        )
    seen = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ManifestError(f"artifacts[{index}] must be an object.")
        _validate_absolute_path(artifact.get("path"), f"artifacts[{index}].path")
        path = artifact["path"]
        if path in seen:
            raise ManifestError(f"Duplicate artifact path in manifest: {path}.")
        seen.add(path)
        if artifact.get("kind") not in ("file", "tree", "symlink"):
            raise ManifestError(f"artifacts[{index}].kind is invalid.")
        if not isinstance(artifact.get("created"), bool):
            raise ManifestError(f"artifacts[{index}].created must be boolean.")
        if not SHA256_PATTERN.fullmatch(str(artifact.get("digest", ""))):
            raise ManifestError(f"artifacts[{index}].digest is invalid.")
        backup = artifact.get("backup")
        if backup is not None:
            _validate_absolute_path(backup, f"artifacts[{index}].backup")
    block_paths = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ManifestError(f"managed_blocks[{index}] must be an object.")
        _validate_absolute_path(block.get("path"), f"managed_blocks[{index}].path")
        if block["path"] in block_paths:
            raise ManifestError(
                f"Duplicate managed block path in manifest: {block['path']}."
            )
        block_paths.add(block["path"])
        for field in ("start_marker", "end_marker"):
            if not isinstance(block.get(field), str) or not block[field]:
                raise ManifestError(f"managed_blocks[{index}].{field} is invalid.")
        if not SHA256_PATTERN.fullmatch(str(block.get("digest", ""))):
            raise ManifestError(f"managed_blocks[{index}].digest is invalid.")
        if not isinstance(block.get("created"), bool):
            raise ManifestError(f"managed_blocks[{index}].created must be boolean.")
        backup = block.get("backup")
        if backup is not None:
            _validate_absolute_path(backup, f"managed_blocks[{index}].backup")
    collision_paths = set()
    collision_backups = set()
    for index, collision in enumerate(collisions):
        if not isinstance(collision, dict):
            raise ManifestError(f"collisions[{index}] must be an object.")
        _validate_absolute_path(collision.get("path"), f"collisions[{index}].path")
        _validate_absolute_path(
            collision.get("backup"),
            f"collisions[{index}].backup",
        )
        if not SHA256_PATTERN.fullmatch(str(collision.get("digest", ""))):
            raise ManifestError(f"collisions[{index}].digest is invalid.")
        if collision["path"] in collision_paths:
            raise ManifestError(
                f"Duplicate collision target in manifest: {collision['path']}."
            )
        if collision["backup"] in collision_backups:
            raise ManifestError(
                f"Duplicate collision backup in manifest: {collision['backup']}."
            )
        collision_paths.add(collision["path"])
        collision_backups.add(collision["backup"])
    return value


def load_manifest(path: Path, expected_tool: Optional[str] = None) -> Dict[str, object]:
    target = Path(path)
    try:
        with target.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ManifestError(f"Cannot read deployment manifest {target}: {error}") from error
    return validate_manifest(value, expected_tool)


def save_manifest(path: Path, value: Dict[str, object]) -> None:
    validate_manifest(value, str(value.get("tool")))
    atomic_write_json(Path(path), value, mode=0o600)


def locate_managed_block(
    content: str,
    start_marker: str,
    end_marker: str,
) -> Optional[Tuple[int, int, str]]:
    starts = content.count(start_marker)
    ends = content.count(end_marker)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ManifestError(
            f"Managed block markers are ambiguous: {start_marker} / {end_marker}."
        )
    start = content.index(start_marker)
    try:
        end_start = content.index(end_marker, start + len(start_marker))
    except ValueError as error:
        raise ManifestError(
            f"Managed block markers are out of order: {start_marker} / {end_marker}."
        ) from error
    end = end_start + len(end_marker)
    if end < len(content) and content[end] == "\n":
        end += 1
    return start, end, content[start:end]


def put_managed_block(
    content: str,
    block: str,
    start_marker: str,
    end_marker: str,
) -> str:
    if not block.startswith(start_marker) or end_marker not in block:
        raise ManifestError("Generated managed block is missing its boundary markers.")
    normalized = block.rstrip("\n") + "\n"
    located = locate_managed_block(content, start_marker, end_marker)
    if located is None:
        prefix = content.rstrip("\n")
        return prefix + ("\n\n" if prefix else "") + normalized
    start, end, _ = located
    return content[:start] + normalized + content[end:]


def remove_managed_block(
    content: str,
    start_marker: str,
    end_marker: str,
    expected_digest: str,
) -> Tuple[str, bool]:
    located = locate_managed_block(content, start_marker, end_marker)
    if located is None:
        return content, True
    start, end, block = located
    if digest_text(block) != expected_digest:
        return content, False
    before = content[:start].rstrip("\n")
    after = content[end:].lstrip("\n")
    if before and after:
        return before + "\n\n" + after, True
    if before:
        return before + "\n", True
    return after, True
