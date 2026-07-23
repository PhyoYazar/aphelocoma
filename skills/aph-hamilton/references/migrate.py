#!/usr/bin/env python3
"""Check or apply the backed-up Hamilton v0.2 project-state migration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _load_package() -> None:
    try:
        import aphelocoma.hamilton_state  # noqa: F401
        return
    except ModuleNotFoundError as error:
        if error.name not in {"aphelocoma", "aphelocoma.hamilton_state"}:
            raise
    source = Path(__file__).resolve().parents[3] / "src"
    if source.is_dir():
        sys.path.insert(0, str(source))


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
    _load_package()
    from aphelocoma.hamilton_state import MigrationError, migrate_project

    try:
        result = migrate_project(
            Path(args.project_dir),
            apply=args.mode == "apply",
            inject_failure=args.inject_failure,
        )
    except MigrationError as error:
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
