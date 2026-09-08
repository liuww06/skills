# 开源精选:Agent Skills 与 Agent 上下文规范

> 面向 Claude Code / Codex / ZCode 等编程 Agent,收录官方与社区高质量的开源技能(skill),以及 **Agent 上下文规范**资源——即写进 AGENTS.md / CLAUDE.md 等规则文件的工程规范、护栏与指令架构。
>
> 收录标准:官方出品或社区口碑明确、维护活跃、可直接取用,每条附中文点评。
> 最后核对:2026-09(star 数与规模为核对时快照,以仓库实况为准)。

## 一、官方资源与开放标准

- [anthropics/skills](https://github.com/anthropics/skills) — Anthropic 官方技能仓库(约 175k star)。除文档技能四件套 docx / pptx / xlsx / pdf 为 source-available 外均为 Apache 2.0;另含 skill-creator、mcp-builder、webapp-testing、frontend-design 等示例,及官方技能模板 `template/`。Claude Code 安装:`/plugin marketplace add anthropics/skills`。
- [Agent Skills 开放标准](https://agentskills.io/) — SKILL.md 格式规范站(标准仓库 [agentskills/agentskills](https://github.com/agentskills/agentskills))。核心是渐进披露三阶段:发现(只读元数据)→ 激活(按需载入全文)→ 执行(可选跑捆绑脚本);已被 Claude Code、Codex、Cursor、Gemini CLI、Copilot 等 26+ 客户端采纳。附[快速上手](https://agentskills.io/skill-creation/quickstart)与[完整规范](https://agentskills.io/specification)。
- [Agent Skills 官方文档](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — 概念、用法与[编写最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)。
- [Claude Code 技能文档](https://code.claude.com/docs/en/skills) — 技能在 Claude Code 中的启用与管理。

## 二、Skill 分类精选

### 2.0 综合合集与发现入口

英文:

- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) — 约 34k star、1400+ 技能,按出品方组织:Microsoft(133 个 Azure/SDK 技能)、OpenAI、Google、Cloudflare、Vercel、Netlify、Stripe、Supabase、Sentry、Hugging Face、HashiCorp 等,另收 Trail of Bits 安全套件与 LambdaTest 测试套件;MIT。强调人工精选、非 AI 批量生成;兼容 Claude Code / Codex / Gemini CLI / Cursor 等。
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) — 约 15k star 的早期精选清单:官方 + 社区技能、工具与教程,2026-02 仍在更新。
- [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills) — 约 10k star,按文档 / 开发 / 数据 / 科研 / 写作 / 安全等 13 类组织的目录式清单,框架技能(React、NestJS、Go、Unity 等)归在开发类之下。
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) — Composio 维护的精选列表,偏工具型与集成型技能。
- [kodustech/awesome-agent-skills](https://github.com/kodustech/awesome-agent-skills) — Kodus 团队按工程领域精选:前端 / 后端 / DevOps / 测试 / 安全 / 可观测性等,CC0 协议。亮点条目:multi-pr-review(三个子代理独立评审后共识聚合)、resolve-conflicts(结构化合并冲突解决)、karpathy-guidelines(压低 LLM 编码坏习惯)、unslop(去 AI 腔)。FAQ 厘清 skills / 提示词 / MCP 的分工。
- [skills-hub.ai](https://skills-hub.ai/) — 技能注册与发现站点:12,800+ 技能、259 个来源,与 Anthropic / Microsoft / Google 等官方仓库同步;`npx @skills-hub-ai/cli` 一键安装,全部免费。

中文:

- [yzfly/awesome-skills-zh](https://github.com/yzfly/awesome-skills-zh) — 中文精选 Claude Skills 合集,附 Skills 技术原理与适用场景解析。
- [libukai/awesome-agent-skills](https://github.com/libukai/awesome-agent-skills) — 《Agent Skills 终极指南》:快速入门、资源推荐、精选技能与实用工具。
- [joneqian/claude-skills-suite](https://github.com/joneqian/claude-skills-suite) — 中文技能套件:14 个自定义 Agent 与自动化 Command。
- [xstongxue/best-skills](https://github.com/xstongxue/best-skills) — 通用中文技能合集,可装入 Cursor / Claude Code / Codex 等的 skills 目录。
- [datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents) — 中文 Agent 开发教程,含 Skills 与 MCP 两种范式的对比与实战案例。

聚合入口:[GitHub topic: claude-code-skills](https://github.com/topics/claude-code-skills) · [GitHub topic: anthropic-skills](https://github.com/topics/anthropic-skills)

### 2.1 软件工程与方法论

- [obra/superpowers](https://github.com/obra/superpowers) — 约 283k star 的软件开发方法论框架(MIT)。以可组合技能 + 引导指令让 agent 自动遵循工作流:头脑风暴出规格 → git worktree 隔离 → 细粒度计划 → 子代理逐任务执行与双阶段评审;强制 TDD(先写测试否则删码)、系统化调试、完成前验证。Claude Code 官方插件市场可装,Codex / Cursor / Gemini CLI / Copilot CLI 等亦有对应安装方式。
- [mattpocock/skills](https://github.com/mattpocock/skills) — TypeScript 教育者 Matt Pocock 的日常工程技能集(约 256k star,MIT),定位"做真工程而非氛围编程":小而可组合、可改,涵盖需求拷问(grilling)、规格与工单拆解、TDD、系统化调试、领域建模与"深模块"架构、代码评审、合并冲突解决,并以 CONTEXT.md + ADR 沉淀共享领域语言。相较 superpowers 的体系化流程更轻量;`claude plugins install mattpocock-skills` 或 `npx skills@latest add mattpocock/skills` 安装(支持 Codex 等)。
- 多代理 PR 评审、合并冲突解决等单项工程技能,见 [kodustech 合集](https://github.com/kodustech/awesome-agent-skills)对应分类。

### 2.2 前端与全栈

- Anthropic 官方 frontend-design(前端审美与实现质量)——见[第一章](#一官方资源与开放标准)。
- React / NestJS / Unity 等框架技能与 65 技能全栈渐进披露包,收录于 [BehiSecc 合集](https://github.com/BehiSecc/awesome-claude-skills)。

### 2.3 后端与语言生态

- [microsoft/skills](https://github.com/microsoft/skills) — 微软官方:面向 Azure SDK 与 Microsoft AI Foundry 的 126 个技能与 AGENTS.md 模板,覆盖 .NET 在内的 6 种语言([文档站](https://microsoft.github.io/skills/))。
- [laravel/boost](https://github.com/laravel/boost) — Laravel 官方:让 agent 按 Laravel 最佳实践编码的 guidelines + 技能(PHP)。

### 2.4 测试与质量

- [LambdaTest/agent-skills](https://github.com/LambdaTest/agent-skills) — TestMu AI(原 LambdaTest)官方:70 个测试技能、15+ 语言,覆盖 Playwright / Cypress / Selenium / Appium / pytest,生成生产级用例;兼容 Claude Code / Cursor / Codex 等 40+ 助手。
- Anthropic 官方 webapp-testing(Playwright 驱动的 Web 应用测试)——见[第一章](#一官方资源与开放标准)。
- superpowers 的 test-driven-development(红-绿-重构强制)——见 [2.1](#21-软件工程与方法论)。

### 2.5 DevOps 与基础设施

- [microsoft/azure-skills](https://github.com/microsoft/azure-skills) — Azure 官方技能插件:以工作流、决策树与护栏教 agent"Azure 的活儿怎么干"。
- HashiCorp / Terraform、Sentry(迁移生成)等官方技能收录于 [VoltAgent 合集](https://github.com/VoltAgent/awesome-agent-skills);DevOps 分类精选另见 [kodustech 合集](https://github.com/kodustech/awesome-agent-skills)。

### 2.6 数据与数据库

- [aliyun/data-agent-skill](https://github.com/aliyun/data-agent-skill) — 阿里云官方数据分析技能:面向同一后端服务的两个独立 skill,按 agent 运行时(如 Claude Code)选用。
- [oceanbase/oceanbase-skills](https://github.com/oceanbase/oceanbase-skills) — OceanBase 官方技能集,以子目录组织多个独立技能,面向 Cursor / Claude Code 等编程助手。

### 2.7 AI 与 LLM 应用开发

- Anthropic 官方 mcp-builder(生成 MCP 服务器骨架)——见[第一章](#一官方资源与开放标准)。
- Hugging Face、OpenAI 等官方技能收录于 [VoltAgent 合集](https://github.com/VoltAgent/awesome-agent-skills);Microsoft AI Foundry 技能见 [microsoft/skills](https://github.com/microsoft/skills)。

### 2.8 安全

- [trailofbits/skills](https://github.com/trailofbits/skills) — 顶级安全审计公司 Trail of Bits 的安全技能市场:静态分析、威胁建模、智能合约审计、GitHub Actions 安全审查(agentic-actions-auditor)、差异代码评审等数十个技能,源自其真实审计工作流。
- [trailofbits/skills-curated](https://github.com/trailofbits/skills-curated) — 上述技能经人工审核的精选版,每项均通过质量与安全审查。

### 2.9 文档与办公

- Anthropic 官方文档技能四件套 docx / pptx / xlsx / pdf(Claude 文档能力同款,source-available)——见[第一章](#一官方资源与开放标准)。

### 2.10 科学与垂直领域

- [K-Dense-AI/scientific-agent-skills](https://github.com/k-dense-ai/scientific-agent-skills) — 原 claude-scientific-skills,约 27.6k star:163 个科研技能,覆盖生物、化学、医学、基因组学等领域的专用库与数据库操作。
- 金融投资方向可参考本仓库 [invest 插件](plugins/invest):A 股研究 9 技能(市场调研 / 公司研究 / 技术分析等)。

### 2.11 元技能(教 agent 写技能)

- Anthropic 官方 skill-creator 与 `template/` 脚手架——见[第一章](#一官方资源与开放标准)。
- superpowers 的 writing-skills(技能自我沉淀)——见 [2.1](#21-软件工程与方法论)。
- [agentskills.io 快速上手](https://agentskills.io/skill-creation/quickstart)与[格式规范](https://agentskills.io/specification)。

## 三、Agent 上下文规范(AGENTS.md / CLAUDE.md / Rules)

> 这类资源回答"往 AGENTS.md / CLAUDE.md 等规则文件里写什么":工程规范、安全护栏与指令架构,决定 agent 的默认行为与边界。

### 3.1 标准与模板

- [agents.md](https://agents.md/) — AGENTS.md 开放标准("给 agent 的 README"):6 万+ 开源项目采用,Linux 基金会 Agentic AI Foundation 维护。约定:放仓库根目录,monorepo 中各包可嵌套、就近文件优先,聊天指令可覆盖文件规则;Codex / Gemini CLI / Cursor / Copilot / Junie 等广泛支持。
- [microsoft/skills](https://github.com/microsoft/skills) — 附现成 AGENTS.md 模板,沉淀 Azure SDK / AI Foundry 的工程规范。
- [If You Build With AI, You Need This File](https://karozieminski.substack.com/p/if-you-build-with-ai-you-need-this) — AI 规则文件(CLAUDE.md 等)的写法:面向产品上下文、防止"agent 失控"的约束设计。

### 3.2 框架官方规范(可直接引入上下文)

- [laravel/boost](https://github.com/laravel/boost) — Laravel 官方编码规范 + 技能,直接约束 agent 产出符合框架惯例的代码。
- [microsoft/azure-skills](https://github.com/microsoft/azure-skills) — 以工作流 / 决策树 / 护栏形式提供 Azure 平台规范。
- karpathy-guidelines(收录于 [kodustech 合集](https://github.com/kodustech/awesome-agent-skills))— 语言无关的行为规范条目,抑制 LLM 常见编码坏习惯,可直接并入规则文件。

### 3.3 安全护栏与权限

- [guardrails.md](https://guardrails.md/) — 自治 agent 安全协议:以"Signs"(触发条件 / 确定性修复 / 理由 / 来源)沉淀失败教训,定义工件验证、上下文轮换、权限边界、速率限制四类通用护栏;放进项目根目录,agent 每轮迭代前读取。
- [Agentic Coding Hooks: Deterministic AI Guardrails](https://ranthebuilder.cloud/blog/agentic-coding-hooks-deterministic-ai-guardrails/) — 用 Claude Code hooks 做确定性护栏:概率性提示词管不住的事,交给钩子强制执行。
- [Equipping Claude Code with Deterministic Security Guardrails](https://blog.codacy.com/equipping-claude-code-with-deterministic-security-guardrails) — Codacy 实践:让每行代码都过确定性安全护栏的配置方法。
- [Practical Guardrails for Claude Code, Copilot, and Codex](https://dev.to/maxkrivich/ai-coding-agent-security-practical-guardrails-for-claude-code-copilot-and-codex-och) — 三大工具的权限收敽数字清单,配置可直接复制粘贴。

### 3.4 指令架构与提示词工程

- [The Complete Guide to Writing Agent System Prompts](https://medium.com/@fengliu_367/the-complete-guide-to-writing-agent-system-prompts-lessons-from-reverse-engineering-claude-code-09ecd87c7cc1) — 逆向 Claude Code 系统提示词:角色身份、安全边界、职责划分的四要素写法。
- [fainir/most-capable-agent-system-prompt](https://github.com/fainir/most-capable-agent-system-prompt) — 可整段粘贴的系统提示词:单代理优先架构、任务图、验证层、文件式持久记忆与自改进循环。
- [System Prompts, Tool Descriptions, and Instruction Hierarchies](https://zylos.ai/research/2026-03-30-prompt-engineering-ai-agent-systems-instruction-hierarchies/) — 生产级 agent 系统的指令层级研究。

## 四、选型建议

1. 优先级:官方出品(Anthropic / Microsoft / Laravel / Trail of Bits / 阿里云等)> 活跃维护的单领域精品 > 堆砌式转载合集。
2. 判断维度:最近提交时间;许可证(注意 anthropics/skills 的文档四件套是 source-available 而非开源);是否渐进披露(元数据轻量、按需加载);是否符合 SKILL.md 开放标准(决定能否跨 Claude Code / Codex / ZCode 复用)。
3. 分工互补:技能教"怎么做事",MCP 提供"工具访问",规则文件定"行为边界"——按需组合,不要用规则文件硬编码本该做成技能的流程。
4. 安装第三方技能前先审读 SKILL.md 与捆绑脚本,确认无危险命令;优先选有人工审核背书的来源(如 trailofbits/skills-curated)。

## 收录标准与贡献

- **收录**:官方或知名团队出品;或社区口碑明确(star / 活跃度 / 被引)、仍在维护、可直接取用。
- **剔除**:长期停更且已有替代、纯镜像转载、无许可证且授权不明。
- 欢迎提 PR 补充条目(附一句话点评与核对日期),或直接修正过时信息。
