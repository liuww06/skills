# 按需交付

只生成用户要求的 CI、容器、打包或发布配置。生成配置不等于执行外部发布，默认不上传包、注册系统服务、创建云资源或推送镜像。

## Docker 与本地编排

- 使用匹配 SDK/runtime 的官方 .NET 镜像；按应用选择 aspnet/runtime/runtime-deps，不混用。
- build context 包含 global.json、Directory.Build.props、Directory.Packages.props、必要引用项目和源文件；多服务默认仓库根作为 context，Dockerfile 位于各服务目录。
- 还原层与源码层分开，路径匹配真实结构；不能使用漏掉中央配置的“只复制 csproj”缓存示例。
- 明确监听地址、容器端口、用户/文件权限与环境配置，不将 secrets 写入镜像。
- 选择多服务容器编排时在 deploy 下生成 Compose，context 相对 Compose 文件解析；宿主端口唯一，服务间用服务 DNS/容器端口。
- Docker 不可用则只检查文件与路径，标为镜像构建/运行未验证。

## CI

用户指定供应商时遵循；只说需要 CI 且无上下文时默认 GitHub Actions。action 与镜像版本核实官方来源，不猜版本。CI 安装匹配 global.json 的 SDK，并执行实际项目的 restore/build/test，测试为空不能冒充通过。

| 项目 | runner |
|---|---|
| 普通跨平台库、Console、Worker、Web | Linux，除非原生依赖要求其他平台 |
| WPF / WinForms / MAUI Windows | Windows |
| MAUI Android | 具备已核实 Android SDK/JDK 的环境 |
| MAUI iOS / Mac Catalyst | 匹配 Xcode 的 macOS |

混合平台按项目/TFM 分任务；MAUI 明确 SDK、workload、工具链、TFM/RID、构建或签名范围，不让全部 runner 构建完整多目标解决方案。缓存键考虑 SDK 和实际包配置，不为简单项目强制创建 lock 文件。

## 打包

NuGet：仅需分发的库设置包元数据，名称/版本/许可证来自用户或项目约定；测试/示例不打包。执行 pack 后检查包内容，选择发布工作流时凭据用 CI secrets，不自动 push。

桌面单文件：确认 RID、框架依赖/自包含与本机库提取需求；不默认裁剪/AOT。MAUI 按平台配置签名，缺证书时只报告未签名/未验证，不生成真实秘密。

项目许可证由用户选择，不能继承脚手架插件 MIT。只有用户有开源要求才生成相应社区文件。
