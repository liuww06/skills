# .NET 存量项目验证

只在目标项目为 .NET 时读取。沿用其 SDK、TFM、包源、中央包管理、测试框架及启动方式，不把本仓库夹具的 .NET 10 版本强加给用户项目。本插件可独立使用，不依赖 dotnet 插件安装。

## 找到真实构建入口

读取 global.json、解决方案、Directory.Build.props/targets、Directory.Packages.props、NuGet.Config、工具清单和 CI。从正确目录运行 dotnet --info，按现有流程还原、构建、测试。记录实际解析的 SDK、目标框架、配置和测试数量；区分声明的 ProjectReference/PackageReference 与条件求值后生效的引用。多目标框架不能只验证其中一个却声称全部通过。

## ASP.NET Core 与持久化

沿用现有测试宿主；适用时用 [WebApplicationFactory](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests) 走完整路由、绑定、过滤器、中间件与 DI。验证状态码、响应体、头部、无效输入和副作用，不能由健康端点正常推断业务端点正确。

涉及查询翻译、排序/大小写、事务、唯一约束、迁移时，使用隔离的同类型数据库。生产使用 SQLite 的夹具可以测试临时 SQLite 文件；生产使用 PostgreSQL/SQL Server 时，SQLite 或 EF InMemory 的通过不能证明生产语义。参见 [EF Core 测试策略](https://learn.microsoft.com/en-us/ef/core/testing/choosing-a-testing-strategy)。数据库或容器不可用时可继续独立的单元检查，并明确集成验证阻塞。

## Worker 与类库

Worker 通过现有 Generic Host 启动/停止路径验证取消传播、异常策略、重试和重复处理；等待可观察的信号而非固定 sleep，用有界超时防止挂起。StopAsync 返回并不自动证明最后一条消息已正确处理。

类库关注公开签名、边界值、数值舍入、文化区、序列化字段与枚举表示、异常类型、排序和副作用。只对本次改动涉及的契约增加测试。行为对照和必要时的 API/消费者编译检查，比私有方法或 mock 调用次数更有意义。
