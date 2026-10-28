# leo-skills

[English](README_EN.md) | 中文

一个面向 **Claude Code**、**OpenAI Codex** 和 **ZCode**（智谱）的插件市场，共享 skill 源码并保留三宿主分发清单。实际安装与调用范围见[兼容性证据](docs/compatibility.md)。

## 插件列表

| 插件 | 用途 |
| --- | --- |
| [hello-world](plugins/hello-world/skills/greeting/SKILL.md) | 最小示例插件，演示 Skill 与命令入口。 |
| [invest](plugins/invest/) | A 股投资研究，覆盖市场、公司、行业、财报等 9 个方向。 |
| [image](plugins/image/skills/photo-restoration/SKILL.md) | 高保真照片修复，优先保留人物与原始场景。 |
| [dotnet](plugins/dotnet/skills/dotnet-scaffold/SKILL.md) | 新建 .NET 类库、桌面应用、Web 和服务代码库，默认简单，按需支持 Clean Architecture、DDD、MVVM 和微服务。 |
| [engineering](docs/engineering.md) | 存量项目维护：代码库体检、缺陷修复、回归测试、保持行为的重构和变更评审。 |

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
│   ├── invest/                     # A股投资研究：9 个技能 + 9 个快捷命令
│   │   ├── .zcode-plugin/plugin.json    # 三份清单内容一致
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .codex-plugin/plugin.json
│   │   ├── references/                  # 跨技能共享：数据源清单、分析规范
│   │   ├── skills/                      # 市场调研 / 公司研究 / 板块分析 / 行业分析 / 宏观分析 /
│   │   │                                # 技术分析 / 财报解读 / 投资决策 / 国际局势（中文技能名）
│   │   └── commands/                    # /invest:market 等快捷命令（Codex 忽略）
│   ├── image/                      # 图像处理：照片修复（1 个技能 + 1 个快捷命令）
│   │   ├── .zcode-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .codex-plugin/plugin.json
│   │   ├── skills/photo-restoration/SKILL.md
│   │   └── commands/restore.md
│   ├── engineering/                # 5 个维护 skill + 同名转交命令，共享参考资料
│   └── dotnet/                     # .NET 新代码库脚手架（1 个技能 + 1 个快捷命令）
│       ├── .zcode-plugin/plugin.json
│       ├── .claude-plugin/plugin.json
│       ├── .codex-plugin/plugin.json    # Codex 增加 interface 元数据
│       ├── skills/dotnet-scaffold/     # 入口、按需参考资料、配置与性能模板
│       └── commands/dotnet-new.md      # Codex 通过 Skill 调用
├── scripts/validate.py             # 跨平台通用校验，validate.sh 为 Bash 入口
├── scripts/sync-version.py         # 六处版本同步，支持 --check / --diff
├── scripts/update.sh               # 刷新与宿主发现检查
├── evals/                          # 用例与夹具源码；runs/results 为忽略的本地产物
├── tests/                          # 校验器及工具回归测试
└── .github/workflows/validate.yml   # 静态与按范围执行的确定性检查
```

设计要点：

- 插件源码（`skills/`、`commands/`、`hooks/hooks.json`、`.mcp.json`）三端格式通用，只写一份。
- 每个插件维护三份公共元数据一致的清单：`.zcode-plugin/plugin.json`（ZCode 推荐位置）、`.claude-plugin/plugin.json`（Claude Code）、`.codex-plugin/plugin.json`（Codex）。字段分别满足宿主要求，例如 dotnet 的 Codex 清单含 interface 元数据。ZCode 也兼容 `.claude-plugin/` 回退。
- Codex 使用自己的清单（`.codex-plugin/plugin.json`）与市场索引（`.agents/plugins/marketplace.json`）。

## 分发格式约定

下表是已有分发结构的预期支持，不等同于本版本已经实测；宿主版本、验证日期与未验证项见[兼容性记录](docs/compatibility.md)。

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
/plugin install image@leo-skills
/plugin install dotnet@leo-skills
/plugin install engineering@leo-skills
```

安装后输入 `/` 即可看到 `hello` 命令；`greeting` 技能会在合适时机自动触发。投资插件 `invest` 安装后可用 `/invest:market`、`/invest:stock 贵州茅台` 等快捷命令，9 个投资技能（市场调研、公司研究、板块分析、行业分析、宏观分析、技术分析、财报解读、投资决策、国际局势）会在相关对话中自动触发。图像插件 `image` 安装后可用 `/image:restore <图片路径>` 修复照片，`photo-restoration` 技能（高保真照片修复：去污去划痕、两阶段修复、优先保持原貌）在对话中请求照片修复时自动触发。

### ZCode

设置 → 插件 → 右上角 **创建** → **添加插件市场**，填入本仓库的 GitHub 地址（`owner/repo` 或链接）、Git URL 或本地目录路径，然后在「个人」分段安装 `hello-world`（`invest`、`image`、`dotnet`、`engineering` 同理）。ZCode 原生支持加载 Claude Code 插件市场格式，无需额外适配。

### Codex

```text
codex plugin marketplace add <github-user>/skills
codex plugin install hello-world
codex plugin install invest
codex plugin install image
codex plugin install dotnet
codex plugin install engineering
```

命令以 `codex plugin --help` 的实际输出为准（Codex 的插件 CLI 仍在快速演进）。Codex 忽略 `commands/`（斜杠命令不可用），`invest` 的 9 个技能与 `image` 的照片修复技能仍可正常触发。

## 新增插件

1. 复制 `plugins/hello-world/` 为 `plugins/<你的插件名>/`（名称不超过 64 字符，匹配 `^[a-z0-9]+(?:[._-][a-z0-9]+)*$`）。
2. 修改插件内的三份清单：`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json` 与 `.codex-plugin/plugin.json`（保持 `name`、`version`、`description` 一致）。
3. 在三份市场清单中各加一个条目：`.claude-plugin/marketplace.json`、根目录 `marketplace.json`（两者内容保持一致）、`.agents/plugins/marketplace.json`（注意 Codex 的 `source` 是对象写法 `{"source": "local", "path": "./plugins/<name>"}`）。
4. 安装 `requirements-dev.txt`，运行 `python scripts/validate.py`（或 `bash scripts/validate.sh`）校验；补充对应的工具测试和 Agent 用例。

版本同步支持预览、只检查和实际更新，先校验完整候选再写入六处版本；IO 失败会尝试回滚已写文件：

```text
python scripts/sync-version.py engineering 0.1.1 --diff
python scripts/sync-version.py engineering 0.1.0 --check
python scripts/sync-version.py engineering 0.1.1
```

## 本地调测

本地源码改动是否实时生效取决于宿主安装方式。需要刷新已安装的 Claude 插件时：

```text
bash scripts/update.sh engineering
python scripts/update.py engineering --output /tmp/engineering-refresh
```

脚本校验仓库、确认市场来源、刷新指定缓存、核对安装文件，再查看新会话的宿主发现元数据。命令失败保留退出码；模型回显标记不作为证据。退出 0 表示安装文件与发现检查通过，2 表示证据不足，1 表示失败；任务行为始终另行评测。该脚本会改变本地安装，不用于纯源码校验。

```text
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/test-engineering.py
```

维护工具的范围见[工作流说明](docs/engineering.md)，三层检查、28 个 Agent 案例与人工复验方式见[评测协议](docs/evaluation.md)。.NET 夹具固定 SDK 10.0.403，在临时目录执行；无需为使用 skill 强制升级目标项目。CI 已配置 Linux/Windows 检查，托管执行结果需以实际 workflow 为准。

dotnet 的专项验证命令：

```text
python scripts/validate-dotnet.py
python scripts/test-dotnet-scaffold.py
node --experimental-vm-modules scripts/test-dotnet-performance.mjs
```

静态检查需要 PyYAML；生成测试需要 .NET SDK，在临时目录中运行，添加 `--online` 可覆盖需 NuGet 的案例。性能脚本检查使用模拟传输；生成规则检查与新会话触发、实际压测分别验证。

## License

[MIT](LICENSE)
