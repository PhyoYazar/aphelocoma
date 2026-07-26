#!/usr/bin/env python3
"""Generate the complete Claude Hamilton crew without partial output."""

import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


def parse_settings(path):
    """Parse the ``models`` and ``effort`` maps with no YAML dependency."""

    models, effort = {}, {}
    current = None
    if not path.exists():
        return models, effort
    with path.open(encoding="utf-8") as stream:
        for raw in stream:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if re.match(r"^models:", line):
                current = models
                continue
            if re.match(r"^effort:", line):
                current = effort
                continue
            if re.match(r"^\S", line):
                current = None
                continue
            match = re.match(r"^\s+([\w-]+):\s*([^#]+?)\s*(?:#.*)?$", line)
            if match and current is not None:
                current[match.group(1)] = match.group(2).strip()
    return models, effort


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


def render_agents(reference_dir):
    template = (reference_dir / "agent-template.md").read_text(encoding="utf-8")
    frontmatter_block = block(template, "FRONTMATTER")
    implementer_block = block(template, "IMPLEMENTER")
    reviewer_block = block(template, "REVIEWER")
    models, effort = parse_settings(reference_dir / "settings.default.yaml")
    failure_limit = _failure_limit()

    rendered = {}
    rows = []
    for index, role_file in enumerate(sorted((reference_dir / "roles").glob("*.md")), 1):
        role_body = role_file.read_text(encoding="utf-8")
        role_id = frontmatter_field(role_body, "id") or role_file.stem
        title = frontmatter_field(role_body, "title") or role_id
        tools = frontmatter_field(role_body, "tools")
        reviewer = bool(tools) and "Write" not in tools and "Edit" not in tools
        agent = "hamilton-" + role_id.replace("#", "-")
        model = models.get(role_id, models.get("default"))
        role_effort = effort.get(role_id, effort.get("default"))
        substitutions = {
            "{{AGENT_NAME}}": agent,
            "{{ROLE_TITLE}}": title,
            "{{ROLE_ID}}": role_id,
            "{{ROLE_BLURB}}": (
                "reviews one in_review task read-only and returns findings + a verdict"
                if reviewer
                else "builds one assigned task and returns a structured result"
            ),
            "{{TOOLS_LINE}}": "tools: "
            + (tools if tools else "Read, Write, Edit, Bash, Grep, Glob"),
            "{{MODEL_LINE}}": ("model: " + model) if model else "",
            "{{EFFORT_LINE}}": ("effort: " + role_effort) if role_effort else "",
            "{{ROLE_BODY}}": role_body,
        }
        frontmatter = frontmatter_block
        body = reviewer_block if reviewer else implementer_block
        for key, value in substitutions.items():
            frontmatter = frontmatter.replace(key, value)
            body = body.replace(key, value)
        frontmatter = "\n".join(
            line for line in frontmatter.splitlines() if line.strip()
        )
        rendered[agent + ".md"] = frontmatter + "\n\n" + body.strip() + "\n"
        rows.append(
            (
                role_id,
                model or "inherit",
                role_effort or "inherit",
                "look-only" if reviewer else "build",
            )
        )
        if failure_limit is not None and index >= failure_limit:
            raise RuntimeError("injected partial generator failure")
    if len(rendered) != 27:
        raise ValueError("Hamilton role inventory must generate exactly 27 Claude agents")
    return rendered, rows


def commit_agents(output_dir, rendered):
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    transaction = Path(
        tempfile.mkdtemp(prefix=".hamilton-claude-", dir=str(output_dir.parent))
    )
    staged = transaction / "staged"
    previous = transaction / "previous"
    staged.mkdir()
    previous.mkdir()
    for name, content in rendered.items():
        (staged / name).write_text(content, encoding="utf-8")

    moved_previous = []
    installed = []
    try:
        for existing in sorted(output_dir.glob("hamilton-*.md")):
            destination = previous / existing.name
            os.replace(str(existing), str(destination))
            moved_previous.append((destination, existing))
        for candidate in sorted(staged.iterdir()):
            destination = output_dir / candidate.name
            os.replace(str(candidate), str(destination))
            installed.append(destination)
    except Exception:
        for path in installed:
            path.unlink(missing_ok=True)
        for source, destination in reversed(moved_previous):
            os.replace(str(source), str(destination))
        raise
    finally:
        shutil.rmtree(transaction, ignore_errors=True)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: gen-hamilton-crew.py <references-dir> <output-agents-dir>"
        )
    reference_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    try:
        if output_dir.is_symlink() or output_dir.parent.is_symlink():
            raise ValueError("Claude agents output symlink was preserved")
        rendered, rows = render_agents(reference_dir)
        commit_agents(output_dir, rendered)
    except Exception as error:
        print("Error: %s" % error, file=sys.stderr)
        return 1

    width = max((len(row[0]) for row in rows), default=4)
    print("Hamilton crew: %d agents -> %s" % (len(rows), output_dir))
    print("  %-*s  %-8s  %-8s  %s" % (width, "role", "model", "effort", "scope"))
    for row in rows:
        print("  %-*s  %-8s  %-8s  %s" % (width, row[0], row[1], row[2], row[3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
