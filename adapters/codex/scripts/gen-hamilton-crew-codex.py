#!/usr/bin/env python3
"""Generate Hamilton crew agent roles for Codex from the role library + agent-template.md.

Usage: gen-hamilton-crew-codex.py <hamilton-references-dir> <codex-home>

Codex's collab tools (`spawn_agent`) accept an `agent_type` that maps to `[agents.<name>]`
sections in <codex-home>/config.toml, each pointing at a role .toml with the display
nickname and developer instructions. This gives Hamilton dispatches a visible role name
(instead of a bare thread id) plus the role contract baked into the worker.

Writes <codex-home>/agents/hamilton-<role>.toml per role (implementer or reviewer body
from agent-template.md, same as the Claude Code crew) and maintains ONE managed block in
<codex-home>/config.toml between these markers (everything else is left untouched):

    # >>> aphelocoma hamilton crew >>>
    # <<< aphelocoma hamilton crew <<<

Per-role model/effort are NOT baked in here — the orchestrator passes them per spawn
(spawn_agent's `model` / `reasoning_effort` args) from the project's settings.yaml, so
overrides apply without regenerating. Output files are DERIVED — never hand-edit; re-run
to regenerate. Called by `aph deploy codex` and the /deploy skill.
"""
import os, re, sys, glob

BLOCK_START = "# >>> aphelocoma hamilton crew >>>"
BLOCK_END = "# <<< aphelocoma hamilton crew <<<"


def block(template, name):
    m = re.search(r"<<<%s\n(.*?)\n%s>>>" % (name, name), template, re.S)
    if not m:
        sys.exit("agent-template.md is missing the <<<%s>>> block" % name)
    return m.group(1)


def frontmatter_field(text, key):
    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    scope = fm.group(1) if fm else text
    m = re.search(r"^%s:\s*(.+)$" % re.escape(key), scope, re.M)
    return m.group(1).strip() if m else None


def toml_str(s):
    """Single-line TOML basic string."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_multiline(s):
    """Multi-line TOML literal string; falls back to escaping if ''' appears."""
    if "'''" not in s:
        return "'''\n" + s + "\n'''"
    return '"""\n' + s.replace("\\", "\\\\").replace('"""', '\\"""') + '\n"""'


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: gen-hamilton-crew-codex.py <references-dir> <codex-home>")
    ref_dir, codex_home = sys.argv[1], sys.argv[2]
    config_path = os.path.join(codex_home, "config.toml")
    agents_dir = os.path.join(codex_home, "agents")

    template = open(os.path.join(ref_dir, "agent-template.md"), encoding="utf-8").read()
    impl_block, rev_block = block(template, "IMPLEMENTER"), block(template, "REVIEWER")

    os.makedirs(agents_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(agents_dir, "hamilton-*.toml")):
        os.remove(stale)

    rows, config_entries = [], []
    for rf in sorted(glob.glob(os.path.join(ref_dir, "roles", "*.md"))):
        role_body = open(rf, encoding="utf-8").read()
        rid = frontmatter_field(role_body, "id") or os.path.splitext(os.path.basename(rf))[0]
        title = frontmatter_field(role_body, "title") or rid
        tools = frontmatter_field(role_body, "tools")
        is_reviewer = bool(tools) and "Write" not in tools and "Edit" not in tools
        agent = "hamilton-" + rid.replace("#", "-")
        blurb = ("reviews one in_review task read-only and returns findings + a verdict"
                 if is_reviewer else
                 "builds one assigned task and returns a structured result")
        body = rev_block if is_reviewer else impl_block
        for k, v in {"{{ROLE_TITLE}}": title, "{{ROLE_ID}}": rid,
                     "{{ROLE_BODY}}": role_body}.items():
            body = body.replace(k, v)

        toml = "\n".join([
            "# DERIVED by gen-hamilton-crew-codex.py — do not hand-edit; re-run `aph deploy codex`.",
            "name = " + toml_str(agent),
            "description = " + toml_str(
                "%s — Hamilton crew member; %s. Dispatched by the Hamilton orchestrator."
                % (title, blurb)),
            "nickname_candidates = [" + toml_str(title) + "]",
            "",
            "developer_instructions = " + toml_multiline(body.strip()),
            "",
        ])
        open(os.path.join(agents_dir, agent + ".toml"), "w", encoding="utf-8").write(toml)
        config_entries.append("[agents.%s]\nconfig_file = \"./agents/%s.toml\"" % (agent, agent))
        rows.append((rid, title, "look-only" if is_reviewer else "build"))

    managed = BLOCK_START + "\n" + "\n\n".join(config_entries) + "\n" + BLOCK_END + "\n"
    config = open(config_path, encoding="utf-8").read() if os.path.exists(config_path) else ""
    pattern = re.compile(re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END) + r"\n?", re.S)
    if pattern.search(config):
        config = pattern.sub(managed, config)
    else:
        config = config.rstrip("\n") + ("\n\n" if config.strip() else "") + managed
    open(config_path, "w", encoding="utf-8").write(config)

    width = max((len(r[0]) for r in rows), default=4)
    print("Hamilton Codex crew: %d roles -> %s (+ managed block in %s)"
          % (len(rows), agents_dir, config_path))
    print("  %-*s  %-28s  %s" % (width, "role", "display name", "scope"))
    for r in rows:
        print("  %-*s  %-28s  %s" % (width, r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
