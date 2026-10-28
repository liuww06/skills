# 宿主兼容性证据 / Host evidence

核对日期：**2026-10-28**。源码格式、CLI 存在、宿主发现、资源读取与任务完成分别记录。

| 宿主与实际版本 | 安装 | 单会话发现 | 显式调用 / 资源定位 | 自然触发 | 任务证据 |
| --- | --- | --- | --- | --- | --- |
| Claude Code 2.1.309，配置模型 `glm-5.3[1m]` | 未验证；未改变个人安装 | 通过：`--plugin-dir` 的 init 列出 5 个 skill | 已观察命令转交与 SKILL.md、共享参考资料读取 | 未通过本次自然评审样例：选择了内置 code-review，随后超时 | 修复、补测、重构、正确变更评审及异常工具案例有独立证据；体检复测仍未完全通过风险证据校准，见记录 |
| Codex CLI 0.164.0 | 未验证 | 未验证 | 未验证 | 未验证 | 本轮只确认 CLI 版本与包静态结构 |
| ZCode，版本未知 | 未验证 | 未验证 | 未验证 | 未验证 | 当前环境无可用 ZCode CLI；按统一人工协议复验 |

Claude 的型号是宿主报告的配置标识，不代表提供方不可变模型修订号。认证沿用用户现有配置；第一次隔离所有用户设置时无法认证，后续保留认证配置并禁用 hooks/MCP。初期工具可见性问题由显式配置所需工具解决。这些运行条件保留在记录中，不能推广到所有安装组合。

本页保留本次核对的结论摘要。候选差异、资源读取、真实命令结果、TRX 与独立评判保留在本机的 `evals/results/2026-10-28/`，已被 Git 忽略，不随仓库分发；需要共享时通过制品存储保留。[统一协议](evaluation.md)说明如何复验安装、发现、显式调用、自然触发及资源定位。CLI 的静态 `plugin validate` 对 engineering 清单通过；这不证明模型任务已通过。

Linux 本地静态与确定性检查已执行。GitHub Actions 配置了 Linux/Windows 检查；截至本页证据核对时，**托管 CI 和 Windows 实际运行未验证**。没有把全部 28 个 Agent 用例或三宿主组合标成通过，也没有进行 enabled/disabled 效果对比。

The package retains three host manifests. Verified Claude session loading does not establish installation or reliable natural routing. Codex/ZCode behavior, hosted CI, the full agent suite and paired effectiveness measurements remain unverified.
