# Blazor

先区分 `blazor`（Web App）与 `blazorwasm`（独立 WASM），再选择交互模式。未给运行形态且会影响部署时询问，不把 Server、WebAssembly、Auto 当作可互换选项。

- Web App：使用 SDK 支持的静态、Server、WebAssembly 或 Auto 参数。静态模式不生成交互绑定示例。
- WASM/Auto：模板可能生成服务端和 `.Client` 项目；保留项目关系、静态资源与交互注册。递归清点所有项目后加入解决方案并转换包版本。
- Standalone WASM：独立客户端，由静态站点托管；不要擅自加服务端项目。客户端不能直接连接需要私密凭据的数据库。

使用 `dotnet new blazor --help` 确认参数；例如支持时 `--interactivity Auto --no-restore`，不能仅凭目录名推断是否有 Client。原始模式保留模板输出，标准模式也不把自动生成的 Client 当无用示例删除。

服务端密钥只存在服务端配置或 user-secrets 中，客户端配置均视为可公开。需要 API 时明确地址/CORS/认证路径；不把用户秘密写入 wwwroot。

验证：还原并构建所有生成项目，运行服务端/独立开发服务器，检查页面加载。只有 HTTP 成功不足以证明 WASM 下载与交互有效；具备浏览器环境才验证交互，否则单列未验证。发布静态站点与发布 Web App 使用不同目标，不混淆。

官方参数参考：[.NET 默认模板](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates)。
