---
description: 财报与公告解读（earnings report shortcut）
argument-hint: "[公司名称或代码] [期间，如 2025Q3]"
allowed-tools: WebSearch, WebFetch
---

对 $ARGUMENTS 进行财报与公告解读。

执行步骤：
1. 读取 ../skills/财报解读/SKILL.md，严格按其分析框架与输出模板执行；数据源优先使用 ../references/data-sources.md 中的清单与检索式。
2. 若 $ARGUMENTS 为空：简要说明本命令用于财报与公告解读，并询问用户想查看的公司名称或代码及报告期间（如 2025Q3），不发起联网检索。
3. 报告文末必须逐字包含 analysis-conventions.md 中的免责声明原文：
> 免责声明：本报告由 AI 基于公开网络信息生成，仅供参考，不构成任何投资建议（非投资建议）。数据可能滞后或有误，请以官方披露为准。投资有风险，入市需谨慎。
