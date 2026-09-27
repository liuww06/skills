# Web API、MVC、Razor Pages

| 类型 | 模板 | 关键选项 |
|---|---|---|
| Web API | webapi | 默认 Minimal API；Controllers 使用该 SDK 帮助中的控制器选项 |
| MVC | mvc | 服务端页面及用户明确要求的认证 |
| Razor Pages | webapp | 页面与必要认证 |

默认不加入数据库、认证框架、映射器或 API 网关。用户明确要求认证但身份来源不明时询问；不得生成看似保护端点、实际绕过验证的占位认证。

标准 API 骨架可移除 WeatherForecast 示例；没有业务端点时以 `/health` 健康检查验证启动，使用内置 `AddHealthChecks` 与 `MapHealthChecks`。普通健康检查只证明进程响应，不能假装验证了数据库或其他依赖。Controllers 场景保留 AddControllers/MapControllers 注册。

OpenAPI 遵循所选模板/用户需求，不假定 SDK 默认带 Swagger UI。保留开发环境限制，不将开发文档及异常详情无条件公开。

MVC/Razor 保留可启动的模板页面，按用户范围精简，不自动改 SPA。服务端本地密钥使用 user-secrets 或已有受支持方式，配置文件只放非敏感示例；不输出真实令牌。

README 写明具体项目及本地 URL，服务启动验证使用已配置的 HTTP/HTTPS 地址。测试环境使用 HTTP 时单独设置端口/启动配置，不能因为证书问题永久移除用户选择的 HTTPS。

选择分层时读取 [内部架构](architectures.md)；微服务及性能能力分别读取其参考。不要仅因 API 类型就加载并应用这些结构。
