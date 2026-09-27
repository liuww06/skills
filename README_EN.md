# leo-skills

English | [中文](README.md)

A single-repo plugin marketplace consumable by **Claude Code**, **OpenAI Codex**, and **ZCode** (Zhipu) — plugin sources are written once and installed everywhere.

## Plugins

| Plugin | Purpose |
| --- | --- |
| [hello-world](plugins/hello-world/skills/greeting/SKILL.md) | Minimal example of a skill and command entry point. |
| [invest](plugins/invest/) | A-share investment research across nine areas, including markets, companies, industries and earnings. |
| [image](plugins/image/skills/photo-restoration/SKILL.md) | High-fidelity photo restoration that preserves people and the original scene. |
| [dotnet](plugins/dotnet/skills/dotnet-scaffold/SKILL.md) | New .NET libraries, desktop apps, web apps and services, simple by default with optional Clean Architecture, DDD, MVVM and microservices. |

## Repository layout

```text
skills/
├── marketplace.json                # ZCode marketplace index (repo root)
├── .claude-plugin/
│   └── marketplace.json            # Claude Code marketplace index
├── .agents/plugins/
│   └── marketplace.json            # Codex marketplace index
├── AWESOME.md                      # curated open-source Agent Skills & context-rules list
├── plugins/
│   ├── hello-world/                # example plugin & template for new plugins
│   │   ├── .zcode-plugin/plugin.json    # ZCode manifest (read first)
│   │   ├── .claude-plugin/plugin.json   # Claude Code manifest
│   │   ├── .codex-plugin/plugin.json    # Codex manifest
│   │   ├── skills/greeting/SKILL.md     # skill (all three tools)
│   │   └── commands/hello.md            # slash command
│   ├── invest/                     # A-share investment research: 9 skills + 9 shortcut commands
│   │   ├── .zcode-plugin/plugin.json    # three identical manifests
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .codex-plugin/plugin.json
│   │   ├── references/                  # shared across skills: data sources, conventions
│   │   ├── skills/                      # 9 Chinese-named skills: 市场调研 / 公司研究 / 板块分析 /
│   │   │                                # 行业分析 / 宏观分析 / 技术分析 / 财报解读 / 投资决策 / 国际局势
│   │   └── commands/                    # /invest:market shortcuts (ignored by Codex)
│   ├── image/                      # image processing: photo restoration
│   │   ├── .zcode-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .codex-plugin/plugin.json
│   │   ├── skills/photo-restoration/SKILL.md
│   │   └── commands/restore.md
│   └── dotnet/                     # new .NET codebases: 1 skill + 1 command
│       ├── .zcode-plugin/plugin.json
│       ├── .claude-plugin/plugin.json
│       ├── .codex-plugin/plugin.json    # includes Codex interface metadata
│       ├── skills/dotnet-scaffold/     # entry, references and output assets
│       └── commands/dotnet-new.md      # Codex uses the skill instead
├── scripts/validate.sh             # structural validation
└── scripts/update.sh               # refresh cache & verify in one shot
```

Design notes:

- Plugin sources (`skills/`, `commands/`, `hooks/hooks.json`, `.mcp.json`) share one format across all three tools — write once.
- Each plugin ships three manifests with matching shared metadata: `.zcode-plugin/plugin.json` (ZCode), `.claude-plugin/plugin.json` (Claude Code), and `.codex-plugin/plugin.json` (Codex). Host-specific fields may differ; dotnet includes Codex interface metadata. ZCode also supports the Claude manifest fallback.
- Codex uses its own manifest (`.codex-plugin/plugin.json`) and marketplace index (`.agents/plugins/marketplace.json`).

## Component compatibility

| Component | Claude Code | Codex | ZCode |
| --- | :---: | :---: | :---: |
| `skills/*/SKILL.md` | ✅ | ✅ | ✅ |
| `hooks/hooks.json` | ✅ | ✅ | ✅ |
| `.mcp.json` | ✅ | ✅ | ✅ |
| `commands/*.md` | ✅ | ➖ ignored | ✅ |
| `agents/*.md` | ✅ | ➖ ignored | ✅ |

## Curated resources

[AWESOME.md](AWESOME.md) (in Chinese) curates high-quality open-source Agent Skills — grouped by domain: software engineering, testing, DevOps, data, security, science, and more — plus **Agent context rules**: engineering conventions, security guardrails, and prompt architecture to put into AGENTS.md / CLAUDE.md. Every entry is verified and annotated as a starting point for adoption and learning.

## Install

Replace `<github-user>/skills` below with the actual GitHub location of this repo, or use a local path `/path/to/skills` to try it out.

### Claude Code

```text
/plugin marketplace add <github-user>/skills
/plugin install hello-world@leo-skills
/plugin install invest@leo-skills
/plugin install image@leo-skills
/plugin install dotnet@leo-skills
```

The `hello` command appears under `/`, and the `greeting` skill triggers automatically when relevant. The `invest` plugin adds shortcuts like `/invest:market` and `/invest:stock <ticker>`, plus 9 skills (market research, company research, sector, industry, macro, technical, earnings, investment decision, geopolitics) that trigger automatically in relevant conversations. The `image` plugin adds `/image:restore <image path>` and a `photo-restoration` skill (conservative high-fidelity restoration: damage repair, two-phase workflow, fidelity over enhancement) that triggers on photo-restoration requests.

### ZCode

Open Settings → Plugins → **Create** → **Add plugin marketplace**, paste this repo's GitHub address (`owner/repo` or link), a Git URL, or a local directory path, then install `hello-world` (and `invest`, `image`, `dotnet`) from the **Personal** section. ZCode natively loads Claude Code plugin marketplaces, so no extra adaptation is needed.

### Codex

```text
codex plugin marketplace add <github-user>/skills
codex plugin install hello-world
codex plugin install invest
codex plugin install image
```

Check `codex plugin --help` for the exact subcommands in your Codex version (the Codex plugin CLI is still evolving quickly). Codex ignores `commands/` (no slash commands), but `invest`'s 9 skills and `image`'s photo-restoration skill still trigger normally.

## Adding a new plugin

1. Copy `plugins/hello-world/` to `plugins/<your-plugin-name>/` (name must match `^[a-z0-9][a-z0-9._-]{0,127}$`).
2. Update all three manifests inside the plugin: `.zcode-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.codex-plugin/plugin.json` (keep `name`, `version`, and `description` in sync).
3. Add an entry to each of the three marketplace indexes: `.claude-plugin/marketplace.json` and the root `marketplace.json` (keep these two identical), plus `.agents/plugins/marketplace.json` (note Codex's `source` uses the object form `{"source": "local", "path": "./plugins/<name>"}`).
4. Run `bash scripts/validate.sh` to validate.

Release note: ZCode compares the marketplace entry's `version` against the installed `plugin.json`, so bump `version` in all three plugin manifests and all three marketplace entries (six places total) after changes, or updates won't be detected.

## Local debug loop

Installing **copies** the plugin into `~/.claude/plugins/cache/` — repo edits are not picked up automatically; a repeated `install` is a no-op, and `update` only compares version numbers. After editing a plugin or skill, refresh and verify in one shot:

```bash
bash scripts/update.sh               # validate → force-refresh cache → verify each skill/command in fresh sessions
bash scripts/update.sh hello-world   # a single plugin
```

The script: ① runs `scripts/validate.sh`; ② ensures this repo is registered as a local marketplace; ③ force-refreshes the cache via `uninstall + install`; ④ slash-invokes every skill and command in a clean `claude -p` session, requiring a verification marker in the reply — it exits 0 only when everything passes.

For zero-reinstall iteration, symlink the plugin into your personal skills dir instead — edits apply on the next session; remove the link when done:

```bash
ln -sfn /path/to/skills/plugins/<plugin> ~/.claude/skills/<plugin>
```

Additional dotnet validation commands:

```text
python scripts/validate-dotnet.py
python scripts/test-dotnet-scaffold.py
node --experimental-vm-modules scripts/test-dotnet-performance.mjs
```

Static checks require PyYAML. Generation tests require the .NET SDK and run in temporary directories; add `--online` for NuGet-dependent cases. Performance-script checks use mock transport. Recipe checks, fresh-session skill selection and actual load tests are separate validations.

## License

[MIT](LICENSE)
