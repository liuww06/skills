---
description: 从自然语言需求新建 .NET 类库、应用或服务代码库
argument-hint: "[项目类型、名称、目录及可选架构/能力]"
---

使用本插件的 dotnet-scaffold Skill 处理用户需求：$ARGUMENTS。

读取本插件根目录下 `skills/dotnet-scaffold/SKILL.md` 并按其路由执行。Claude Code 中可通过 `${CLAUDE_PLUGIN_ROOT}/skills/dotnet-scaffold/SKILL.md` 定位；其他宿主使用其提供的已安装插件资源路径，不相对用户当前工作目录解析。如果无法定位资源，说明加载问题，不自行重建另一套流程。

参数缺失时结合用户意图和上下文，只询问创建所必需的信息。保持 Skill 的新建范围与默认简单结构，不在此重复脚手架流程。
