# 存量项目维护工具集 / Maintenance workflows

首版交付范围为 P0（校验、版本同步、CI、评测）和 P1（以下五个 skill）。P2 的架构检查、CI 修复、SDK 升级、EF 迁移，以及 P3 的兼容性、诊断与发布检查尚未实现。工程插件和 dotnet 脚手架可独立安装；现有投资技能保持原名。

| Skill | 使用场景 / Request | 交付与范围 / Outcome |
| --- | --- | --- |
| [repo-assess](../plugins/engineering/skills/repo-assess/SKILL.md) | 接手项目，理解维护风险 / Assess this repository | 入口、调用链、依赖、命令和有证据的风险排序；默认只读 |
| [bugfix](../plugins/engineering/skills/bugfix/SKILL.md) | 定位并修复异常 / Fix this defect | 复现、根因证据、最小修复、回归验证；分析请求只读 |
| [regression-tests](../plugins/engineering/skills/regression-tests/SKILL.md) | 给遗留逻辑补可靠测试 / Add regression coverage | 沿用框架，保护业务结果，以代表性变异验证断言有效性 |
| [safe-refactor](../plugins/engineering/skills/safe-refactor/SKILL.md) | 拆分模块并保持行为 / Refactor without behavior changes | 相关公共契约、行为基线、渐进修改、前后对照 |
| [change-review](../plugins/engineering/skills/change-review/SKILL.md) | 评审提交或工作区 / Review this diff | 固定范围，追踪调用方，输出有触发条件与位置的缺陷；默认只读 |

Claude Code / ZCode 的命令入口与 skill 同名，例如 `/engineering:bugfix`。命令只转交 skill；Codex 使用 `$bugfix` 等 skill 入口。每个宿主的发现与调用应按[兼容性证据](compatibility.md)确认，不由包结构检查推断。

所有流程读取目标仓库的项目指令、贡献指南、构建、测试和 CI。明确规定与推断出的惯例分开；不附带创建新的工程策略配置语言或规范体系。用户要求修复时完成授权范围内的代码与验证；已有授权无需重复确认。未提交修改必须保留。

结果默认在会话中给出：改了什么、解决什么、命令与目录、实际结果、剩余风险。通过、失败、环境阻塞、未验证是不同状态。空测试、工具失败和未运行命令不能写成通过。

完整确定性夹具覆盖 .NET 后端与类库：固定 .NET SDK、xUnit、WebApplicationFactory、SQLite 实际持久化与迁移、Generic Host Worker、多项目条件引用和 CPM。SQLite 是该夹具的真实数据库；结果不代表 SQL Server 或 PostgreSQL 语义。其他语言可使用通用工作流，但尚未获得同等自动验证；WPF、MAUI 不在本版维护夹具范围。

The initial release contains P0 infrastructure and the five P1 workflows above. Skills follow the target repository's conventions and versions. Fix requests include implementation and verification; analysis/review stays read-only. Reports distinguish passed, failed, blocked and unverified evidence. Deterministic fixture coverage is .NET backend/library maintenance; agent behavior and host installation require separate evidence. P2/P3 remain future work.
