# leo-skills

一个仓库，三端通用的插件市场：同一份插件源码可被 **Claude Code**、**OpenAI Codex** 和 **ZCode**（智谱）直接安装使用。

A single-repo plugin marketplace consumable by **Claude Code**, **OpenAI Codex**, and **ZCode** — plugin sources are written once and installed everywhere.

## 目录结构 / Repository layout

```text
skills/
├── marketplace.json                # ZCode 市场清单 / ZCode marketplace index (repo root)
├── .claude-plugin/
│   └── marketplace.json            # Claude Code 市场清单 / Claude Code marketplace index
├── .agents/plugins/
│   └── marketplace.json            # Codex 市场清单 / Codex marketplace index
├── plugins/
│   └── hello-world/                # 示例插件，也是新插件的模板 / example plugin & template
│       ├── .zcode-plugin/plugin.json    # ZCode 清单（ZCode 优先读取）/ ZCode manifest (read first)
│       ├── .claude-plugin/plugin.json   # Claude Code 清单 / Claude Code manifest
│       ├── .codex-plugin/plugin.json    # Codex 清单 / Codex manifest
│       ├── skills/greeting/SKILL.md     # 技能（三端通用）/ skill (all three tools)
│       └── commands/hello.md            # 斜杠命令 / slash command
└── scripts/validate.sh             # 结构校验 / structural validation
```

设计要点 / Design notes:

- 插件源码（`skills/`、`commands/`、`hooks/hooks.json`、`.mcp.json`）三端格式通用，只写一份。
  Plugin sources are written once; the component formats are shared.
- 每个插件维护三份内容一致的清单：`.zcode-plugin/plugin.json`（ZCode 推荐位置，查找优先级最高）、`.claude-plugin/plugin.json`（Claude Code）、`.codex-plugin/plugin.json`（Codex）。ZCode 也兼容 `.claude-plugin/` 回退，但本仓库采用其推荐方式；若某插件需要 ZCode 专属配置（如 `userConfig`），改 `.zcode-plugin/` 那份即可。
  Each plugin ships three identical manifests; ZCode reads `.zcode-plugin/plugin.json` first, and ZCode-specific options (e.g. `userConfig`) go in that copy.
- Codex 使用自己的清单（`.codex-plugin/plugin.json`）与市场索引（`.agents/plugins/marketplace.json`）。
  Codex uses its own manifest and index format.

## 组件兼容矩阵 / Component compatibility

| 组件 Component | Claude Code | Codex | ZCode |
| --- | :---: | :---: | :---: |
| `skills/*/SKILL.md` | ✅ | ✅ | ✅ |
| `hooks/hooks.json` | ✅ | ✅ | ✅ |
| `.mcp.json` | ✅ | ✅ | ✅ |
| `commands/*.md` | ✅ | ➖ 忽略 / ignored | ✅ |
| `agents/*.md` | ✅ | ➖ 忽略 / ignored | ✅ |

## 安装 / Install

以下命令中的 `<github-user>/skills` 替换为本仓库实际的 GitHub 地址；也可直接用本地路径 `/path/to/skills` 测试。
Replace `<github-user>/skills` with the actual GitHub location of this repo, or use a local path `/path/to/skills` to try it out.

### Claude Code

```text
/plugin marketplace add <github-user>/skills
/plugin install hello-world@leo-skills
```

安装后输入 `/` 即可看到 `hello` 命令；`greeting` 技能会在合适时机自动触发。
The `hello` command appears under `/`, and the `greeting` skill triggers automatically when relevant.

### ZCode

设置 → 插件 → 右上角 **创建** → **添加插件市场**，填入本仓库的 GitHub 地址（`owner/repo` 或链接）、Git URL 或本地目录路径，然后在「个人」分段安装 `hello-world`。

Open Settings → Plugins → **Create** → **Add plugin marketplace**, paste this repo's GitHub address (`owner/repo`), a Git URL, or a local directory path, then install `hello-world` from the **Personal** section. ZCode natively loads Claude Code plugin marketplaces, so no extra adaptation is needed.

### Codex

```text
codex plugin marketplace add <github-user>/skills
codex plugin install hello-world
```

命令以 `codex plugin --help` 的实际输出为准（Codex 的插件 CLI 仍在快速演进）。
Check `codex plugin --help` for the exact subcommands in your Codex version.

## 新增插件 / Adding a new plugin

1. 复制 `plugins/hello-world/` 为 `plugins/<你的插件名>/`（名称须匹配 `^[a-z0-9][a-z0-9._-]{0,127}$`）。
   Copy `plugins/hello-world/` to `plugins/<your-plugin-name>/` (name must match `^[a-z0-9][a-z0-9._-]{0,127}$`).
2. 修改插件内的三份清单：`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json` 与 `.codex-plugin/plugin.json`（保持 `name`、`version`、`description` 一致）。
   Update all three manifests inside the plugin, keeping `name`, `version` and `description` in sync.
3. 在三份市场清单中各加一个条目：`.claude-plugin/marketplace.json`、根目录 `marketplace.json`（两者内容保持一致）、`.agents/plugins/marketplace.json`（注意 Codex 的 `source` 是对象写法 `{"source": "local", "path": "./plugins/<name>"}`）。
   Add an entry to each of the three marketplace indexes; the two Claude/ZCode copies stay identical, and Codex uses the object form of `source`.
4. 运行 `bash scripts/validate.sh` 校验结构。
   Run `bash scripts/validate.sh` to validate.

发版提醒：ZCode 以市场清单条目里的 `version` 判断是否有更新，插件代码更新后务必同步修改六处 `version`（三份插件清单 + 三份市场条目），否则不会提示可更新。
When releasing: ZCode compares the marketplace entry's `version` against the installed `plugin.json`, so bump `version` in all three plugin manifests and all three marketplace entries, or updates won't be detected.

## License

[MIT](LICENSE)
