#!/usr/bin/env python3
"""Read-only validator for versioned Hamilton project state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def _load_package() -> None:
    """Make a source checkout runnable without weakening installed imports."""

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
        description="Validate Hamilton schema, protocol, ledger, and privacy invariants."
    )
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit one stable JSON report",
    )
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    _load_package()
    try:
        from aphelocoma.hamilton_state import validate_project

        report = validate_project(Path(args.project_dir))
    except Exception as error:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "internal_error",
                        "error": str(error),
                    },
                    sort_keys=True,
                )
            )
        else:
            print("Hamilton validate could not run: %s" % error, file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report.as_dict(), sort_keys=True))
    else:
        print(
            "Hamilton validate — %s: %d events, %d tasks (%d done)"
            % (
                report.project,
                report.event_count,
                report.task_count,
                report.done_count,
            )
        )
        for issue in report.errors:
            print("  ERROR [%s] %s: %s" % (issue.code, issue.path, issue.message))
            if issue.remediation:
                print("        remediation: %s" % issue.remediation)
        for issue in report.warnings:
            print("  WARN  [%s] %s: %s" % (issue.code, issue.path, issue.message))
        if report.ok:
            print("  OK — no errors (%d warning(s))" % len(report.warnings))
        else:
            print(
                "  %d error(s), %d warning(s)"
                % (len(report.errors), len(report.warnings))
            )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
