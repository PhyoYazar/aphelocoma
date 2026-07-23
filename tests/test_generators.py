import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
REFERENCES = REPOSITORY / "skills" / "aph-hamilton" / "references"
CLAUDE_GENERATOR = (
    REPOSITORY / "adapters" / "claude-code" / "scripts" / "gen-hamilton-crew.py"
)
CODEX_GENERATOR = (
    REPOSITORY / "adapters" / "codex" / "scripts" / "gen-hamilton-crew-codex.py"
)


def run_generator(script, *arguments, environment=None):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if environment:
        env.update(environment)
    return subprocess.run(
        [sys.executable, str(script), *map(str, arguments)],
        cwd=str(REPOSITORY),
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


class GeneratorTests(unittest.TestCase):
    def test_generators_refuse_symlinked_output_parents(self):
        with tempfile.TemporaryDirectory(prefix="aph generator parent symlink ") as directory:
            base = Path(directory)
            external_claude = base / "external claude"
            external_codex = base / "external codex"
            external_claude.mkdir()
            external_codex.mkdir()
            (external_claude / "sentinel").write_bytes(b"claude")
            (external_codex / "sentinel").write_bytes(b"codex")
            claude_output = base / "claude-agents"
            codex_home = base / ".codex"
            claude_output.symlink_to(external_claude, target_is_directory=True)
            codex_home.symlink_to(external_codex, target_is_directory=True)

            claude = run_generator(CLAUDE_GENERATOR, REFERENCES, claude_output)
            codex = run_generator(CODEX_GENERATOR, REFERENCES, codex_home)

            self.assertNotEqual(claude.returncode, 0)
            self.assertNotEqual(codex.returncode, 0)
            self.assertIn("symlink", claude.stderr.lower())
            self.assertIn("symlink", codex.stderr.lower())
            self.assertEqual(
                {path.name: path.read_bytes() for path in external_claude.iterdir()},
                {"sentinel": b"claude"},
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in external_codex.iterdir()},
                {"sentinel": b"codex"},
            )

    def test_claude_generator_writes_all_27_agents(self):
        with tempfile.TemporaryDirectory(prefix="aph claude agents ") as directory:
            output = Path(directory) / "agents"

            completed = run_generator(CLAUDE_GENERATOR, REFERENCES, output)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            agents = sorted(output.glob("hamilton-*.md"))
            self.assertEqual(len(agents), 27)
            for agent in agents:
                content = agent.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"), agent)
                self.assertIn("name: hamilton-", content)
                self.assertNotIn("{{", content)

    def test_codex_generator_writes_parseable_named_roles_and_preserves_config(self):
        try:
            import tomllib
        except ImportError:  # pragma: no cover - Python 3.9/3.10 CI
            tomllib = None

        with tempfile.TemporaryDirectory(prefix="aph codex agents ") as directory:
            codex_home = Path(directory) / ".codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_text('model = "user-choice"\n', encoding="utf-8")

            completed = run_generator(CODEX_GENERATOR, REFERENCES, codex_home)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            agents = sorted((codex_home / "agents").glob("hamilton-*.toml"))
            self.assertEqual(len(agents), 27)
            config_text = config.read_text(encoding="utf-8")
            self.assertIn('model = "user-choice"', config_text)
            self.assertEqual(config_text.count("[agents.hamilton-"), 27)
            self.assertEqual(
                config_text.count("# >>> aphelocoma hamilton crew >>>"),
                1,
            )
            if tomllib is not None:
                for agent in agents:
                    parsed = tomllib.loads(agent.read_text(encoding="utf-8"))
                    self.assertTrue(parsed["name"].startswith("hamilton-"))
                    self.assertTrue(parsed["developer_instructions"])
                parsed_config = tomllib.loads(config_text)
                self.assertEqual(len(parsed_config["agents"]), 27)

    def test_claude_partial_failure_leaves_existing_output_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="aph claude generator failure ") as directory:
            output = Path(directory) / "agents"
            output.mkdir()
            existing = output / "hamilton-cto.md"
            unrelated = output / "personal.md"
            existing.write_bytes(b"custom cto\n")
            unrelated.write_bytes(b"personal\n")
            before = {path.name: path.read_bytes() for path in output.iterdir()}

            completed = run_generator(
                CLAUDE_GENERATOR,
                REFERENCES,
                output,
                environment={"APHELOCOMA_FAIL_GENERATOR_AFTER": "3"},
            )

            self.assertNotEqual(completed.returncode, 0)
            after = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(after, before)

    def test_codex_partial_failure_preserves_agents_and_config_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="aph codex generator failure ") as directory:
            codex_home = Path(directory) / ".codex"
            agents = codex_home / "agents"
            agents.mkdir(parents=True)
            existing = agents / "hamilton-cto.toml"
            config = codex_home / "config.toml"
            existing.write_bytes(b'name = "custom"\n')
            config.write_bytes(b'model = "keep"\n')
            before_agent = existing.read_bytes()
            before_config = config.read_bytes()

            completed = run_generator(
                CODEX_GENERATOR,
                REFERENCES,
                codex_home,
                environment={"APHELOCOMA_FAIL_GENERATOR_AFTER": "3"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(existing.read_bytes(), before_agent)
            self.assertEqual(config.read_bytes(), before_config)
            self.assertEqual(list(agents.iterdir()), [existing])

    def test_codex_generator_refuses_config_symlink_without_changing_target(self):
        with tempfile.TemporaryDirectory(prefix="aph codex generator symlink ") as directory:
            base = Path(directory)
            codex_home = base / ".codex"
            codex_home.mkdir()
            external = base / "external.toml"
            external.write_bytes(b'model = "external"\n')
            config = codex_home / "config.toml"
            config.symlink_to(external)

            completed = run_generator(CODEX_GENERATOR, REFERENCES, codex_home)

            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(config.is_symlink())
            self.assertEqual(external.read_bytes(), b'model = "external"\n')
            self.assertFalse((codex_home / "agents").exists())
