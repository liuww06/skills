---
description: 遗留逻辑回归测试
argument-hint: "[目标路径、症状或变更范围]"
---

读取并执行本插件的 [regression-tests](../skills/regression-tests/SKILL.md)，处理用户需求：$ARGUMENTS。

路径相对于本命令文件；Claude Code 可使用 `${CLAUDE_PLUGIN_ROOT}/skills/regression-tests/SKILL.md`。其他宿主使用其已安装插件资源位置，不相对用户工作目录解析。资源无法定位时报告加载阻塞；流程和授权边界以该 skill 为准。
