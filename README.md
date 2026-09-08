# leo-skills

[English](README_EN.md) | 中文

一个仓库，三端通用的插件市场：同一份插件源码可被 **Claude Code**、**OpenAI Codex** 和 **ZCode**（智谱）直接安装使用。

## 目录结构

```text
skills/
├── marketplace.json                # ZCode 市场清单（仓库根目录）
├── .claude-plugin/
│   └── marketplace.json            # Claude Code 市场清单
├── .agents/plugins/
│   └── marketplace.json            # Codex 市场清单
├── AWESOME.md                      # 开源 Agent Skills 与上下文规范精选
├── plugins/
│   ├── hello-world/                # 示例插件，也是新插件的模板
│   │   ├── .zcode-plugin/plugin.json    # ZCode 清单（ZCode 优先读取）
│   │   ├── .claude-plugin/plugin.json   # Claude Code 清单
│   │   ├── .codex-plugin/plugin.json    # Codex 清单
│   │   ├── skills/greeting/SKILL.md     # 技能（三端通用）
│   │   └── commands/hello.md            # 斜杠命令
│   └── invest/                     # A股投资研究：9 个技能 + 9 个快捷命令
│       ├── .zcode-plugin/plugin.json    # 三份清单内容一致
│       ├── .claude-plugin/plugin.json
│       ├── .codex-plugin/plugin.json
│       ├── references/                  # 跨技能共享：数据源清单、分析规范
│       ├── skills/                      # 市场调研 / 公司研究 / 板块分析 / 行业分析 / 宏观分析 /
│       │                                # 技术分析 / 财报解读 / 投资决策 / 国际局势（中文技能名）
│       └── commands/                    # /invest:market 等快捷命令（Codex 忽略）
├── scripts/validate.sh             # 结构校验
└── scripts/update.sh               # 一键刷新缓存 + 新会话验证
```

设计要点：

- 插件源码（`skills/`、`commands/`、`hooks/hooks.json`、`.mcp.json`）三端格式通用，只写一份。
- 每个插件维护三份内容一致的清单：`.zcode-plugin/plugin.json`（ZCode 推荐位置，查找优先级最高）、`.claude-plugin/plugin.json`（Claude Code）、`.codex-plugin/plugin.json`（Codex）。ZCode 也兼容 `.claude-plugin/` 回退，但本仓库采用其推荐方式；若某插件需要 ZCode 专属配置（如 `userConfig`），改 `.zcode-plugin/` 那份即可。
- Codex 使用自己的清单（`.codex-plugin/plugin.json`）与市场索引（`.agents/plugins/marketplace.json`）。

## 组件兼容矩阵

| 组件 | Claude Code | Codex | ZCode |
| --- | :---: | :---: | :---: |
| `skills/*/SKILL.md` | ✅ | ✅ | ✅ |
| `hooks/hooks.json` | ✅ | ✅ | ✅ |
| `.mcp.json` | ✅ | ✅ | ✅ |
| `commands/*.md` | ✅ | ➖ 忽略 | ✅ |
| `agents/*.md` | ✅ | ➖ 忽略 | ✅ |

## 资源精选

[AWESOME.md](AWESOME.md) 收录官方与社区高质量的开源 Agent Skills（按软件工程、测试、DevOps、数据、安全、科研等领域分类），以及 **Agent 上下文规范**资源——写进 AGENTS.md / CLAUDE.md 的工程规范、安全护栏与提示词架构。条目均经核实并附中文点评，可作为选型与学习的索引。

## 安装

以下命令中的 `<github-user>/skills` 替换为本仓库实际的 GitHub 地址；也可直接用本地路径 `/path/to/skills` 测试。

### Claude Code

```text
/plugin marketplace add <github-user>/skills
/plugin install hello-world@leo-skills
/plugin install invest@leo-skills
```

安装后输入 `/` 即可看到 `hello` 命令；`greeting` 技能会在合适时机自动触发。投资插件 `invest` 安装后可用 `/invest:market`、`/invest:stock 贵州茅台` 等快捷命令，9 个投资技能（市场调研、公司研究、板块分析、行业分析、宏观分析、技术分析、财报解读、投资决策、国际局势）会在相关对话中自动触发。

### ZCode

设置 → 插件 → 右上角 **创建** → **添加插件市场**，填入本仓库的 GitHub 地址（`owner/repo` 或链接）、Git URL 或本地目录路径，然后在「个人」分段安装 `hello-world`（`invest` 同理）。ZCode 原生支持加载 Claude Code 插件市场格式，无需额外适配。

### Codex

```text
codex plugin marketplace add <github-user>/skills
codex plugin install hello-world
codex plugin install invest
```

命令以 `codex plugin --help` 的实际输出为准（Codex 的插件 CLI 仍在快速演进）。Codex 忽略 `commands/`（斜杠命令不可用），`invest` 的 9 个技能仍可正常触发。

## 新增插件

1. 复制 `plugins/hello-world/` 为 `plugins/<你的插件名>/`（名称须匹配 `^[a-z0-9][a-z0-9._-]{0,127}$`）。
2. 修改插件内的三份清单：`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json` 与 `.codex-plugin/plugin.json`（保持 `name`、`version`、`description` 一致）。
3. 在三份市场清单中各加一个条目：`.claude-plugin/marketplace.json`、根目录 `marketplace.json`（两者内容保持一致）、`.agents/plugins/marketplace.json`（注意 Codex 的 `source` 是对象写法 `{"source": "local", "path": "./plugins/<name>"}`）。
4. 运行 `bash scripts/validate.sh` 校验结构。

发版提醒：ZCode 以市场清单条目里的 `version` 判断是否有更新，插件代码更新后务必同步修改六处 `version`（三份插件清单 + 三份市场条目），否则不会提示可更新。

## 本地调测

安装是**拷贝**插件到 `~/.claude/plugins/cache/`，仓库里改代码不会自动生效；已安装时重复 `install` 是空操作，`update` 只比对版本号。写完插件或 skill 后一键刷新并在新会话中验证：

```bash
bash scripts/update.sh               # 校验结构 → 强刷缓存 → 新会话逐个验证 skill/命令
bash scripts/update.sh hello-world   # 只处理指定插件
```

脚本会：① 跑 `scripts/validate.sh`；② 确认本仓库已注册为本地市场；③ `uninstall + install` 强制刷新缓存；④ 在干净的 `claude -p` 新会话里斜杠调用每个 skill 和命令，要求回复中带出验证标记，全部通过才退出 0。

快速迭代（免刷新）的替代做法：把插件符号链接进个人技能目录，改完开新会话即生效，适合频繁改动；调试完删除链接即可：

```bash
ln -sfn /path/to/skills/plugins/<插件> ~/.claude/skills/<插件>
```

## License

[MIT](LICENSE)
