#!/usr/bin/env python3
"""Generate Hamilton native crew agents from the role library + agent-template.md.

Usage: gen-hamilton-crew.py <hamilton-references-dir> <output-agents-dir>

Fills references/agent-template.md once per role file: implementer roles get the
build contract, look-only roles (no Write/Edit in their `tools:`) get the reviewer
contract. model/effort come from references/settings.default.yaml (omitted -> the
agent inherits the session). Output files are DERIVED — never hand-edit them; re-run
to regenerate. Called by `aph deploy claude` and the /deploy skill.
"""
import os, re, sys, glob


def parse_settings(path):
    """Parse the `models:` and `effort:` maps from a settings.yaml (stdlib only)."""
    models, effort = {}, {}
    cur = None
    if not os.path.exists(path):
        return models, effort
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^models:", line):
            cur = models; continue
        if re.match(r"^effort:", line):
            cur = effort; continue
        if re.match(r"^\S", line):          # any other top-level key ends the block
            cur = None; continue
        m = re.match(r"^\s+([\w-]+):\s*([^#]+?)\s*(?:#.*)?$", line)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2).strip()
    return models, effort


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


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: gen-hamilton-crew.py <references-dir> <output-agents-dir>")
    ref_dir, out_dir = sys.argv[1], sys.argv[2]
    template = open(os.path.join(ref_dir, "agent-template.md"), encoding="utf-8").read()
    fm_block, impl_block, rev_block = (block(template, "FRONTMATTER"),
                                       block(template, "IMPLEMENTER"),
                                       block(template, "REVIEWER"))
    models, effort = parse_settings(os.path.join(ref_dir, "settings.default.yaml"))

    os.makedirs(out_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(out_dir, "hamilton-*.md")):
        os.remove(stale)

    rows = []
    for rf in sorted(glob.glob(os.path.join(ref_dir, "roles", "*.md"))):
        role_body = open(rf, encoding="utf-8").read()
        rid = frontmatter_field(role_body, "id") or os.path.splitext(os.path.basename(rf))[0]
        title = frontmatter_field(role_body, "title") or rid
        tools = frontmatter_field(role_body, "tools")
        is_reviewer = bool(tools) and "Write" not in tools and "Edit" not in tools
        agent = "hamilton-" + rid.replace("#", "-")
        tools_line = "tools: " + (tools if tools else "Read, Write, Edit, Bash, Grep, Glob")
        mdl = models.get(rid, models.get("default"))
        eff = effort.get(rid, effort.get("default"))
        subs = {
            "{{AGENT_NAME}}": agent,
            "{{ROLE_TITLE}}": title,
            "{{ROLE_ID}}": rid,
            "{{ROLE_BLURB}}": ("reviews one in_review task read-only and returns findings + a verdict"
                               if is_reviewer else
                               "builds one assigned task and returns a structured result"),
            "{{TOOLS_LINE}}": tools_line,
            "{{MODEL_LINE}}": ("model: " + mdl) if mdl else "",
            "{{EFFORT_LINE}}": ("effort: " + eff) if eff else "",
            "{{ROLE_BODY}}": role_body,
        }
        fm, body = fm_block, (rev_block if is_reviewer else impl_block)
        for k, v in subs.items():
            fm = fm.replace(k, v)
            body = body.replace(k, v)
        fm = "\n".join(l for l in fm.splitlines() if l.strip() != "")   # drop omitted model/effort lines
        open(os.path.join(out_dir, agent + ".md"), "w", encoding="utf-8").write(
            fm + "\n\n" + body.strip() + "\n")
        rows.append((rid, mdl or "inherit", eff or "inherit",
                     "look-only" if is_reviewer else "build"))

    width = max((len(r[0]) for r in rows), default=4)
    print("Hamilton crew: %d agents -> %s" % (len(rows), out_dir))
    print("  %-*s  %-8s  %-8s  %s" % (width, "role", "model", "effort", "scope"))
    for r in rows:
        print("  %-*s  %-8s  %-8s  %s" % (width, r[0], r[1], r[2], r[3]))


if __name__ == "__main__":
    main()
