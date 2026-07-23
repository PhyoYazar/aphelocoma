"""Command-line surface for the Hamilton-only Aphelocoma product."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List, Optional, Sequence

from .doctor import DoctorContext, default_registry, run_checks as run_doctor
from .paths import RuntimePaths, resolve_paths


COMMANDS = (
    "deploy",
    "undeploy",
    "doctor",
    "update",
    "uninstall",
    "version",
    "help",
)
TOOLS = ("claude", "codex")


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


def _unavailable(command: str) -> int:
    print(
        f"Error: 'aph {command}' is not available in this build. "
        "Install the complete Aphelocoma lifecycle components and try again.",
        file=sys.stderr,
    )
    return 1


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
    if command == "version":
        return _version(paths)
    if command in ("deploy", "undeploy", "update", "uninstall"):
        return _unavailable(command)
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
    except SystemExit as exit_signal:
        return int(exit_signal.code or 0)
    except Exception as error:
        print(f"Error: unexpected failure: {error}", file=sys.stderr)
        return 2
