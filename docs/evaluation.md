# 验证与评测协议 / Validation and evaluation

## 版本控制与产物存放

提交 `evals/cases.json` 和 `evals/fixtures/` 中的源码、项目配置、迁移与测试。它们是可复用的评测输入。

运行产物存放在系统临时目录，或仓库中已忽略的 `evals/runs/`、`evals/results/`。这些目录下的工作副本、模型对话、日志、TRX、候选差异、文件快照、评判与结果 JSON 均不提交。夹具中的 `bin/`、`obj/`、`TestResults/` 和临时 SQLite 文件也由现有规则忽略。

需要长期保留的简短结论写入 `docs/`，完整运行证据通过 CI artifacts 或团队制品存储保留；版本化文档不链接到仅在本机存在的输出文件。不要通过忽略整个 `evals/` 或所有 JSON 文件来隐藏评测源码。

## 三层证据

| 层级 | 命令 | 能证明什么 |
| --- | --- | --- |
| 静态 | `python scripts/validate.py` / `bash scripts/validate.sh` | 三份插件公共元数据、三市场版本/条目、严格 JSON/YAML、skill/命令入口、本地资源边界 |
| 专项静态 | `python scripts/validate-dotnet.py` | 在通用契约基础上，验证 dotnet 资产与资源可达性 |
| 工具回归 | `python -m unittest discover -s tests -v` | 对错误清单、元数据、版本同步、刷新误报、评测记录等实际失败样例的拦截 |
| 确定性执行 | `python scripts/test-engineering.py` | 真实 .NET 构建/测试、业务变异失败与恢复、契约重构；不是模型行为 |
| Agent 评测 | `python scripts/evaluate.py run ...` 或人工协议 | 真实宿主的选择、加载、代码与回答；需要独立判定任务结果 |

安装 Python 3.10+ 与 `python -m pip install -r requirements-dev.txt`。Node 22+ 用于原有 k6 模板模拟测试。维护夹具使用 `evals/fixtures/dotnet/global.json` 固定完整 SDK **10.0.403**、关闭 roll-forward；依赖版本由 CPM 固定。可用 `--dotnet` 指定 SDK 命令、`--nuget-packages` 指定隔离缓存。首次还原需要 NuGet 网络；不更改用户包源。

```text
python scripts/test-engineering.py --output /tmp/engineering-check
python scripts/test-dotnet-scaffold.py --online
node --experimental-vm-modules scripts/test-dotnet-performance.mjs
```

`test-engineering.py` 在新副本里运行 14 个基线断言案例，依次注入折扣边界、舍入、HTTP 校验、Worker 去重/取消、序列化契约六类错误，要求指定业务测试失败；恢复后必须通过。提取折扣方法时重新运行全部契约测试。编译失败不算成功杀死变异；缺失 TRX、零发现数或跳过的测试不能当作通过。每次命令与退出码保存在日志中，TRX 和 results.json 留在输出目录。

SDK 缺失返回 2（blocked）；测试/夹具错误返回 1；执行全部通过返回 0。无法分类的工具故障保留原始日志，不推测为通过。旧 scaffold 的条件 CPM 案例在 SDK 不含 NETStandard 目标包时需要 `--online`；本地合成包源作为额外来源保留。

## Agent 用例与执行

[用例清单](../evals/cases.json)包括每个 skill 的正向、相邻请求、信息不足、环境受限场景，以及正确变更评审、用户未提交修改、只读分析、Worker/HTTP 修复、零测试、工具失败、数据库不可用。用例的 rubric 是行为和产物判据，不比较整段回答措辞。

```text
python scripts/evaluate.py prepare --case bugfix-user-edits --output /tmp/bugfix-manual
python scripts/evaluate.py run --case change-review-clean --output /tmp/review-enabled
python scripts/evaluate.py run --case change-review-clean --invocation explicit --output /tmp/review-explicit
python scripts/evaluate.py run --case change-review-clean --condition disabled --output /tmp/review-disabled
python scripts/evaluate.py verify /tmp/bugfix-run --dotnet /path/to/dotnet
python scripts/evaluate.py validate-record /tmp/review-enabled/record.json
```

`prepare` 复制夹具并建立本地 Git 基线、注入指定问题，再保存输入文件哈希；不会修改源码夹具。缺 SDK、数据库和工具失败通过独立 PATH shim 模拟，run.json 明示模拟条件。不要把这些案例宣传为真实断网/真实生产数据库故障测试。Windows 可用 prepare + 手工工具限制复验；自动 shim 目前使用 POSIX shell。

`run` 当前适配 Claude CLI，用 `--plugin-dir` 进行单会话加载，不安装插件。默认 natural，`--invocation explicit` 添加指定 skill 的命令入口；disabled 对照只使用自然请求。可用 `--dotnet` 和 `--nuget-packages` 指定隔离验证环境。沿用用户认证和模型配置，不读取或拷贝凭据；禁用 hooks、项目设置和 MCP，显式启用所需文件与执行工具。宿主自带或用户启用的其他技能仍可能存在：记录 init 清单，若另一份 engineering skill 污染 disabled 对照，作废该对照。自动调用会消耗已配置模型的用量；外层超时默认 300 秒，可用 --timeout 调整。新宿主先确认其本机 `--help`，不要绕过授权或沙箱。

CLI 退出 0 仅记录 **unverified**，表示有待独立评判；非零、超时与 API 故障记录阻塞并保留日志。只读用例产生源文件差异会自动判为失败。其余需要评审者检查：

1. 查看 host.jsonl 的宿主 init 和实际 Skill/Read 工具事件。init 列出 skill 只证明发现；模型说“已加载”不能证明加载。显式调用和自然触发分别记录。
2. 对照 prompt、rubric、输入哈希、工作区差异和用户注释。修复必须改变错误路径；评审必须有准确触发条件与位置，正确 diff 不应出现编造问题。
3. `verify` 子命令在另一临时副本独立执行修复/补测/重构候选的测试；修复和补测还复验代表性变异，并保存真实进程退出码与 TRX。它不会自动将 Agent 记录提升为 passed，任务范围、契约和触发仍需评审。也可在候选工作区使用既有命令验证。修复类在隔离副本恢复旧错误，要求新回归测试失败，再恢复修复通过；补测试类将代表性变异应用到候选代码，要求其新增断言失败；重构比较 API、异常、序列化和业务断言。不能用仓库里现成测试全部通过代替检查模型是否完成了所请求改动。
4. 在输出目录写 `grade.md`，记录判断、命令、目录、退出码/测试数量和证据路径。检查调用失败、零测试、未执行命令是否被虚报，确认用户修改和只读边界。
5. 更新 record.json 的 status/reason/evidence，并添加 `checks: [{"status":"passed", "evidence":"grade.md"}]` 等独立检查；有任何失败不能整体 passed。使用 validate-record 验证必需字段与证据文件。此校验检查记录完整性，不替代语义评审。

记录最少包含案例 ID、层级、宿主与版本、模型标识、skill 版本、时间、enabled/disabled 条件、状态、证据、失败或阻塞原因。未知模型版本不能把行为标成 passed。record.json 另保留实际退出码、耗时与可用的 token/费用数据；run.json 的资源哈希固定本次 skill 内容。

## 三宿主人工复验

对 Claude Code、Codex、ZCode 使用同一夹具、原始提示词和判据，分别记录：安装、发现、显式调用、自然触发、资源定位。调用另一宿主可使用 prepare 生成的 workspace 与 prompt.txt；按该宿主当前支持的方式安装/发现插件，再开启新会话。检查共享 references 仍从安装包内定位，独立安装 engineering 时不依赖 dotnet 插件。将宿主版本、模型版本、操作步骤、日志或录屏的相对证据路径写入记录。没有接口或未执行的步骤明确标 unverified。

发布前对修改过的 skill 执行对应四类路由案例和相关核心用例；正式兼容性声明要求各宿主逐项证据。托管 CI 只运行静态和确定性层，不把 PR 检查通过冒充三宿主任务通过。CI 不保存模型凭据，也不运行付费模型评测。

试用比较使用同一案例的 enabled/disabled 配对，记录任务完成率、人工返工次数、误触发数、耗时、token/费用与额外依赖。没有足够重复样本不声称质量提升；失败案例先回归复现，规则只有带来可观察改进才保留。

## 依据

- [Agent Skills 规范](https://agentskills.io/specification)：逐步加载与元数据；保留本仓库已有 Unicode skill 名称，不批量重命名。
- [ASP.NET Core 集成测试](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests)：通过测试宿主验证请求管线。
- [EF Core 测试策略](https://learn.microsoft.com/en-us/ef/core/testing/choosing-a-testing-strategy)：替代数据库的结果不能代表生产数据库语义。
- [.NET 10 下载与版本](https://dotnet.microsoft.com/en-us/download/dotnet/10.0)：本次核对日期 2026-10-28；固定版本属于夹具，不强制升级用户项目。

Version case definitions and fixture sources. Keep generated runs/results in ignored local directories or CI artifacts, and retain concise conclusions in docs. The automated layers validate packaging and executable fixtures. Agent runs intentionally remain unverified until an independent reviewer checks routing, artifacts, regressions and scope. Use the same cases on each host, record exact versions and evidence, and compare enabled/disabled runs before making effectiveness claims.
