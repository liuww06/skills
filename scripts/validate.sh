#!/usr/bin/env bash
#
# validate.sh — structural checks for the leo-skills marketplace repo.
#
# Checks:
#   1. Every manifest JSON parses.
#   2. Every marketplace entry points to an existing plugin directory that has
#      all three manifests (.zcode-plugin/, .claude-plugin/, .codex-plugin/
#      plugin.json), each with a name matching the marketplace entry.
#   3. Every plugin ships at least one skills/<name>/SKILL.md with frontmatter.
#   4. All three marketplace indexes list the same set of plugins, and every
#      directory under plugins/ is listed.
#
# Usage: bash scripts/validate.sh   (works from any directory)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$REPO_ROOT" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
errors = []

def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path.relative_to(root)}")
    except json.JSONDecodeError as e:
        errors.append(f"invalid JSON: {path.relative_to(root)}: {e}")
    return None

marketplaces = {
    "claude": root / ".claude-plugin" / "marketplace.json",
    "zcode": root / "marketplace.json",
    "codex": root / ".agents" / "plugins" / "marketplace.json",
}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

listed = {}
for tool, path in marketplaces.items():
    m = load(path)
    names = set()
    if m is not None:
        for entry in m.get("plugins", []):
            name = entry.get("name", "")
            if not NAME_RE.match(name):
                errors.append(f"[{tool}] bad plugin name: {name!r}")
            names.add(name)

            src = entry.get("source")
            if isinstance(src, str):
                rel = src
            elif isinstance(src, dict) and "path" in src:
                rel = src["path"]
            else:
                errors.append(f"[{tool}] plugin {name}: unsupported source {src!r}")
                continue
            pdir = root / rel
            if not pdir.is_dir():
                errors.append(f"[{tool}] plugin {name}: source dir not found: {rel}")
                continue
            for manifest in (
                ".zcode-plugin/plugin.json",
                ".claude-plugin/plugin.json",
                ".codex-plugin/plugin.json",
            ):
                p = load(pdir / manifest)
                if p is not None and p.get("name") != name:
                    errors.append(
                        f"[{tool}] plugin {name}: name mismatch in {manifest}: {p.get('name')!r}"
                    )
    listed[tool] = names

plugins_dir = root / "plugins"
on_disk = {p.name for p in plugins_dir.iterdir() if p.is_dir()} if plugins_dir.is_dir() else set()
for name in sorted(on_disk):
    pdir = plugins_dir / name
    skills = sorted(pdir.glob("skills/*/SKILL.md"))
    if not skills:
        errors.append(f"plugin {name}: no skills/*/SKILL.md found")
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append(f"plugin {name}: {skill.relative_to(root)}: missing YAML frontmatter")
        elif "description:" not in text.split("---")[1]:
            errors.append(f"plugin {name}: {skill.relative_to(root)}: frontmatter missing description")

ref = listed["claude"]
for tool, names in listed.items():
    if names != ref:
        errors.append(f"[{tool}] marketplace differs from claude index: {sorted(names ^ ref)}")
unlisted = on_disk - ref
if unlisted:
    errors.append(f"plugins/ has dirs not listed in marketplaces: {sorted(unlisted)}")

if errors:
    print("\n".join(f"FAIL: {e}" for e in errors), file=sys.stderr)
    sys.exit(1)
print(f"OK: {len(ref)} plugin(s) validated across 3 marketplaces")
PY
