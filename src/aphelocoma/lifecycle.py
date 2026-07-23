"""Transactional installation, update, PATH ownership, and uninstall."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple
import uuid

from .doctor import DEFINITION_FILES
from .io import atomic_write_json, atomic_write_text
from .manifest import (
    first_symlink_component,
    ManifestError,
    digest_path,
    digest_text,
    is_within_resolved,
    locate_managed_block,
    paths_overlap_resolved,
    put_managed_block,
    remove_managed_block,
)
from .paths import RuntimePaths


INSTALL_SCHEMA_VERSION = 1
PATH_BLOCK_START = "# >>> aphelocoma path >>>"
PATH_BLOCK_END = "# <<< aphelocoma path <<<"
VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9][A-Za-z0-9.-]*)?$"
)
DEFAULT_REPOSITORY = "https://github.com/PhyoYazar/aphelocoma.git"
RELEASE_RUNTIME_FILES = (
    "install.sh",
    "bin/aph",
    "src/aphelocoma/__init__.py",
    "src/aphelocoma/cli.py",
    "src/aphelocoma/paths.py",
    "src/aphelocoma/io.py",
    "src/aphelocoma/doctor.py",
    "src/aphelocoma/hamilton_state.py",
    "src/aphelocoma/lifecycle.py",
    "src/aphelocoma/deploy.py",
    "src/aphelocoma/manifest.py",
    "src/aphelocoma/legacy.py",
    "adapters/claude-code/scripts/gen-hamilton-crew.py",
    "adapters/codex/scripts/gen-hamilton-crew-codex.py",
)
HAMILTON_RELEASE_FILES = (
    "skills/aph-hamilton/metadata.yaml",
    "skills/aph-hamilton/skill.md",
)
HAMILTON_RELEASE_DIRECTORIES = (
    "skills/aph-hamilton/references",
    "skills/aph-hamilton/templates",
    "skills/aph-hamilton/examples",
)
RELEASE_COPY_PATHS = (
    "VERSION",
    *RELEASE_RUNTIME_FILES,
    *HAMILTON_RELEASE_FILES,
    *HAMILTON_RELEASE_DIRECTORIES,
)


class LifecycleError(RuntimeError):
    """An install/update/uninstall action was refused or rolled back."""


@dataclass(frozen=True)
class LifecycleResult:
    ok: bool
    messages: Tuple[str, ...]
    recovery: Optional[Path] = None


@dataclass(frozen=True)
class PathMarkerResult:
    ok: bool
    path: Path
    digest: str
    message: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "start_marker": PATH_BLOCK_START,
            "end_marker": PATH_BLOCK_END,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class InstallationInspection:
    ok: bool
    messages: Tuple[str, ...]


def install_manifest_path(root: Path) -> Path:
    return Path(root) / "install.json"


def _normalized_path(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(str(path))))


def _unowned_path_block_issue(shell_rc: Path) -> Optional[str]:
    if shell_rc.is_symlink():
        return (
            f"Refusing unowned supported shell symlink at {shell_rc}; "
            "replace it with a regular file before installation."
        )
    if not shell_rc.exists():
        return None
    try:
        current = shell_rc.read_text(encoding="utf-8")
        located = locate_managed_block(
            current,
            PATH_BLOCK_START,
            PATH_BLOCK_END,
        )
    except ManifestError as error:
        return (
            f"Refusing ambiguous unowned canonical PATH markers in "
            f"{shell_rc}: {error}"
        )
    except (OSError, UnicodeError) as error:
        return f"Cannot safely inspect {shell_rc} for an unowned PATH block: {error}"
    if located is None:
        return None
    return (
        f"Refusing unowned canonical PATH managed block in {shell_rc}; "
        "move or remove that block before installation."
    )


def _unowned_path_block_issues(
    paths: RuntimePaths,
    owned_path: Optional[Path] = None,
) -> Tuple[str, ...]:
    normalized_owned = (
        _normalized_path(owned_path) if owned_path is not None else None
    )
    issues = []
    for name in (".zshrc", ".bashrc", ".bash_profile"):
        candidate = _normalized_path(paths.home / name)
        if normalized_owned is not None and candidate == normalized_owned:
            continue
        issue = _unowned_path_block_issue(candidate)
        if issue is not None:
            issues.append(issue)
    return tuple(issues)


def _ensure_active_root_is_not_legacy(
    paths: RuntimePaths,
    mutation_targets: Sequence[Path],
) -> None:
    if any(
        is_within_resolved(paths.root, protected)
        for protected in paths.protected_legacy_paths
    ):
        raise LifecycleError(
            f"Active root {paths.root} overlaps protected legacy data; "
            "choose a different APHELOCOMA_ROOT."
        )
    for candidate in mutation_targets:
        if any(
            paths_overlap_resolved(candidate, protected)
            for protected in paths.protected_legacy_paths
        ):
            raise LifecycleError(
                f"Owned lifecycle path {candidate} overlaps protected legacy data; "
                "choose a different APHELOCOMA_ROOT."
            )
    current = paths.root
    while not current.exists() and not current.is_symlink():
        if current.parent == current:
            break
        current = current.parent
    if current.is_symlink():
        raise LifecycleError(
            f"Active root uses symlinked path component {current}; "
            "choose a direct APHELOCOMA_ROOT."
        )
    for candidate in mutation_targets:
        symlink = first_symlink_component(candidate, paths.root)
        if symlink is not None:
            raise LifecycleError(
                f"Active-root path component is a symlink and was refused: {symlink}."
            )


def _validate_path_marker(
    paths: RuntimePaths,
    marker: object,
) -> Optional[str]:
    if marker is None:
        return None
    if not isinstance(marker, dict):
        return "Install manifest PATH marker is invalid."
    required = ("path", "start_marker", "end_marker", "digest")
    if any(not isinstance(marker.get(field), str) for field in required):
        return "Install manifest PATH marker is invalid."
    if (
        marker["start_marker"] != PATH_BLOCK_START
        or marker["end_marker"] != PATH_BLOCK_END
    ):
        return "Install manifest PATH marker boundaries are not canonical."
    if not re.fullmatch(r"[0-9a-f]{64}", marker["digest"]):
        return "Install manifest PATH marker digest is invalid."
    marker_path = Path(marker["path"])
    if not marker_path.is_absolute():
        return "Install manifest PATH marker path is not absolute."
    allowed_shell_files = {
        _normalized_path(paths.home / name)
        for name in (".zshrc", ".bashrc", ".bash_profile")
    }
    if _normalized_path(marker_path) not in allowed_shell_files:
        return (
            "Install manifest PATH marker is outside supported shell files: "
            f"{marker_path}."
        )
    try:
        symlink = first_symlink_component(marker_path, paths.home)
    except ManifestError as error:
        return str(error)
    if symlink is not None:
        return f"Install manifest PATH marker path uses a symlink: {symlink}."
    if any(
        paths_overlap_resolved(marker_path, protected)
        for protected in paths.protected_legacy_paths
    ):
        return f"Install manifest PATH marker overlaps protected legacy data: {marker_path}."
    try:
        content = marker_path.read_text(encoding="utf-8")
        located = locate_managed_block(
            content,
            PATH_BLOCK_START,
            PATH_BLOCK_END,
        )
    except (OSError, UnicodeError, ManifestError) as error:
        return f"PATH managed block drift in {marker_path}: {error}"
    expected_block = (
        PATH_BLOCK_START
        + "\n"
        + f"export PATH={_shell_quote(str(paths.root / 'tool' / 'bin'))}:\"$PATH\""
        + "\n"
        + PATH_BLOCK_END
        + "\n"
    )
    if (
        located is None
        or located[2] != expected_block
        or digest_text(located[2]) != marker["digest"]
    ):
        return f"PATH managed block drift in {marker_path}."
    return None


def _verify_active_install(
    paths: RuntimePaths,
    manifest: Dict[str, object],
) -> None:
    active = paths.root / "tool"
    if _normalized_path(Path(manifest["tool_path"])) != _normalized_path(active):
        raise LifecycleError(
            f"Install manifest tool path is outside the active root: "
            f"{manifest['tool_path']}."
        )
    if not active.is_dir() or active.is_symlink():
        raise LifecycleError(f"Installed tool is missing or unsafe at {active}.")
    if digest_path(active) != manifest["tool_digest"]:
        raise LifecycleError(f"Installed tool digest drift detected at {active}.")
    marker_issue = _validate_path_marker(paths, manifest.get("path_marker"))
    if marker_issue is not None:
        raise LifecycleError(marker_issue)


def _copy_release(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise LifecycleError(
            f"Release source is missing or unsafe: {source}."
        )
    ignored = shutil.ignore_patterns(
        "__pycache__",
        "*.pyc",
        ".DS_Store",
    )
    assets = []
    for relative in RELEASE_COPY_PATHS:
        asset = source / relative
        if asset.is_symlink():
            raise LifecycleError(
                f"Release asset is a symlink and was refused: {asset}."
            )
        if asset.is_dir():
            for child in asset.rglob("*"):
                if child.is_symlink():
                    raise LifecycleError(
                        f"Release asset is a symlink and was refused: {child}."
                    )
                if not child.is_dir() and not child.is_file():
                    raise LifecycleError(
                        f"Release asset is not a regular file or directory: {child}."
                    )
        elif not asset.is_file():
            raise LifecycleError(
                f"Release asset is missing or unsafe: {asset}."
            )
        assets.append((asset, destination / relative))

    destination.mkdir()
    for asset, target in assets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if asset.is_dir():
            shutil.copytree(
                asset,
                target,
                symlinks=True,
                ignore=ignored,
            )
        else:
            shutil.copy2(asset, target, follow_symlinks=False)


def verify_release(tool_root: Path) -> str:
    root = Path(tool_root)
    missing = [
        relative
        for relative in (*RELEASE_RUNTIME_FILES, *DEFINITION_FILES)
        if not (root / relative).is_file()
    ]
    if missing:
        raise LifecycleError(
            "Release verification failed; missing: " + ", ".join(missing) + "."
        )
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise LifecycleError(f"Release VERSION is unreadable: {error}") from error
    if not VERSION_PATTERN.fullmatch(version):
        raise LifecycleError(f"Release VERSION is invalid: {version!r}.")
    completed = subprocess.run(
        [sys.executable, str(root / "bin" / "aph"), "version"],
        cwd=str(root),
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0 or completed.stdout.strip() != f"aph {version}":
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise LifecycleError(f"Release CLI verification failed: {detail}.")
    return version


def _load_install_manifest(path: Path) -> Dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LifecycleError(f"Cannot read install manifest {path}: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != INSTALL_SCHEMA_VERSION:
        raise LifecycleError(
            f"Install manifest {path} has an unsupported or invalid schema."
        )
    tool_path = value.get("tool_path")
    digest = value.get("tool_digest")
    if not isinstance(tool_path, str) or not Path(tool_path).is_absolute():
        raise LifecycleError(f"Install manifest {path} has an invalid tool_path.")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LifecycleError(f"Install manifest {path} has an invalid tool_digest.")
    return value


def activate_release(
    source: Path,
    paths: RuntimePaths,
    *,
    fail_at: Optional[str] = None,
    shell_rc: Optional[Path] = None,
) -> LifecycleResult:
    source = Path(source)
    shell_rc = Path(shell_rc) if shell_rc is not None else None
    active = paths.root / "tool"
    old_manifest_path = install_manifest_path(paths.root)
    container = paths.root / f".stage-{uuid.uuid4().hex}"
    transient_recovery = paths.root / f".tool-recovery-{uuid.uuid4().hex}"
    recovery_parent = (
        paths.root
        / "backups"
        / "install"
        / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex
        )
    )
    mutation_targets = [
        active,
        old_manifest_path,
        container,
    ]
    if active.exists() or active.is_symlink():
        mutation_targets.extend((transient_recovery, recovery_parent))
    _ensure_active_root_is_not_legacy(paths, mutation_targets)
    old_manifest_bytes = (
        old_manifest_path.read_bytes() if old_manifest_path.exists() else None
    )
    old_install = (
        _load_install_manifest(old_manifest_path)
        if old_manifest_path.exists()
        else None
    )
    if old_install is not None:
        _verify_active_install(paths, old_install)
    path_marker = old_install.get("path_marker") if old_install is not None else None
    if shell_rc is not None:
        allowed_shell_files = {
            _normalized_path(paths.home / name)
            for name in (".zshrc", ".bashrc", ".bash_profile")
        }
        if _normalized_path(shell_rc) not in allowed_shell_files:
            raise LifecycleError(
                f"PATH marker target is outside supported shell files: {shell_rc}."
            )
        if any(
            paths_overlap_resolved(shell_rc, protected)
            for protected in paths.protected_legacy_paths
        ):
            raise LifecycleError(
                f"PATH marker target overlaps protected legacy data: {shell_rc}."
            )
        shell_symlink = first_symlink_component(shell_rc, paths.home)
        if shell_symlink is not None:
            raise LifecycleError(
                f"PATH marker target uses a symlink and was refused: {shell_symlink}."
            )
    owned_path_marker: Optional[Path] = None
    if path_marker is not None and isinstance(path_marker, dict):
        recorded_shell = Path(path_marker["path"])
        owned_path_marker = recorded_shell
        if shell_rc is not None and _normalized_path(shell_rc) != _normalized_path(
            recorded_shell
        ):
            raise LifecycleError(
                f"Owned PATH marker is recorded in {recorded_shell}, not {shell_rc}."
            )
    unowned_blocks = _unowned_path_block_issues(paths, owned_path_marker)
    if unowned_blocks:
        raise LifecycleError(" ".join(unowned_blocks))

    paths.root.mkdir(parents=True, exist_ok=True)
    container.mkdir()
    staged_tool = container / "tool"
    persistent_recovery: Optional[Path] = None
    moved_old = False
    activated = False
    shell_existed = bool(shell_rc is not None and shell_rc.exists())
    shell_bytes = (
        shell_rc.read_bytes()
        if shell_rc is not None and shell_rc.exists()
        else None
    )
    try:
        _copy_release(source, staged_tool)
        version = verify_release(staged_tool)
        if fail_at == "after_stage":
            raise LifecycleError("injected lifecycle failure after staging")
        if active.exists() or active.is_symlink():
            os.replace(str(active), str(transient_recovery))
            moved_old = True
        os.replace(str(staged_tool), str(active))
        activated = True
        if fail_at == "after_activate":
            raise LifecycleError("injected lifecycle failure after activation")
        verify_release(active)
        if shell_rc is not None:
            marker = ensure_path_marker(shell_rc, active / "bin")
            path_marker = marker.as_dict()
        if fail_at == "after_path_marker":
            raise LifecycleError("injected lifecycle failure after PATH marker")

        if moved_old:
            recovery_parent.mkdir(parents=True, exist_ok=False)
            persistent_recovery = recovery_parent / "tool"
            os.replace(str(transient_recovery), str(persistent_recovery))

        manifest = {
            "schema_version": INSTALL_SCHEMA_VERSION,
            "tool_path": str(active),
            "tool_digest": digest_path(active),
            "version": version,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "recovery": (
                str(persistent_recovery) if persistent_recovery is not None else None
            ),
            "path_marker": path_marker,
        }
        atomic_write_json(old_manifest_path, manifest, mode=0o600)
    except Exception as error:
        if activated and (active.exists() or active.is_symlink()):
            if active.is_dir() and not active.is_symlink():
                shutil.rmtree(active)
            else:
                active.unlink()
        recovery_source = None
        if transient_recovery.exists() or transient_recovery.is_symlink():
            recovery_source = transient_recovery
        elif persistent_recovery is not None and (
            persistent_recovery.exists() or persistent_recovery.is_symlink()
        ):
            recovery_source = persistent_recovery
        if recovery_source is not None:
            active.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(recovery_source), str(active))
        if old_manifest_bytes is None:
            old_manifest_path.unlink(missing_ok=True)
        else:
            atomic_write_text(old_manifest_path, old_manifest_bytes.decode("utf-8"), mode=0o600)
        if shell_rc is not None:
            if shell_existed and shell_bytes is not None:
                atomic_write_text(shell_rc, shell_bytes.decode("utf-8"))
            elif shell_rc.exists():
                shell_rc.unlink()
        if isinstance(error, LifecycleError):
            raise
        raise LifecycleError(f"Activation failed and was rolled back: {error}") from error
    finally:
        shutil.rmtree(container, ignore_errors=True)
        if transient_recovery.exists():
            if transient_recovery.is_dir():
                shutil.rmtree(transient_recovery)
            else:
                transient_recovery.unlink()
    from .legacy import cleanup_legacy_artifacts

    cleanup = cleanup_legacy_artifacts(paths)
    return LifecycleResult(
        True,
        (
            f"Activated Aphelocoma {version} at {active}.",
            *cleanup.messages,
        ),
        persistent_recovery,
    )


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def ensure_path_marker(shell_rc: Path, bin_dir: Path) -> PathMarkerResult:
    shell_rc = Path(shell_rc)
    if shell_rc.is_symlink():
        raise LifecycleError(
            f"PATH marker target is a symlink and was preserved: {shell_rc}."
        )
    current = shell_rc.read_text(encoding="utf-8") if shell_rc.exists() else ""
    export = f"export PATH={_shell_quote(str(Path(bin_dir)))}:\"$PATH\""
    block = PATH_BLOCK_START + "\n" + export + "\n" + PATH_BLOCK_END + "\n"
    updated = put_managed_block(
        current,
        block,
        PATH_BLOCK_START,
        PATH_BLOCK_END,
    )
    atomic_write_text(shell_rc, updated)
    located = locate_managed_block(updated, PATH_BLOCK_START, PATH_BLOCK_END)
    if located is None:
        raise LifecycleError(f"PATH marker was not installed in {shell_rc}.")
    return PathMarkerResult(
        True,
        shell_rc,
        digest_text(located[2]),
        f"PATH marker installed in {shell_rc}.",
    )


def remove_path_marker(shell_rc: Path, expected_digest: str) -> PathMarkerResult:
    shell_rc = Path(shell_rc)
    if shell_rc.is_symlink():
        return PathMarkerResult(
            False,
            shell_rc,
            expected_digest,
            f"PATH marker target is a symlink and was preserved: {shell_rc}.",
        )
    if not shell_rc.exists():
        return PathMarkerResult(True, shell_rc, expected_digest, "PATH file is absent.")
    current = shell_rc.read_text(encoding="utf-8")
    updated, removed = remove_managed_block(
        current,
        PATH_BLOCK_START,
        PATH_BLOCK_END,
        expected_digest,
    )
    if not removed:
        return PathMarkerResult(
            False,
            shell_rc,
            expected_digest,
            f"PATH managed block drift preserved in {shell_rc}.",
        )
    atomic_write_text(shell_rc, updated)
    return PathMarkerResult(True, shell_rc, expected_digest, "PATH marker removed.")


def record_path_marker(root: Path, marker: PathMarkerResult) -> None:
    path = install_manifest_path(root)
    manifest = _load_install_manifest(path)
    manifest["path_marker"] = marker.as_dict()
    atomic_write_json(path, manifest, mode=0o600)


def inspect_installation(paths: RuntimePaths) -> InstallationInspection:
    manifest = install_manifest_path(paths.root)
    active = paths.root / "tool"
    try:
        _ensure_active_root_is_not_legacy(paths, (active, manifest))
    except (LifecycleError, ManifestError) as error:
        return InstallationInspection(False, (str(error),))
    if not manifest.exists():
        unowned_blocks = _unowned_path_block_issues(paths)
        if active.exists() or active.is_symlink():
            return InstallationInspection(
                False,
                (
                    f"Installed tool exists without an ownership manifest: {active}.",
                    *unowned_blocks,
                ),
            )
        if unowned_blocks:
            return InstallationInspection(False, unowned_blocks)
        return InstallationInspection(
            True,
            ("No managed installation is recorded; source-checkout operation is healthy.",),
        )
    try:
        value = _load_install_manifest(manifest)
        _verify_active_install(paths, value)
    except (LifecycleError, ManifestError, OSError) as error:
        return InstallationInspection(False, (str(error),))
    marker = value.get("path_marker")
    owned_marker_path = (
        Path(marker["path"])
        if isinstance(marker, dict) and isinstance(marker.get("path"), str)
        else None
    )
    unowned_blocks = _unowned_path_block_issues(paths, owned_marker_path)
    if unowned_blocks:
        return InstallationInspection(False, unowned_blocks)
    path_detail = (
        f" PATH ownership is healthy in {marker['path']}."
        if isinstance(marker, dict)
        else " PATH is managed manually."
    )
    return InstallationInspection(
        True,
        (
            f"Install manifest and active tool digest are healthy at {active}."
            + path_detail,
        ),
    )


def _download_release(paths: RuntimePaths, repository: str) -> Path:
    checkout = paths.root / f".download-{uuid.uuid4().hex}"
    _ensure_active_root_is_not_legacy(paths, (checkout,))
    checkout.mkdir()
    completed = subprocess.run(
        ["git", "clone", "--depth", "1", repository, str(checkout / "source")],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        shutil.rmtree(checkout, ignore_errors=True)
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise LifecycleError(f"Update download failed: {detail}")
    return checkout


def update_installation(
    paths: RuntimePaths,
    *,
    source: Optional[Path] = None,
    fail_at: Optional[str] = None,
) -> LifecycleResult:
    manifest = install_manifest_path(paths.root)
    active = paths.root / "tool"
    _ensure_active_root_is_not_legacy(paths, (active, manifest))
    if not manifest.exists():
        raise LifecycleError(
            f"Aphelocoma is not installed at {paths.root}; run install.sh first."
        )
    current_install = _load_install_manifest(manifest)
    _verify_active_install(paths, current_install)
    download = None
    if source is None:
        override = os.environ.get("APHELOCOMA_UPDATE_SOURCE")
        if override:
            source = Path(override)
        else:
            download = _download_release(
                paths,
                os.environ.get("APHELOCOMA_REPOSITORY", DEFAULT_REPOSITORY),
            )
            source = download / "source"
    try:
        return activate_release(Path(source), paths, fail_at=fail_at)
    finally:
        if download is not None:
            shutil.rmtree(download, ignore_errors=True)


def uninstall_installation(paths: RuntimePaths) -> LifecycleResult:
    from .deploy import undeploy_hamilton
    from .legacy import cleanup_legacy_artifacts

    manifest_path = install_manifest_path(paths.root)
    active = paths.root / "tool"
    _ensure_active_root_is_not_legacy(paths, (active, manifest_path))
    messages: List[str] = []
    manifest: Optional[Dict[str, object]] = None
    if manifest_path.exists():
        try:
            manifest = _load_install_manifest(manifest_path)
            _verify_active_install(paths, manifest)
        except LifecycleError as error:
            return LifecycleResult(False, (str(error),))
    elif active.exists() or active.is_symlink():
        return LifecycleResult(
            False,
            (f"Unowned tool path preserved at {active}; install manifest is missing.",),
        )

    deployment_ok = True
    for tool in ("claude", "codex"):
        try:
            result = undeploy_hamilton(paths, tool)
        except (ManifestError, OSError) as error:
            deployment_ok = False
            messages.append(f"Cannot undeploy {tool}: {error}")
            continue
        messages.extend(result.messages)
        deployment_ok = deployment_ok and result.ok
    if not deployment_ok:
        messages.append("Uninstall stopped because deployed artifacts still need attention.")
        return LifecycleResult(False, tuple(messages))

    legacy = cleanup_legacy_artifacts(paths)
    messages.extend(legacy.messages)

    if manifest is None:
        messages.append("Aphelocoma installation is already absent.")
        return LifecycleResult(True, tuple(messages))

    marker = manifest.get("path_marker")
    if marker is not None:
        if (
            not isinstance(marker, dict)
            or not isinstance(marker.get("path"), str)
            or not isinstance(marker.get("digest"), str)
        ):
            messages.append("Install manifest PATH marker is invalid.")
            return LifecycleResult(False, tuple(messages))
        marker_path = _normalized_path(Path(marker["path"]))
        allowed_shell_files = {
            _normalized_path(paths.home / name)
            for name in (".zshrc", ".bashrc", ".bash_profile")
        }
        if marker_path not in allowed_shell_files:
            messages.append(
                f"Install manifest PATH marker is outside supported shell files: {marker_path}."
            )
            return LifecycleResult(False, tuple(messages))
        result = remove_path_marker(marker_path, str(marker["digest"]))
        messages.append(result.message)
        if not result.ok:
            return LifecycleResult(False, tuple(messages))

    if active.exists() or active.is_symlink():
        if active.is_dir() and not active.is_symlink():
            shutil.rmtree(active)
        else:
            active.unlink()
    manifest_path.unlink()
    messages.append("Removed the manifest-owned Aphelocoma tool.")
    return LifecycleResult(True, tuple(messages))
