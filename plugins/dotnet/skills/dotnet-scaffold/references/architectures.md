# 应用内部架构

只在用户指定架构或需求包含明确边界时加载。简单项目保持一个程序集。分层数量来自选定结构与实际职责，不为每个名词建项目。

## 传统分层

- 宿主/UI → Business → DataAccess。
- Business 承载业务操作，DataAccess 承载已选持久化实现；没有持久化需求时仅宿主/UI → Business。
- 不把此引用方向冒充 Clean Architecture。若需要依赖倒置，选择下面的规则。

## Clean Architecture

```text
src/
  MyApp.Domain/
  MyApp.Application/
  MyApp.Infrastructure/
  MyApp.Api/                # 或用户选择的宿主/UI
```

| 项目 | 允许的内部直接引用 | 职责 |
|---|---|---|
| Domain | 无 | 领域类型及不变量，不依赖 UI、数据库实现、宿主框架 |
| Application | Domain | 用例及应用所需端口 |
| Infrastructure | Application；确有用途时 Domain | 数据访问、外部系统等端口实现 |
| 宿主 | Application、Infrastructure | 入口与组合根；Infrastructure 只在组合入口使用 |

以 `classlib` 生成三层，宿主用对应模板；使用 CLI 添加引用。移除本次模板的 Class1，领域信息缺失时允许空的领域程序集，不用 EntityBase/RepositoryBase 凑内容。

需要注册入口时可在 Application/Infrastructure 使用核实版本的 `Microsoft.Extensions.DependencyInjection.Abstractions`，提供 `AddApplication(IServiceCollection)`、`AddInfrastructure(IServiceCollection)` 扩展并在宿主调用；不要让 Domain 为了注册服务引用 DI 包。没有实现时扩展可返回原 services，说明这是组合入口，不声称存在业务链路。不要把整个 ASP.NET 共享框架引入普通库以省掉小型包引用。

验证 ProjectReference 的有向关系，重点排除 Domain → Infrastructure、Application → 宿主、循环引用。只检查四个目录存在不足以证明架构正确。业务代码不得通过组合根之外的具体基础设施类型绕开接口。

## DDD

默认沿用上述项目边界，按用户提供的限界上下文及聚合组织 Domain；用例放 Application，持久化/外部适配放 Infrastructure。

仅在信息足够时创建：聚合根、实体、值对象、领域服务/事件及对应行为。用户只给“订单服务”名称并不能推断订单状态机、付款规则或一致性需求。缺信息先问；只要求通用结构则保留中性边界并记录领域待定义。

不默认添加 CQRS、MediatR、通用仓储、工作单元、事件总线、对象映射或贫血 CRUD 样例。一个限界上下文不自动等于一个微服务；需服务拆分时读取 [服务组织](microservices.md)。

参考：[常见架构与依赖倒置](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures)、[微服务领域模型](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model)。
