"""Transactional, ownership-aware Hamilton deployment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple
import uuid

from .doctor import HAMILTON_ROLE_IDS
from .io import atomic_write_text
from .manifest import (
    first_symlink_component,
    ManifestError,
    digest_path,
    digest_text,
    is_within_resolved,
    load_manifest,
    locate_managed_block,
    manifest_path,
    paths_overlap_resolved,
    put_managed_block,
    remove_managed_block,
    save_manifest,
)
from .paths import RuntimePaths


CODEX_BLOCK_START = "# >>> aphelocoma hamilton crew >>>"
CODEX_BLOCK_END = "# <<< aphelocoma hamilton crew <<<"


class DeploymentError(RuntimeError):
    """Deployment could not complete without risking user-owned content."""


@dataclass(frozen=True)
class DeploymentResult:
    ok: bool
    messages: Tuple[str, ...]
    manifest_path: Optional[Path] = None


@dataclass(frozen=True)
class DeploymentInspection:
    ok: bool
    messages: Tuple[str, ...]
    deployed_tools: Tuple[str, ...]
    collision_backups: int


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(str(source)))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def _normalized(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(str(path))))


def _ensure_active_root_is_not_legacy(
    paths: RuntimePaths,
    mutation_targets: Sequence[Path],
) -> None:
    if any(
        is_within_resolved(paths.root, protected)
        for protected in paths.protected_legacy_paths
    ):
        raise DeploymentError(
            f"Active root {paths.root} overlaps protected legacy data; "
            "choose a different APHELOCOMA_ROOT."
        )
    for candidate in mutation_targets:
        if any(
            paths_overlap_resolved(candidate, protected)
            for protected in paths.protected_legacy_paths
        ):
            raise DeploymentError(
                f"Owned deployment path {candidate} overlaps protected legacy data; "
                "choose a different APHELOCOMA_ROOT."
            )
    current = paths.root
    while not current.exists() and not current.is_symlink():
        if current.parent == current:
            break
        current = current.parent
    if current.is_symlink():
        raise DeploymentError(
            f"Active root uses symlinked path component {current}; "
            "choose a direct APHELOCOMA_ROOT."
        )
    for candidate in mutation_targets:
        symlink = first_symlink_component(candidate, paths.root)
        if symlink is not None:
            raise DeploymentError(
                f"Active-root path component is a symlink and was refused: {symlink}."
            )


def _ensure_host_paths_safe(paths: RuntimePaths, tool: str) -> None:
    host = paths.home / (".claude" if tool == "claude" else ".codex")
    mutation_targets = list(_expected_targets(paths, tool))
    if tool == "codex":
        mutation_targets.append(host / "config.toml")
    for candidate in mutation_targets:
        if any(
            paths_overlap_resolved(candidate, protected)
            for protected in paths.protected_legacy_paths
        ):
            raise DeploymentError(
                f"{tool} host path overlaps protected legacy data: {candidate}."
            )
    candidates = [host, host / "skills", host / "agents", *mutation_targets]
    for candidate in candidates:
        symlink = first_symlink_component(candidate, paths.home)
        if symlink is not None:
            raise DeploymentError(
                f"{tool} host path uses a symlink and was preserved: {symlink}."
            )


class _PathTransaction:
    def __init__(self) -> None:
        self._changes: List[Tuple[Path, Optional[Path]]] = []

    def replace_path(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        nonce = uuid.uuid4().hex
        staged = target.parent / f".{target.name}.aphelocoma-new-{nonce}"
        displaced = target.parent / f".{target.name}.aphelocoma-old-{nonce}"
        try:
            _copy_path(source, staged)
        except Exception:
            if staged.exists() or staged.is_symlink():
                _remove_path(staged)
            raise
        had_target = target.exists() or target.is_symlink()
        if had_target:
            os.replace(str(target), str(displaced))
        try:
            os.replace(str(staged), str(target))
        except Exception:
            if displaced.exists() or displaced.is_symlink():
                os.replace(str(displaced), str(target))
            _remove_path(staged)
            raise
        self._changes.append((target, displaced if had_target else None))

    def replace_text(self, content: str, target: Path, mode: int = 0o600) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        nonce = uuid.uuid4().hex
        staged = target.parent / f".{target.name}.aphelocoma-new-{nonce}"
        atomic_write_text(staged, content, mode=mode)
        self.replace_path(staged, target)
        if staged.exists() or staged.is_symlink():
            _remove_path(staged)

    def rollback(self) -> None:
        for target, displaced in reversed(self._changes):
            if target.exists() or target.is_symlink():
                _remove_path(target)
            if displaced is not None and (displaced.exists() or displaced.is_symlink()):
                os.replace(str(displaced), str(target))
        self._changes.clear()

    def commit(self) -> None:
        changes = self._changes
        self._changes = []
        for _, displaced in changes:
            if displaced is not None and (displaced.exists() or displaced.is_symlink()):
                try:
                    _remove_path(displaced)
                except OSError:
                    pass


def _metadata_value(path: Path, key: str) -> Optional[str]:
    prefix = key + ":"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _build_skill(source_root: Path, destination: Path) -> None:
    source = source_root / "skills" / "aph-hamilton"
    metadata = source / "metadata.yaml"
    body = (source / "skill.md").read_text(encoding="utf-8")
    name = _metadata_value(metadata, "name") or "aph-hamilton"
    description = _metadata_value(metadata, "description") or "Run Hamilton."
    argument_hint = _metadata_value(metadata, "arguments")
    disable = _metadata_value(metadata, "disable-model-invocation") or "true"
    frontmatter = [
        "---",
        f"name: {name}",
        f"description: {description}",
    ]
    if argument_hint:
        frontmatter.append(f"argument-hint: {argument_hint}")
    frontmatter.extend(
        [
            f"disable-model-invocation: {disable}",
            "---",
            "",
        ]
    )
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text(
        "\n".join(frontmatter) + body.rstrip("\n") + "\n",
        encoding="utf-8",
    )
    for name in ("references", "templates", "examples"):
        shutil.copytree(
            source / name,
            destination / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )


def _run_generator(
    script: Path,
    arguments: Sequence[Path],
    *,
    inject_partial_failure: bool = False,
) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if inject_partial_failure:
        environment["APHELOCOMA_FAIL_GENERATOR_AFTER"] = "3"
    completed = subprocess.run(
        [sys.executable, str(script), *map(str, arguments)],
        env=environment,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise DeploymentError(f"Hamilton agent generator failed: {detail}")


def _expected_agent_names(tool: str) -> Tuple[str, ...]:
    suffix = ".md" if tool == "claude" else ".toml"
    return tuple(f"hamilton-{role_id}{suffix}" for role_id in HAMILTON_ROLE_IDS)


def _canonical_codex_block() -> str:
    entries = [
        (
            f"[agents.hamilton-{role_id}]\n"
            f'config_file = "./agents/hamilton-{role_id}.toml"'
        )
        for role_id in sorted(HAMILTON_ROLE_IDS)
    ]
    return (
        CODEX_BLOCK_START
        + "\n"
        + "\n\n".join(entries)
        + "\n"
        + CODEX_BLOCK_END
        + "\n"
    )


def _prepare_assets(
    paths: RuntimePaths,
    tool: str,
    stage: Path,
    fail_at: Optional[str],
) -> Tuple[Path, List[Tuple[Path, Path]], Optional[str]]:
    skill_stage = stage / "skill"
    _build_skill(paths.tool_root, skill_stage)
    references = paths.tool_root / "skills" / "aph-hamilton" / "references"
    inject = fail_at == "during_generator"
    config_block = None
    artifacts: List[Tuple[Path, Path]] = []
    if tool == "claude":
        output = stage / "agents"
        script = (
            paths.tool_root
            / "adapters"
            / "claude-code"
            / "scripts"
            / "gen-hamilton-crew.py"
        )
        _run_generator(script, (references, output), inject_partial_failure=inject)
        expected = set(_expected_agent_names(tool))
        actual = {path.name for path in output.glob("hamilton-*.md")}
        if actual != expected:
            raise DeploymentError(
                "Claude generator output does not match the 27-role Hamilton inventory."
            )
        host = paths.home / ".claude"
        artifacts.append((skill_stage, host / "skills" / "aph-hamilton"))
        artifacts.extend(
            (output / name, host / "agents" / name) for name in sorted(expected)
        )
    else:
        codex_stage = stage / "codex-home"
        script = (
            paths.tool_root
            / "adapters"
            / "codex"
            / "scripts"
            / "gen-hamilton-crew-codex.py"
        )
        _run_generator(script, (references, codex_stage), inject_partial_failure=inject)
        output = codex_stage / "agents"
        expected = set(_expected_agent_names(tool))
        actual = {path.name for path in output.glob("hamilton-*.toml")}
        if actual != expected:
            raise DeploymentError(
                "Codex generator output does not match the 27-role Hamilton inventory."
            )
        generated_config = (codex_stage / "config.toml").read_text(encoding="utf-8")
        located = locate_managed_block(
            generated_config,
            CODEX_BLOCK_START,
            CODEX_BLOCK_END,
        )
        if located is None:
            raise DeploymentError("Codex generator omitted its managed configuration block.")
        config_block = located[2]
        host = paths.home / ".codex"
        artifacts.append((skill_stage, host / "skills" / "aph-hamilton"))
        artifacts.extend(
            (output / name, host / "agents" / name) for name in sorted(expected)
        )
    return skill_stage, artifacts, config_block


def _persistent_backup(
    target: Path,
    backup_root: Path,
    index: int,
) -> Path:
    suffix = target.name or "artifact"
    destination = backup_root / f"{index:03d}-{suffix}"
    _copy_path(target, destination)
    return destination


def _artifact_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    return "tree" if path.is_dir() else "file"


def _read_version(tool_root: Path) -> str:
    version = (tool_root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise DeploymentError("Installed VERSION is empty; reinstall Aphelocoma.")
    return version


def _unowned_codex_block_issue(paths: RuntimePaths) -> Optional[str]:
    config_path = _normalized(paths.home / ".codex" / "config.toml")
    if not config_path.exists() or config_path.is_symlink():
        return None
    try:
        current = config_path.read_text(encoding="utf-8")
        located = locate_managed_block(
            current,
            CODEX_BLOCK_START,
            CODEX_BLOCK_END,
        )
    except ManifestError as error:
        return (
            f"Refusing ambiguous unowned canonical Hamilton markers in "
            f"{config_path}: {error}"
        )
    except (OSError, UnicodeError) as error:
        return f"Cannot safely inspect {config_path} for an unowned block: {error}"
    if located is None:
        return None
    return (
        f"Refusing unowned canonical Hamilton managed block in {config_path}; "
        "move or remove that block before deploying."
    )


def deploy_hamilton(
    paths: RuntimePaths,
    tool: str,
    *,
    fail_at: Optional[str] = None,
) -> DeploymentResult:
    if tool not in ("claude", "codex"):
        raise DeploymentError(f"Unsupported deployment target: {tool}.")
    _ensure_host_paths_safe(paths, tool)
    deployment_manifest = manifest_path(paths.root, tool)
    deployment_id = uuid.uuid4().hex
    stage = paths.root / f".deploy-stage-{uuid.uuid4().hex}"
    backup_root = paths.root / "backups" / tool / deployment_id
    _ensure_active_root_is_not_legacy(
        paths,
        (deployment_manifest, stage, backup_root),
    )
    manifest_symlink = first_symlink_component(deployment_manifest, paths.root)
    if manifest_symlink is not None:
        raise DeploymentError(
            f"Deployment manifest path uses a symlink: {manifest_symlink}."
        )
    old_manifest: Optional[Dict[str, object]] = None
    try:
        old_manifest = load_manifest(deployment_manifest, tool)
        _validate_manifest_scope(paths, tool, old_manifest, require_complete=True)
        _verify_manifest_backups(old_manifest)
    except FileNotFoundError:
        pass

    if tool == "codex" and old_manifest is None:
        unowned_block = _unowned_codex_block_issue(paths)
        if unowned_block is not None:
            raise DeploymentError(unowned_block)

    paths.root.mkdir(parents=True, exist_ok=True)
    stage.mkdir()
    transaction = _PathTransaction()
    try:
        _, prepared, config_block = _prepare_assets(paths, tool, stage, fail_at)
        old_artifacts = {
            artifact["path"]: artifact
            for artifact in (old_manifest or {}).get("artifacts", [])
        }
        artifact_records = []
        collision_records = list((old_manifest or {}).get("collisions", []))
        for index, (source, target) in enumerate(prepared, 1):
            target = _normalized(target)
            old = old_artifacts.get(str(target))
            exists = target.exists() or target.is_symlink()
            if old is not None and exists and digest_path(target) != old["digest"]:
                raise DeploymentError(
                    f"Owned artifact drift at {target}; run aph undeploy {tool} "
                    "or move the modified file before redeploying."
                )
            backup = old.get("backup") if old is not None else None
            created = bool(old.get("created")) if old is not None else not exists
            if old is None and exists:
                backup_root.mkdir(parents=True, exist_ok=True)
                backup_path = _persistent_backup(target, backup_root, index)
                backup = str(backup_path)
                created = False
                collision_records.append(
                    {
                        "path": str(target),
                        "backup": str(backup_path),
                        "digest": digest_path(backup_path),
                    }
                )
            transaction.replace_path(source, target)
            artifact_records.append(
                {
                    "path": str(target),
                    "kind": _artifact_kind(target),
                    "digest": digest_path(target),
                    "created": created,
                    "backup": backup,
                }
            )
            if fail_at == "after_first_artifact" and index == 1:
                raise DeploymentError("injected deploy failure after first artifact")

        managed_blocks = []
        if tool == "codex":
            if config_block is None:
                raise DeploymentError("Codex generator omitted its managed block.")
            config_path = _normalized(paths.home / ".codex" / "config.toml")
            if config_path.is_symlink():
                raise DeploymentError(
                    f"Codex config is a symlink and was preserved: {config_path}."
                )
            existed = config_path.exists() or config_path.is_symlink()
            current = (
                config_path.read_text(encoding="utf-8") if config_path.exists() else ""
            )
            old_blocks = (old_manifest or {}).get("managed_blocks", [])
            old_block = old_blocks[0] if old_blocks else None
            located = locate_managed_block(current, CODEX_BLOCK_START, CODEX_BLOCK_END)
            if old_block is not None:
                if located is None or digest_text(located[2]) != old_block["digest"]:
                    raise DeploymentError(
                        f"Managed block drift in {config_path}; preserve or remove the "
                        "modified block before redeploying."
                    )
            backup = old_block.get("backup") if old_block is not None else None
            created = bool(old_block.get("created")) if old_block is not None else not existed
            if old_block is None and existed:
                backup_root.mkdir(parents=True, exist_ok=True)
                backup_path = _persistent_backup(
                    config_path,
                    backup_root,
                    len(prepared) + 1,
                )
                backup = str(backup_path)
                collision_records.append(
                    {
                        "path": str(config_path),
                        "backup": str(backup_path),
                        "digest": digest_path(backup_path),
                    }
                )
            updated = put_managed_block(
                current,
                config_block,
                CODEX_BLOCK_START,
                CODEX_BLOCK_END,
            )
            transaction.replace_text(updated, config_path)
            installed = locate_managed_block(
                updated,
                CODEX_BLOCK_START,
                CODEX_BLOCK_END,
            )
            if installed is None:
                raise DeploymentError("Codex managed block was not installed.")
            managed_blocks.append(
                {
                    "path": str(config_path),
                    "start_marker": CODEX_BLOCK_START,
                    "end_marker": CODEX_BLOCK_END,
                    "digest": digest_text(installed[2]),
                    "created": created,
                    "backup": backup,
                }
            )

        manifest = {
            "schema_version": 1,
            "tool": tool,
            "state": "complete",
            "aphelocoma_version": _read_version(paths.tool_root),
            "deployment_id": deployment_id,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifact_records,
            "managed_blocks": managed_blocks,
            "collisions": collision_records,
        }
        _validate_manifest_scope(paths, tool, manifest, require_complete=True)
        _verify_manifest_backups(manifest)
        save_manifest(deployment_manifest, manifest)
        transaction.commit()
    except Exception:
        transaction.rollback()
        if backup_root.exists():
            shutil.rmtree(backup_root)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    messages = (
        f"Deployed Hamilton to {tool}.",
        f"Ownership manifest: {deployment_manifest}",
    )
    return DeploymentResult(True, messages, deployment_manifest)


def _expected_targets(paths: RuntimePaths, tool: str) -> Tuple[Path, ...]:
    host = paths.home / (".claude" if tool == "claude" else ".codex")
    skill = host / "skills" / "aph-hamilton"
    agents = host / "agents"
    return (skill,) + tuple(agents / name for name in _expected_agent_names(tool))


def _validate_manifest_scope(
    paths: RuntimePaths,
    tool: str,
    manifest: Dict[str, object],
    *,
    require_complete: bool = False,
) -> None:
    allowed = {_normalized(path) for path in _expected_targets(paths, tool)}
    recorded = {
        _normalized(Path(artifact["path"]))
        for artifact in manifest["artifacts"]
    }
    state = manifest["state"]
    if require_complete and state != "complete":
        raise ManifestError(
            f"{tool} deployment is partial; finish undeploy before redeploying."
        )
    if state == "complete" and recorded != allowed:
        missing = sorted(str(path) for path in allowed - recorded)
        unexpected = sorted(str(path) for path in recorded - allowed)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if unexpected:
            detail.append("unexpected " + ", ".join(unexpected))
        raise ManifestError(
            f"{tool} deployment inventory is incomplete: {'; '.join(detail)}."
        )
    for artifact in manifest["artifacts"]:
        recorded_path = Path(artifact["path"])
        target = _normalized(recorded_path)
        if str(recorded_path) != str(target):
            raise ManifestError(
                f"Manifest artifact path is not canonical: {recorded_path}."
            )
        if target not in allowed:
            raise ManifestError(
                f"Manifest artifact is outside the {tool} Hamilton deployment: {target}."
            )
    expected_config = _normalized(
        paths.home / (".codex" if tool == "codex" else ".claude") / "config.toml"
    )
    expected_block_count = 1 if tool == "codex" else 0
    if state == "complete" and len(manifest["managed_blocks"]) != expected_block_count:
        raise ManifestError(
            f"{tool} deployment managed-block inventory is incomplete."
        )
    for block in manifest["managed_blocks"]:
        recorded_path = Path(block["path"])
        if str(recorded_path) != str(_normalized(recorded_path)):
            raise ManifestError(
                f"Manifest managed-block path is not canonical: {recorded_path}."
            )
        if tool != "codex" or _normalized(recorded_path) != expected_config:
            raise ManifestError(
                f"Manifest managed block is outside the {tool} configuration."
            )
        if (
            block["start_marker"] != CODEX_BLOCK_START
            or block["end_marker"] != CODEX_BLOCK_END
        ):
            raise ManifestError(
                "Manifest managed-block markers are not the canonical "
                "Aphelocoma Hamilton markers."
            )
        if block["digest"] != digest_text(_canonical_codex_block()):
            raise ManifestError(
                "Manifest managed-block digest does not match the canonical "
                "Hamilton crew block."
            )

    owned_records = list(manifest["artifacts"]) + list(manifest["managed_blocks"])
    collision_by_path = {
        _normalized(Path(collision["path"])): collision
        for collision in manifest["collisions"]
    }
    normalized_collision_backups = {
        _normalized(Path(collision["backup"]))
        for collision in manifest["collisions"]
    }
    if len(collision_by_path) != len(manifest["collisions"]):
        raise ManifestError("Deployment collision target paths overlap.")
    if len(normalized_collision_backups) != len(manifest["collisions"]):
        raise ManifestError("Deployment collision backup paths overlap.")
    for collision in manifest["collisions"]:
        if str(Path(collision["path"])) != str(
            _normalized(Path(collision["path"]))
        ):
            raise ManifestError(
                f"Manifest collision target path is not canonical: "
                f"{collision['path']}."
            )
        if str(Path(collision["backup"])) != str(
            _normalized(Path(collision["backup"]))
        ):
            raise ManifestError(
                f"Manifest collision backup path is not canonical: "
                f"{collision['backup']}."
            )
    owned_by_path = {
        _normalized(Path(record["path"])): record
        for record in owned_records
    }
    if len(owned_by_path) != len(owned_records):
        raise ManifestError("Deployment ownership paths overlap in the manifest.")
    for record in owned_records:
        target = _normalized(Path(record["path"]))
        backup_value = record.get("backup")
        created = bool(record["created"])
        if created and backup_value is not None:
            raise ManifestError(
                f"Created ownership record unexpectedly has a backup: {target}."
            )
        if not created and backup_value is None:
            raise ManifestError(
                f"Preexisting ownership record is missing its backup: {target}."
            )
        collision = collision_by_path.get(target)
        if backup_value is None:
            if collision is not None:
                raise ManifestError(
                    f"Collision record has no owned backup relationship: {target}."
                )
            continue
        backup = _normalized(Path(backup_value))
        backup_root = _normalized(paths.root / "backups" / tool)
        try:
            backup.relative_to(backup_root)
        except ValueError as error:
            raise ManifestError(
                f"Manifest backup is outside {tool} Aphelocoma backups: {backup}."
            ) from error
        if not is_within_resolved(backup, backup_root):
            raise ManifestError(
                f"Manifest backup resolves outside {tool} Aphelocoma backups: {backup}."
            )
        if any(
            paths_overlap_resolved(backup, protected)
            for protected in paths.protected_legacy_paths
        ):
            raise ManifestError(
                f"Manifest backup overlaps protected legacy data: {backup}."
            )
        backup_symlink = first_symlink_component(backup, paths.root)
        if backup_symlink is not None:
            raise ManifestError(
                f"Manifest backup path uses a symlink: {backup_symlink}."
            )
        if (
            collision is None
            or _normalized(Path(collision["backup"])) != backup
        ):
            raise ManifestError(
                f"Manifest collision backup relationship is invalid for {target}."
            )
    for collision_path in collision_by_path:
        if collision_path not in owned_by_path:
            raise ManifestError(
                f"Manifest collision record is not owned: {collision_path}."
            )

    if state == "partial" and not owned_records:
        raise ManifestError("Partial deployment manifest has no unresolved ownership.")


def _verify_manifest_backups(manifest: Dict[str, object]) -> None:
    for collision in manifest["collisions"]:
        backup = Path(collision["backup"])
        if not (backup.exists() or backup.is_symlink()):
            raise ManifestError(
                f"Collision backup is missing for {collision['path']}: {backup}."
            )
        if digest_path(backup) != collision["digest"]:
            raise ManifestError(
                f"Collision backup digest mismatch for {collision['path']}: {backup}."
            )


def _restore_backup(backup: Path, target: Path) -> None:
    if target.exists() or target.is_symlink():
        _remove_path(target)
    _copy_path(backup, target)


def undeploy_hamilton(paths: RuntimePaths, tool: str) -> DeploymentResult:
    if tool not in ("claude", "codex"):
        raise DeploymentError(f"Unsupported deployment target: {tool}.")
    _ensure_host_paths_safe(paths, tool)
    deployment_manifest = manifest_path(paths.root, tool)
    _ensure_active_root_is_not_legacy(paths, (deployment_manifest,))
    manifest_symlink = first_symlink_component(deployment_manifest, paths.root)
    if manifest_symlink is not None:
        raise DeploymentError(
            f"Deployment manifest path uses a symlink: {manifest_symlink}."
        )
    try:
        manifest = load_manifest(deployment_manifest, tool)
    except FileNotFoundError:
        return DeploymentResult(True, (f"Hamilton is not deployed to {tool}.",), None)
    _validate_manifest_scope(paths, tool, manifest)
    _verify_manifest_backups(manifest)
    messages: List[str] = []
    unresolved_artifacts = []
    for artifact in manifest["artifacts"]:
        target = Path(artifact["path"])
        backup = Path(artifact["backup"]) if artifact.get("backup") else None
        exists = target.exists() or target.is_symlink()
        if exists and digest_path(target) != artifact["digest"]:
            messages.append(f"Artifact drift preserved at {target}.")
            unresolved_artifacts.append(artifact)
            continue
        if backup is not None and not (backup.exists() or backup.is_symlink()):
            messages.append(f"Collision backup is missing for {target}: {backup}.")
            unresolved_artifacts.append(artifact)
            continue
        if exists:
            _remove_path(target)
        if backup is not None:
            _restore_backup(backup, target)

    unresolved_blocks = []
    for block in manifest["managed_blocks"]:
        target = Path(block["path"])
        if not target.exists():
            continue
        content = target.read_text(encoding="utf-8")
        updated, removed = remove_managed_block(
            content,
            block["start_marker"],
            block["end_marker"],
            block["digest"],
        )
        if not removed:
            messages.append(f"Managed block drift preserved in {target}.")
            unresolved_blocks.append(block)
            continue
        if not updated and block["created"]:
            target.unlink()
        else:
            atomic_write_text(target, updated)

    if unresolved_artifacts or unresolved_blocks:
        manifest["state"] = "partial"
        manifest["artifacts"] = unresolved_artifacts
        manifest["managed_blocks"] = unresolved_blocks
        unresolved_paths = {
            str(record["path"])
            for record in (*unresolved_artifacts, *unresolved_blocks)
        }
        manifest["collisions"] = [
            collision
            for collision in manifest["collisions"]
            if collision["path"] in unresolved_paths
        ]
        _validate_manifest_scope(paths, tool, manifest)
        _verify_manifest_backups(manifest)
        save_manifest(deployment_manifest, manifest)
        messages.append(
            f"Undeploy incomplete; resolve drift and rerun aph undeploy {tool}."
        )
        return DeploymentResult(False, tuple(messages), deployment_manifest)

    deployment_manifest.unlink()
    messages.append(f"Undeployed Hamilton from {tool}.")
    return DeploymentResult(True, tuple(messages), None)


def inspect_deployments(paths: RuntimePaths) -> DeploymentInspection:
    messages = []
    deployed = []
    collision_count = 0
    ok = True
    for tool in ("claude", "codex"):
        path = manifest_path(paths.root, tool)
        if not path.exists() and not path.is_symlink():
            if tool == "codex":
                unowned_block = _unowned_codex_block_issue(paths)
                if unowned_block is not None:
                    ok = False
                    messages.append(unowned_block)
            continue
        deployed.append(tool)
        try:
            _ensure_active_root_is_not_legacy(paths, (path,))
            _ensure_host_paths_safe(paths, tool)
            manifest_symlink = first_symlink_component(path, paths.root)
            if manifest_symlink is not None:
                raise DeploymentError(
                    f"Deployment manifest path uses a symlink: {manifest_symlink}."
                )
            manifest = load_manifest(path, tool)
            _validate_manifest_scope(paths, tool, manifest, require_complete=True)
            _verify_manifest_backups(manifest)
        except (DeploymentError, ManifestError, OSError) as error:
            ok = False
            messages.append(f"{tool} manifest is invalid: {error}")
            continue
        collision_count += len(manifest.get("collisions", []))
        for artifact in manifest["artifacts"]:
            target = Path(artifact["path"])
            if not (target.exists() or target.is_symlink()):
                ok = False
                messages.append(f"{tool} owned artifact is missing: {target}")
            elif digest_path(target) != artifact["digest"]:
                ok = False
                messages.append(f"{tool} artifact digest drift: {target}")
            backup = artifact.get("backup")
            if backup is not None and not Path(backup).exists():
                ok = False
                messages.append(f"{tool} collision backup is missing: {backup}")
        for block in manifest["managed_blocks"]:
            target = Path(block["path"])
            if not target.exists():
                ok = False
                messages.append(f"{tool} managed configuration is missing: {target}")
                continue
            try:
                located = locate_managed_block(
                    target.read_text(encoding="utf-8"),
                    block["start_marker"],
                    block["end_marker"],
                )
            except (ManifestError, OSError, UnicodeError) as error:
                ok = False
                messages.append(f"{tool} managed block is invalid: {error}")
                continue
            if located is None or digest_text(located[2]) != block["digest"]:
                ok = False
                messages.append(f"{tool} managed block drift: {target}")
            backup = block.get("backup")
            if backup is not None and not Path(backup).exists():
                ok = False
                messages.append(f"{tool} configuration backup is missing: {backup}")
    if not deployed:
        messages.append("No Hamilton deployments recorded.")
    elif ok:
        detail = ", ".join(deployed)
        messages.append(
            f"Hamilton deployments are healthy for {detail}; "
            f"{collision_count} collision backup(s) recorded."
        )
    return DeploymentInspection(ok, tuple(messages), tuple(deployed), collision_count)
