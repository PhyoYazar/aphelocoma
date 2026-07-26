#!/usr/bin/env python3
"""Check or apply the backed-up Hamilton v0.2 project-state migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


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


class RuntimeDiscoveryError(RuntimeError):
    pass


def _active_root() -> Path:
    home = Path(os.environ.get("HOME") or str(Path.home()))
    value = os.environ.get("APHELOCOMA_ROOT")
    if not value:
        return home / ".aphelocoma"
    if value == "~":
        return home
    if value.startswith("~/"):
        return home / value[2:]
    root = Path(value)
    return root if root.is_absolute() else Path.cwd() / root


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_path(path: Path) -> str:
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


def _release_source(bundle: Path):
    source = bundle / "src"
    required = (bundle / "VERSION",) + tuple(
        bundle / relative for relative in RELEASE_RUNTIME_FILES
    )
    return source if all(path.is_file() for path in required) else None


def _installed_source():
    root = _active_root()
    tool = root / "tool"
    manifest = root / "install.json"
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
        recorded_tool = Path(record["tool_path"])
        recorded_digest = record["tool_digest"]
        recorded_version = record["version"]
        active_version = (tool / "VERSION").read_text(encoding="utf-8").strip()
        active_digest = _digest_path(tool)
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None
    if (
        record.get("schema_version") != 1
        or recorded_tool != tool
        or recorded_version != active_version
        or recorded_digest != active_digest
    ):
        return None
    return _release_source(tool)


def _load_package(required_symbols):
    bundle = Path(__file__).resolve().parents[3]
    source = _installed_source() or _release_source(bundle)
    if source is None:
        raise RuntimeDiscoveryError(
            "Cannot locate a manifest-owned Aphelocoma Python runtime for this "
            "Hamilton skill. Reinstall Aphelocoma and run `aph deploy claude` or "
            "`aph deploy codex` again. If APHELOCOMA_ROOT is customized, export it "
            "before running this command."
        )
    for name in tuple(sys.modules):
        if name == "aphelocoma" or name.startswith("aphelocoma."):
            del sys.modules[name]
    sys.path.insert(0, str(source))
    try:
        import aphelocoma.hamilton_state as runtime
    except Exception as error:
        raise RuntimeDiscoveryError(
            "The manifest-owned Aphelocoma runtime could not be loaded. Reinstall "
            "Aphelocoma and run `aph deploy claude` or `aph deploy codex` again."
        ) from error
    missing = [name for name in required_symbols if not hasattr(runtime, name)]
    if missing:
        raise RuntimeDiscoveryError(
            "The manifest-owned Aphelocoma runtime is incomplete or incompatible. "
            "Reinstall Aphelocoma and run `aph deploy claude` or `aph deploy codex` "
            "again."
        )
    return runtime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate unversioned Hamilton v0.2 state transactionally."
    )
    parser.add_argument("mode", choices=("check", "apply"))
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument(
        "--inject-failure",
        choices=("after_backup", "after_write", "after_validate", "after_swap"),
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        runtime = _load_package(("MigrationError", "migrate_project"))
    except RuntimeDiscoveryError as error:
        print("Hamilton migration could not run: %s" % error, file=sys.stderr)
        return 2

    try:
        result = runtime.migrate_project(
            Path(args.project_dir),
            apply=args.mode == "apply",
            inject_failure=args.inject_failure,
        )
    except runtime.MigrationError as error:
        print("Hamilton migration failed: %s" % error, file=sys.stderr)
        if error.backup is not None:
            print("Recoverable backup: %s" % error.backup, file=sys.stderr)
        return 2

    if result.status == "migration_required":
        print(
            "%s Run `migrate.py apply %s`; a recoverable backup will be retained."
            % (result.message, result.project)
        )
        return 1
    if result.backup is not None:
        print("%s Backup: %s" % (result.message, result.backup))
    else:
        print(result.message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
