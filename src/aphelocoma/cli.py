"""Command-line surface for the Hamilton-only Aphelocoma product."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import List, Optional, Sequence

from .deploy import DeploymentError, deploy_hamilton, undeploy_hamilton
from .doctor import DoctorContext, default_registry, run_checks as run_doctor
from .lifecycle import (
    LifecycleError,
    uninstall_installation,
    update_installation,
)
from .manifest import ManifestError
from .paths import RuntimePaths, resolve_paths


COMMANDS = (
    "deploy",
    "undeploy",
    "doctor",
    "status",
    "update",
    "uninstall",
    "version",
    "help",
)
TOOLS = ("claude", "codex")
STATUS_LABEL_WIDTH = 9


class UsageError(Exception):
    pass


class AphArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "invalid choice" in message and "command" in message.lower():
            value = message.split("invalid choice:", 1)[1].split("(", 1)[0].strip()
            raise UsageError(
                f"Unknown command {value}. Run 'aph help' for the supported commands."
            )
        raise UsageError(f"{message}. Run 'aph help' for usage.")


def build_parser() -> AphArgumentParser:
    parser = AphArgumentParser(
        prog="aph",
        description="Aphelocoma — install and operate the Hamilton workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    deploy = subparsers.add_parser("deploy", help="Deploy Hamilton to an AI tool.")
    deploy.add_argument("tool", choices=TOOLS, help="Target tool: claude or codex.")

    undeploy = subparsers.add_parser(
        "undeploy",
        help="Remove manifest-owned Hamilton files from an AI tool.",
    )
    undeploy.add_argument("tool", choices=TOOLS, help="Target tool: claude or codex.")

    doctor = subparsers.add_parser(
        "doctor",
        help="Check installation health and print remediation.",
    )
    doctor.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit stable machine-readable JSON.",
    )

    status = subparsers.add_parser(
        "status",
        help="Show the Hamilton progress board for a project.",
    )
    status.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory holding .aphelocoma/ (default: this directory).",
    )
    status.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit stable machine-readable JSON.",
    )
    status.add_argument(
        "--write",
        action="store_true",
        dest="write_report",
        help="Also regenerate .aphelocoma/STATUS.md from current state.",
    )

    subparsers.add_parser("update", help="Update Aphelocoma transactionally.")
    subparsers.add_parser(
        "uninstall",
        help="Remove files owned by the Aphelocoma installation.",
    )
    subparsers.add_parser("version", help="Print the installed Aphelocoma version.")

    help_parser = subparsers.add_parser("help", help="Show command help.")
    help_parser.add_argument(
        "topic",
        nargs="?",
        choices=tuple(command for command in COMMANDS if command != "help"),
        help="Command to describe.",
    )
    return parser


def _warn_legacy_home(paths: RuntimePaths) -> None:
    legacy = paths.legacy_home_override
    if legacy is None:
        return
    print(
        "Warning: APHELOCOMA_HOME is ignored. "
        f"{legacy} is protected legacy data and will not be read, changed, or deleted.",
        file=sys.stderr,
    )


def _version(paths: RuntimePaths) -> int:
    version_file = paths.tool_root / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        print(
            f"Error: cannot read installed version at {version_file}: {error}. "
            "Reinstall Aphelocoma.",
            file=sys.stderr,
        )
        return 1
    if not version:
        print(
            f"Error: installed version at {version_file} is empty. "
            "Reinstall Aphelocoma.",
            file=sys.stderr,
        )
        return 1
    print(f"aph {version}")
    return 0


def _doctor(paths: RuntimePaths, *, json_output: bool) -> int:
    context = DoctorContext(paths=paths, cwd=Path.cwd())
    report = run_doctor(context, default_registry())
    if json_output:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        state = "healthy" if report.healthy else "action required"
        print(f"Aphelocoma doctor: {state}")
        for diagnostic in report.checks:
            print(f"[{diagnostic.status}] {diagnostic.message}")
            if diagnostic.remediation:
                print(f"  Fix: {diagnostic.remediation}")
    return report.exit_code


def _field(label: str, value: str) -> str:
    return f"{label.ljust(STATUS_LABEL_WIDTH)} {value}"


def render_status_board(summary: object) -> List[str]:
    """Render the PROTOCOL §5.6 board as plain text: the stage and the tasks.

    No colour and no glyphs: every task line carries its status as a word, so the
    board reads identically in a pipe, a log, and a screen reader — a `blocked`
    task says so in its own row.
    """

    lines = [
        _field("Hamilton", summary.project),
        _field("Phase", summary.phase),
        _field(
            "Progress",
            f"{summary.done_count} of {summary.total_count} tasks done",
        ),
        "",
        "Tasks",
    ]
    if not summary.tasks:
        lines.append("  no tasks on the board yet")
        return lines
    status_width = max(len(task.status) for task in summary.tasks) + 2
    id_width = max(len(task.id) for task in summary.tasks)
    for task in summary.tasks:
        status = f"[{task.status}]".ljust(status_width)
        lines.append(f"  {status}  {task.id.ljust(id_width)}  {task.title}")
    return lines


def _status(path: str, *, json_output: bool, write_report: bool) -> int:
    # Imported lazily so a damaged Hamilton runtime still leaves `aph doctor`
    # and `aph version` able to report it.
    from .hamilton_state import (
        STATUS_REPORT_SCHEMA_VERSION,
        StatusError,
        summarize_project,
        write_status_report,
    )

    written: Optional[Path] = None
    try:
        summary = summarize_project(Path(path))
        if write_report:
            written = write_status_report(Path(path), summary)
    except StatusError as error:
        if json_output:
            print(
                json.dumps(
                    {
                        "schema_version": STATUS_REPORT_SCHEMA_VERSION,
                        "status": "error",
                        "error": {
                            "path": error.path,
                            "message": str(error),
                            "remediation": error.remediation,
                        },
                    },
                    indent=2,
                )
            )
        else:
            print(f"Error: {error}", file=sys.stderr)
            print(f"  Fix: {error.remediation}", file=sys.stderr)
        return 1
    if json_output:
        print(json.dumps(summary.as_dict(), indent=2))
    else:
        for line in render_status_board(summary):
            print(line)
    if written is not None:
        # Stdout stays exactly the board, or exactly one JSON document.
        print(f"Wrote the Hamilton progress board to {written}", file=sys.stderr)
    return 0


def _print_result(messages: Sequence[str], ok: bool) -> int:
    stream = sys.stdout if ok else sys.stderr
    for message in messages:
        print(message, file=stream)
    return 0 if ok else 1


def _deploy(paths: RuntimePaths, tool: str) -> int:
    result = deploy_hamilton(paths, tool)
    return _print_result(result.messages, result.ok)


def _undeploy(paths: RuntimePaths, tool: str) -> int:
    result = undeploy_hamilton(paths, tool)
    return _print_result(result.messages, result.ok)


def _update(paths: RuntimePaths) -> int:
    result = update_installation(
        paths,
        fail_at=os.environ.get("APHELOCOMA_FAIL_AT"),
    )
    return _print_result(result.messages, result.ok)


def _uninstall(paths: RuntimePaths) -> int:
    result = uninstall_installation(paths)
    return _print_result(result.messages, result.ok)


def _show_help(parser: AphArgumentParser, topic: Optional[str]) -> int:
    if topic is None:
        parser.print_help()
    else:
        subparsers_action = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        subparsers_action.choices[topic].print_help()
    return 0


def _dispatch(
    parser: AphArgumentParser,
    arguments: argparse.Namespace,
    paths: RuntimePaths,
) -> int:
    command = arguments.command
    if command is None:
        parser.print_help()
        return 0
    if command == "help":
        return _show_help(parser, arguments.topic)

    _warn_legacy_home(paths)
    if command == "doctor":
        return _doctor(paths, json_output=arguments.json_output)
    if command == "status":
        return _status(
            arguments.path,
            json_output=arguments.json_output,
            write_report=arguments.write_report,
        )
    if command == "version":
        return _version(paths)
    if command == "deploy":
        return _deploy(paths, arguments.tool)
    if command == "undeploy":
        return _undeploy(paths, arguments.tool)
    if command == "update":
        return _update(paths)
    if command == "uninstall":
        return _uninstall(paths)
    raise UsageError(
        f"Unknown command {command!r}. Run 'aph help' for the supported commands."
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    raw_arguments: List[str] = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    try:
        arguments = parser.parse_args(raw_arguments)
        paths = resolve_paths()
        return _dispatch(parser, arguments, paths)
    except UsageError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except (DeploymentError, LifecycleError, ManifestError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except SystemExit as exit_signal:
        return int(exit_signal.code or 0)
    except Exception as error:
        print(f"Error: unexpected failure: {error}", file=sys.stderr)
        return 2
