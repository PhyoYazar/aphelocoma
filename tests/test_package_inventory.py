from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.cli import TOOLS
from aphelocoma.lifecycle import activate_release
from aphelocoma.paths import resolve_paths


HAMILTON_TOP_LEVEL = {
    "metadata.yaml",
    "skill.md",
    "references",
    "templates",
    "examples",
}
REMOVED_RUNTIME_PATH_PARTS = {
    "adr",
    "aph-status",
    "auto-sync",
    "capture",
    "cursor",
    "generate-view",
    "identity",
    "journal",
    "knowledge",
    "knowledge-lookup",
    "project-context",
    "project-init",
    "prompt-architect",
    "reflect",
    "registry",
    "session-end",
    "session-record",
    "sync",
    "ux-guardian",
    "views",
    "wrap-up",
}
REMOVED_RUNTIME_FILENAMES = {
    "agents-md-template.md",
    "claude-md-template.md",
    "hooks.json",
}
RETIRED_INSTRUCTION_MARKERS = {
    "adapters/cursor",
    "aphelocoma second brain",
    "core/identity",
    "core/journal",
    "core/knowledge",
    "core/projects",
    "deploy cursor",
    "personal context layer",
}
EXPECTED_INSTALLED_STATIC_FILES = {
    "VERSION",
    "install.sh",
    "bin/aph",
    "src/aphelocoma/__init__.py",
    "src/aphelocoma/cli.py",
    "src/aphelocoma/deploy.py",
    "src/aphelocoma/doctor.py",
    "src/aphelocoma/hamilton_state.py",
    "src/aphelocoma/io.py",
    "src/aphelocoma/legacy.py",
    "src/aphelocoma/lifecycle.py",
    "src/aphelocoma/manifest.py",
    "src/aphelocoma/paths.py",
    "adapters/claude-code/scripts/gen-hamilton-crew.py",
    "adapters/codex/scripts/gen-hamilton-crew-codex.py",
}


def shipped_files(root):
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


class HamiltonPackageInventoryTests(unittest.TestCase):
    def test_activation_installs_only_the_explicit_hamilton_runtime(self):
        with tempfile.TemporaryDirectory(
            prefix="aph installed package inventory "
        ) as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            paths = resolve_paths(
                {
                    "HOME": str(home),
                    "APHELOCOMA_ROOT": str(base / "active"),
                },
                tool_root=REPOSITORY,
            )

            activate_release(REPOSITORY, paths)

            installed = paths.root / "tool"
            expected = EXPECTED_INSTALLED_STATIC_FILES | {
                "skills/aph-hamilton/" + relative
                for relative in shipped_files(
                    REPOSITORY / "skills" / "aph-hamilton"
                )
            }
            self.assertEqual(shipped_files(installed), expected)
            self.assertEqual(
                {path.name for path in installed.iterdir()},
                {"VERSION", "install.sh", "bin", "src", "skills", "adapters"},
            )
            for forbidden in (
                ".aphelocoma",
                ".claude",
                ".git",
                ".gitignore",
                ".omc",
                ".superpowers",
                "brainstorms.md",
                "CLAUDE.md",
                "docs",
                "README.md",
                "tests",
                "tests/fixtures/legacy",
            ):
                with self.subTest(forbidden=forbidden):
                    self.assertFalse((installed / forbidden).exists())
            for executable in (
                "install.sh",
                "bin/aph",
                "adapters/claude-code/scripts/gen-hamilton-crew.py",
                "adapters/codex/scripts/gen-hamilton-crew-codex.py",
            ):
                with self.subTest(mode=executable):
                    self.assertEqual(
                        (installed / executable).stat().st_mode & 0o777,
                        (REPOSITORY / executable).stat().st_mode & 0o777,
                    )

    def test_skills_tree_contains_only_hamilton(self):
        skill_names = sorted(
            {
                relative.split("/", 1)[0]
                for relative in shipped_files(REPOSITORY / "skills")
            }
        )

        self.assertEqual(skill_names, ["aph-hamilton"])

    def test_hamilton_skill_has_only_installable_top_level_assets(self):
        hamilton = REPOSITORY / "skills" / "aph-hamilton"
        top_level = {
            path.name
            for path in hamilton.iterdir()
            if path.name != "__pycache__"
        }

        self.assertEqual(top_level, HAMILTON_TOP_LEVEL)

    def test_adapters_are_only_the_hamilton_generators(self):
        adapter_files = shipped_files(REPOSITORY / "adapters")
        self.assertEqual(
            adapter_files,
            {
                "claude-code/scripts/gen-hamilton-crew.py",
                "codex/scripts/gen-hamilton-crew-codex.py",
            },
        )
        self.assertFalse(
            any(relative.startswith("cursor/") for relative in adapter_files)
        )

    def test_removed_runtime_assets_are_absent_from_shipped_paths(self):
        package_roots = (
            REPOSITORY / "bin",
            REPOSITORY / "src",
            REPOSITORY / "skills",
            REPOSITORY / "adapters",
        )
        offenders = []
        for root in package_roots:
            for relative in shipped_files(root):
                path = Path(relative)
                if (
                    REMOVED_RUNTIME_PATH_PARTS.intersection(path.parts)
                    or path.name in REMOVED_RUNTIME_FILENAMES
                ):
                    offenders.append(
                        (root.relative_to(REPOSITORY) / path).as_posix()
                    )

        self.assertEqual(offenders, [])

    def test_root_runtime_instructions_do_not_reactivate_retired_product(self):
        offenders = {}
        for name in ("AGENTS.md", "CLAUDE.md"):
            instruction_file = REPOSITORY / name
            if not instruction_file.is_file():
                continue
            content = instruction_file.read_text(encoding="utf-8").lower()
            matched = sorted(
                marker
                for marker in RETIRED_INSTRUCTION_MARKERS
                if marker in content
            )
            if matched:
                offenders[name] = matched

        self.assertEqual(offenders, {})

    def test_context_runtime_and_private_exports_are_not_packaged(self):
        for relative in (
            "core",
            "views",
        ):
            with self.subTest(path=relative):
                self.assertFalse((REPOSITORY / relative).exists())

        ignored = {
            line.strip()
            for line in (REPOSITORY / ".gitignore").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue(
            {"core/", "views/", ".cursor/"}.isdisjoint(ignored),
            "Context, view, and Cursor export paths must not be hidden as package inputs.",
        )

    def test_supported_targets_are_claude_and_codex_only(self):
        self.assertEqual(TOOLS, ("claude", "codex"))


if __name__ == "__main__":
    unittest.main()
