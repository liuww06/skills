---
name: dotnet-scaffold
description: Scaffold new .NET codebases for libraries, desktop apps, web apps and services, using official templates or optional layered, Clean Architecture, DDD, MVVM and microservice structures. 用于从零搭建 .NET 类库、WPF 等应用及服务的基础结构；支持原始模板、简单布局及按需复杂架构。不用于修改已有代码库、迁移架构或单纯解释 C# 概念。
---

# .NET 项目脚手架

根据用户需求创建可继续开发的代码库，默认 C#、现代 SDK 风格、简单且最小可运行。只要求目录设计时输出设计，不创建文件。

## 边界与默认值

- 首版只新建代码库。先检查目标目录（包括隐藏文件）、Git 边界、项目指令及祖先配置。已有代码库不覆盖、不搬迁、不追加项目；请用户给出新目录。已有非代码文件也须保留，发生冲突时改用新目录。
- 默认标准布局、最少项目、官方模板。“简单”“最小可运行”只减少项目/能力数量，仍使用解决方案 + `src/<Name>/` + 共享开发配置；不等于原始布局。只有明确要求“官方原始结构”“不要 src/共享配置”等才进入原始模式。只请求 WPF 不隐含 MVVM；只请求类库不隐含测试、打包或分层。
- 用户明确要求原始/官方结构时保留模板组织和默认代码，不自动加入 `src/`、CPM、全局编译配置或额外解决方案。SDK 选择仍需确认实际生效版本。
- 先提取名称、目录、项目类型、布局、架构、UI 组织、服务边界、平台和附加能力。能推断的选项用简单默认值；Web API 默认 Minimal API。
- “微服务”未明确单个服务或多服务时，当前回复只澄清这一选择，等待答案后才读取场景参考、推荐目录树或选择配套能力。可以简述两种选择的区别，但不能先画多服务方案再在结尾提问。明确多服务但没有名称或职责时，先确认服务边界，不自行编造服务。
- 澄清可以直接问：“这是单个可独立部署的服务，还是由多个服务组成的代码库？”两种选择均不隐含分层、共享库、网关、数据库、缓存或消息队列；介绍选项时也不能把这些列为标配。
- DDD 缺少领域信息时询问核心领域/边界；若用户仅要通用骨架，可提供中性分层，不虚构聚合和业务。整洁代码“结构”按 Clean Architecture 理解，普通代码风格请求不触发分层。
- 原始结构与额外架构要求冲突时说明差异并澄清，不静默覆盖用户选择。
- 先简述将生成的结构与主要依赖，信息足够就继续，不设置固定确认关卡。第三方包只为所选能力引入，优先内置能力，不逐包请求批准。
- 只设计目录时，不把目标磁盘路径或本机工具安装状态作为必须回答的前置问题。未请求测试、容器、CI 等能力时不将它们列入默认产物。

## 按需加载

资源路径相对于本 Skill 目录。先解决上面的范围歧义；信息足够后读取 [SDK 与平台](references/sdk-and-platforms.md)，再按下表选择。不要一次读取整个 references 目录，也不提前加载未启用的附加能力。

| 条件 | 读取 |
|---|---|
| 标准布局 | [解决方案布局](references/solution-layout.md)、[共享配置与 CPM](references/shared-configuration.md) |
| Console / Class Library / Worker | [基础项目](references/basic-projects.md) |
| Web API / MVC / Razor Pages | [Web 项目](references/web-projects.md) |
| Blazor Web App / WASM Standalone | [Blazor](references/blazor-projects.md) |
| WPF / WinForms | [桌面项目](references/desktop-projects.md) |
| MAUI | [MAUI](references/maui-projects.md) |
| 传统分层 / Clean Architecture / DDD | [内部架构](references/architectures.md) |
| 明确选择 MVVM | [MVVM](references/mvvm.md) |
| 单个微服务 / 多服务系统 | [服务组织](references/microservices.md) |
| 测试 | [测试](references/testing.md) |
| 数据、认证、缓存、消息、观测 | [数据与通信](references/data-and-communication.md) |
| Docker、CI、打包、发布配置 | [交付](references/delivery.md) |
| 高性能 / 负载验证 | [性能](references/performance.md) |

原始结构路径跳过标准布局与 CPM 资料，除非用户又明确要求相应能力。简单结构无需读取架构文档。模板只在实际使用时读取/复制。

## 创建流程

1. 检查目标及配置继承范围，拒绝覆盖。确认用户范围和上述必要决策；不把新 `.sln` 等同于独立配置范围。
2. 选择 SDK/TFM。标准布局先写 global.json → 从目标目录确认 `dotnet --version` → 检查模板/workload → 才生成解决方案和项目。只输出创建计划时也使用这个顺序，global.json 不能推迟到步骤 5。安装需求按当前授权、权限及环境处理，不以生成项目为由默认安装所有平台工具链。
3. 按所选 SDK 的官方模板生成；支持时使用 `--no-restore`。明确每次命令的工作目录和目标路径，不依赖调用 Skill 时的目录。
4. 应用布局和项目引用。Clean Architecture、DDD、MVVM、微服务属于可组合维度，按命中规则实现，不自动堆叠框架、服务或依赖。
5. 标准布局应用共享配置；显式包依赖出现时启用 CPM。保留版本、条件及元数据，检查中央求值是否等价。只生成有用途的文件和目录。
6. 写 README：实际结构、职责、已选择的可选能力、具体构建/运行/测试命令及环境前提。只有长期项目约定才进入简短 `AGENTS.md`，不复制本 Skill 或其参考资料。
7. 独立新仓库默认 `git init`；已有 Git 边界内不建嵌套仓库。不自动提交、推送、发布。许可证只按用户要求生成。
8. 按下节验证，检查差异及目标目录外是否有意外改动。失败时修复本次生成内容，不改宿主机全局配置或不相关代码来让检查通过。

## 验证与交付

- 检查实际解决方案成员、ProjectReference 方向及包依赖；执行适用的 restore、build、`dotnet format --verify-no-changes`。明确具体解决方案/项目路径。
- 有测试时使用匹配的测试运行器。不能用空测试或占位断言宣称通过。
- 应用执行最小启动验证；类库构建即可，选择打包才验证 pack。服务启动检查真实端点；桌面编译不等于 UI 验证。
- 多服务分别构建、启动，检查端口和独立发布边界。混合平台分目标验证，尤其不要向每个 runner 提交完整 MAUI 多目标构建。
- 仅清理自己启动的进程。交付列出生成位置、结构选择、关键依赖、可执行命令，以及每项“通过 / 失败 / 环境阻塞 / 未验证”的证据。
- 高性能只报告实际测量；缺少目标或未运行负载测试时明确说明。参考中的支持能力不代表该平台已验证。
