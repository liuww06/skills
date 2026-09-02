---
description: A股大盘市场调研（market overview shortcut）
argument-hint: "[关注点，如：今日行情 / 本周复盘 / 情绪与资金面]"
allowed-tools: WebSearch, WebFetch
---

对 $ARGUMENTS 进行 A股市场调研。

执行步骤：
1. 读取 ../skills/市场调研/SKILL.md，严格按其分析框架与输出模板执行；数据源优先使用 ../references/data-sources.md 中的清单与检索式。
2. 若 $ARGUMENTS 为空：按该技能的默认框架输出最新一期全维度市场报告（大盘走势、情绪、资金面、热点）。
3. 报告文末必须逐字包含 analysis-conventions.md 中的免责声明原文：
> 免责声明：本报告由 AI 基于公开网络信息生成，仅供参考，不构成任何投资建议（非投资建议）。数据可能滞后或有误，请以官方披露为准。投资有风险，入市需谨慎。
