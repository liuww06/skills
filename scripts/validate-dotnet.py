#!/usr/bin/env python3
"""Static checks for dotnet packaging, resource reachability and output assets.

Requires PyYAML. Does not claim host schema or runtime discovery validation.
"""
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/dotnet"
SKILL = PLUGIN / "skills/dotnet-scaffold"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"Missing frontmatter: {path}")
    return yaml.safe_load(text.split("---", 2)[1])


def main():
    manifests = [json.loads((PLUGIN / host / "plugin.json").read_text(encoding="utf-8"))
                 for host in (".codex-plugin", ".claude-plugin", ".zcode-plugin")]
    for key in ("name", "version", "description", "author", "license", "keywords"):
        require(all(m[key] == manifests[0][key] for m in manifests), f"Manifest mismatch: {key}")
    require(manifests[0]["name"] == PLUGIN.name, "Plugin name/path mismatch")
    require(re.fullmatch(r"\d+\.\d+\.\d+", manifests[0]["version"]), "Invalid release version")
    for index in ("marketplace.json", ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        entries = json.loads((ROOT / index).read_text(encoding="utf-8"))["plugins"]
        matches = [e for e in entries if e["name"] == "dotnet"]
        require(len(matches) == 1, f"Expected one dotnet entry: {index}")
        entry = matches[0]
        source = entry["source"]
        if isinstance(source, dict):
            require(source["source"] == "local", "Invalid Codex source")
            require(entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "Invalid policy")
            require(entry["category"] == "Productivity", "Invalid Codex category")
            source = source["path"]
        require(source == "./plugins/dotnet", f"Invalid source in {index}")
        require(entry["version"] == manifests[0]["version"], f"Version mismatch: {index}")
    require((ROOT / "marketplace.json").read_bytes() == (ROOT / ".claude-plugin/marketplace.json").read_bytes(), "ZCode/Claude indexes differ")
    meta = frontmatter(SKILL / "SKILL.md")
    require(meta["name"] == SKILL.name and bool(meta["description"]), "Invalid Skill metadata")
    require(bool(frontmatter(PLUGIN / "commands/dotnet-new.md")["description"]), "Invalid command")
    ui = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))
    require("$dotnet-scaffold" in ui["interface"]["default_prompt"], "UI prompt must name Skill")
    require(ui.get("policy", {}).get("allow_implicit_invocation", True), "Implicit discovery disabled")

    # Follow local Markdown links from the entrypoint; ensure all shipped references/assets are reachable.
    seen = set()
    pending = [SKILL / "SKILL.md"]
    while pending:
        path = pending.pop().resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"[a-z]+://", link) or link.startswith("#"):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            require(target.is_relative_to(SKILL.resolve()), f"Resource outside skill: {link}")
            require(target.is_file(), f"Broken link in {path.name}: {link}")
            pending.append(target)
    for directory in ("references", "assets"):
        for path in (SKILL / directory).rglob("*"):
            if path.is_file():
                require(path.resolve() in seen, f"Unreachable resource: {path}")
    for path in SKILL.rglob("*"):
        if path.is_file():
            require("[TODO:" not in path.read_text(encoding="utf-8"), f"Unfinished scaffold: {path}")
    config = SKILL / "assets/config"
    sdk_template = (config / "global.json.template").read_text(encoding="utf-8")
    require(re.findall(r"\{\{[^}]+\}\}", sdk_template) == ["{{SDK_VERSION}}"], "Unexpected placeholders")
    sdk = json.loads(sdk_template.replace("{{SDK_VERSION}}", "10.0.400"))["sdk"]
    require(sdk["rollForward"] == "latestFeature" and sdk["allowPrerelease"] is False, "Invalid SDK strategy")
    props = ET.parse(config / "Directory.Build.props.template").getroot()
    require(props.find(".//TargetFramework") is None and props.find(".//TreatWarningsAsErrors") is None, "Unexpected global policy")
    packages = ET.parse(config / "Directory.Packages.props.template").getroot()
    require(packages.findtext(".//ManagePackageVersionsCentrally") == "true", "CPM not enabled")
    print(f"PASS: dotnet manifests/indexes, YAML, {len(seen)} reachable resources, JSON/XML assets")


if __name__ == "__main__":
    main()
