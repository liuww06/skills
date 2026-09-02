---
description: 投资决策支持（investment decision shortcut）
argument-hint: "[标的] [已知观点或持仓信息]"
allowed-tools: WebSearch, WebFetch
---

对 $ARGUMENTS 提供投资决策支持。

执行步骤：
1. 读取 ../skills/投资决策/SKILL.md，严格按其分析框架与输出模板执行；数据源优先使用 ../references/data-sources.md 中的清单与检索式。
2. 若 $ARGUMENTS 为空：简要说明本命令用于投资决策支持，并询问用户关注的标的及已知观点或持仓信息，不发起联网检索。
3. 报告文末必须逐字包含 analysis-conventions.md 中的免责声明原文：
> 免责声明：本报告由 AI 基于公开网络信息生成，仅供参考，不构成任何投资建议（非投资建议）。数据可能滞后或有误，请以官方披露为准。投资有风险，入市需谨慎。
