import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
SRC = REPOSITORY / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aphelocoma.io import atomic_write_json, atomic_write_text
from aphelocoma.paths import resolve_paths


class RuntimePathsTests(unittest.TestCase):
    def test_default_root_comes_from_isolated_home(self):
        with tempfile.TemporaryDirectory(prefix="aph user's home ") as directory:
            home = Path(directory)
            paths = resolve_paths({"HOME": str(home)}, tool_root=REPOSITORY)

        self.assertEqual(paths.root, home / ".aphelocoma")
        self.assertEqual(paths.default_legacy_data, home / ".aphelocoma" / "data")
        self.assertEqual(paths.protected_legacy_paths, (paths.default_legacy_data,))

    def test_only_root_override_controls_active_storage(self):
        with tempfile.TemporaryDirectory(prefix="aph path model ") as directory:
            base = Path(directory)
            root = base / "new root's location"
            custom_legacy = base / "old custom location"
            paths = resolve_paths(
                {
                    "HOME": str(base / "home"),
                    "APHELOCOMA_ROOT": str(root),
                    "APHELOCOMA_HOME": str(custom_legacy),
                },
                tool_root=REPOSITORY,
            )

        self.assertEqual(paths.root, root)
        self.assertEqual(paths.legacy_home_override, custom_legacy)
        self.assertIn(custom_legacy, paths.protected_legacy_paths)
        self.assertNotEqual(paths.root, paths.legacy_home_override)

    def test_tilde_in_override_uses_the_supplied_isolated_home(self):
        with tempfile.TemporaryDirectory(prefix="aph home ") as directory:
            home = Path(directory)
            paths = resolve_paths(
                {"HOME": str(home), "APHELOCOMA_ROOT": "~/root with spaces"},
                tool_root=REPOSITORY,
            )

        self.assertEqual(paths.root, home / "root with spaces")

    def test_protected_path_check_uses_path_components_not_string_prefixes(self):
        with tempfile.TemporaryDirectory(prefix="aph containment ") as directory:
            home = Path(directory)
            paths = resolve_paths({"HOME": str(home)}, tool_root=REPOSITORY)

            self.assertTrue(paths.is_legacy_protected(home / ".aphelocoma" / "data"))
            self.assertTrue(paths.is_legacy_protected(home / ".aphelocoma" / "data" / "file"))
            self.assertFalse(paths.is_legacy_protected(home / ".aphelocoma" / "database"))


class AtomicIoTests(unittest.TestCase):
    def test_atomic_text_and_json_writes_support_apostrophe_paths(self):
        with tempfile.TemporaryDirectory(prefix="aph atomic ") as directory:
            base = Path(directory) / "Alex's files"
            text_path = base / "nested" / "state.txt"
            json_path = base / "state.json"

            atomic_write_text(text_path, "first\n")
            atomic_write_text(text_path, "second\n")
            atomic_write_json(json_path, {"z": 1, "a": ["safe"]})

            self.assertEqual(text_path.read_text(encoding="utf-8"), "second\n")
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8")),
                {"a": ["safe"], "z": 1},
            )
            self.assertTrue(json_path.read_text(encoding="utf-8").endswith("\n"))
            self.assertEqual(list(base.glob(".*.tmp")), [])
            self.assertEqual(list((base / "nested").glob(".*.tmp")), [])

    def test_atomic_write_preserves_existing_permissions(self):
        with tempfile.TemporaryDirectory(prefix="aph atomic mode ") as directory:
            target = Path(directory) / "config"
            target.write_text("old", encoding="utf-8")
            target.chmod(0o600)

            atomic_write_text(target, "new")

            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_atomic_write_cleans_temporary_file_when_replace_fails(self):
        with tempfile.TemporaryDirectory(prefix="aph atomic failure ") as directory:
            target = Path(directory) / "config.json"

            with mock.patch("aphelocoma.io.os.replace", side_effect=OSError("injected")):
                with self.assertRaisesRegex(OSError, "injected"):
                    atomic_write_json(target, {"safe": True})

            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])
