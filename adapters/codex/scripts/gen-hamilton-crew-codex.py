#!/usr/bin/env python3
"""Generate all Codex Hamilton roles and one transactionally managed config block."""

import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


BLOCK_START = "# >>> aphelocoma hamilton crew >>>"
BLOCK_END = "# <<< aphelocoma hamilton crew <<<"


def block(template, name):
    match = re.search(r"<<<%s\n(.*?)\n%s>>>" % (name, name), template, re.S)
    if not match:
        raise ValueError("agent-template.md is missing the <<<%s>>> block" % name)
    return match.group(1)


def frontmatter_field(text, key):
    frontmatter = re.search(r"^---\n(.*?)\n---", text, re.S)
    scope = frontmatter.group(1) if frontmatter else text
    match = re.search(r"^%s:\s*(.+)$" % re.escape(key), scope, re.M)
    return match.group(1).strip() if match else None


def toml_str(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_multiline(value):
    if "'''" not in value:
        return "'''\n" + value + "\n'''"
    return '"""\n' + value.replace("\\", "\\\\").replace('"""', '\\"""') + '\n"""'


def _locate_block(content):
    starts = content.count(BLOCK_START)
    ends = content.count(BLOCK_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ValueError("Codex config has ambiguous Aphelocoma managed-block markers")
    start = content.index(BLOCK_START)
    end = content.index(BLOCK_END, start) + len(BLOCK_END)
    if end < len(content) and content[end] == "\n":
        end += 1
    return start, end


def _put_block(content, managed):
    located = _locate_block(content)
    if located is None:
        prefix = content.rstrip("\n")
        return prefix + ("\n\n" if prefix else "") + managed
    start, end = located
    return content[:start] + managed + content[end:]


def _failure_limit():
    value = os.environ.get("APHELOCOMA_FAIL_GENERATOR_AFTER")
    if not value:
        return None
    try:
        limit = int(value)
    except ValueError as error:
        raise ValueError("APHELOCOMA_FAIL_GENERATOR_AFTER must be an integer") from error
    if limit < 1:
        raise ValueError("APHELOCOMA_FAIL_GENERATOR_AFTER must be positive")
    return limit


def render(reference_dir, current_config):
    template = (reference_dir / "agent-template.md").read_text(encoding="utf-8")
    implementer_block = block(template, "IMPLEMENTER")
    reviewer_block = block(template, "REVIEWER")
    failure_limit = _failure_limit()
    rendered = {}
    entries = []
    rows = []
    for index, role_file in enumerate(sorted((reference_dir / "roles").glob("*.md")), 1):
        role_body = role_file.read_text(encoding="utf-8")
        role_id = frontmatter_field(role_body, "id") or role_file.stem
        title = frontmatter_field(role_body, "title") or role_id
        tools = frontmatter_field(role_body, "tools")
        reviewer = bool(tools) and "Write" not in tools and "Edit" not in tools
        agent = "hamilton-" + role_id.replace("#", "-")
        blurb = (
            "reviews one in_review task read-only and returns findings + a verdict"
            if reviewer
            else "builds one assigned task and returns a structured result"
        )
        body = reviewer_block if reviewer else implementer_block
        for key, value in {
            "{{ROLE_TITLE}}": title,
            "{{ROLE_ID}}": role_id,
            "{{ROLE_BODY}}": role_body,
        }.items():
            body = body.replace(key, value)
        rendered[agent + ".toml"] = "\n".join(
            [
                "# DERIVED by gen-hamilton-crew-codex.py — do not hand-edit; "
                "re-run `aph deploy codex`.",
                "name = " + toml_str(agent),
                "description = "
                + toml_str(
                    "%s — Hamilton crew member; %s. Dispatched by the Hamilton orchestrator."
                    % (title, blurb)
                ),
                "nickname_candidates = [" + toml_str(title) + "]",
                "",
                "developer_instructions = " + toml_multiline(body.strip()),
                "",
            ]
        )
        entries.append(
            '[agents.%s]\nconfig_file = "./agents/%s.toml"' % (agent, agent)
        )
        rows.append((role_id, title, "look-only" if reviewer else "build"))
        if failure_limit is not None and index >= failure_limit:
            raise RuntimeError("injected partial generator failure")
    if len(rendered) != 27:
        raise ValueError("Hamilton role inventory must generate exactly 27 Codex agents")
    managed = BLOCK_START + "\n" + "\n\n".join(entries) + "\n" + BLOCK_END + "\n"
    return rendered, _put_block(current_config, managed), rows


def commit(codex_home, rendered, config_content):
    agents_dir = codex_home / "agents"
    config_path = codex_home / "config.toml"
    codex_home.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)
    transaction = Path(
        tempfile.mkdtemp(prefix=".hamilton-codex-", dir=str(codex_home))
    )
    staged_agents = transaction / "staged-agents"
    previous_agents = transaction / "previous-agents"
    staged_agents.mkdir()
    previous_agents.mkdir()
    staged_config = transaction / "config.toml"
    staged_config.write_text(config_content, encoding="utf-8")
    for name, content in rendered.items():
        (staged_agents / name).write_text(content, encoding="utf-8")

    moved_agents = []
    installed_agents = []
    previous_config = transaction / "previous-config.toml"
    config_existed = config_path.exists() or config_path.is_symlink()
    try:
        for existing in sorted(agents_dir.glob("hamilton-*.toml")):
            destination = previous_agents / existing.name
            os.replace(str(existing), str(destination))
            moved_agents.append((destination, existing))
        if config_existed:
            os.replace(str(config_path), str(previous_config))
        os.replace(str(staged_config), str(config_path))
        for candidate in sorted(staged_agents.iterdir()):
            destination = agents_dir / candidate.name
            os.replace(str(candidate), str(destination))
            installed_agents.append(destination)
    except Exception:
        for path in installed_agents:
            path.unlink(missing_ok=True)
        if config_path.exists() or config_path.is_symlink():
            config_path.unlink()
        if config_existed and previous_config.exists():
            os.replace(str(previous_config), str(config_path))
        for source, destination in reversed(moved_agents):
            os.replace(str(source), str(destination))
        raise
    finally:
        shutil.rmtree(transaction, ignore_errors=True)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: gen-hamilton-crew-codex.py <references-dir> <codex-home>"
        )
    reference_dir = Path(sys.argv[1])
    codex_home = Path(sys.argv[2])
    config_path = codex_home / "config.toml"
    try:
        if codex_home.is_symlink():
            raise ValueError("Codex home symlink was preserved")
        if (codex_home / "agents").is_symlink():
            raise ValueError("Codex agents directory symlink was preserved")
        if config_path.is_symlink():
            raise ValueError("Codex config symlink was preserved")
        current_config = (
            config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        )
        rendered, config_content, rows = render(reference_dir, current_config)
        commit(codex_home, rendered, config_content)
    except Exception as error:
        print("Error: %s" % error, file=sys.stderr)
        return 1

    width = max((len(row[0]) for row in rows), default=4)
    print(
        "Hamilton Codex crew: %d roles -> %s (+ managed block in %s)"
        % (len(rows), codex_home / "agents", config_path)
    )
    print("  %-*s  %-28s  %s" % (width, "role", "display name", "scope"))
    for row in rows:
        print("  %-*s  %-28s  %s" % (width, row[0], row[1], row[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
