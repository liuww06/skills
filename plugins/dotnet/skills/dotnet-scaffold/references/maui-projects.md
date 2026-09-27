# MAUI

使用 `maui` 官方模板。先明确目标平台及开发/CI 环境，再检查 workload、完整 TFM 和原生工具链；不默认安装全套平台。

MAUI 有独立于 .NET LTS 的生命周期。分别核对 [.NET MAUI 支持政策](https://dotnet.microsoft.com/en-us/platform/support/policy/maui) 和 [安装/平台要求](https://learn.microsoft.com/en-us/dotnet/maui/get-started/installation)，不能由 SDK 受支持推断 workload 或 Xcode 组合受支持。

| 目标 | 必查 |
|---|---|
| Windows | maui-windows、Windows SDK、完整 Windows TFM 与最低系统版本 |
| Android | 对应 workload、Android SDK/JDK、设备/模拟器是否可用 |
| iOS / Mac Catalyst | 兼容 macOS/Xcode、对应 workload、设备或模拟器、签名要求 |

保留模板平台条件、资源、平台入口及完整 TFM。明确要求仅某平台时可收窄目标，但不能通过删掉平台后缀、最低版本属性或资源来让构建变绿。

`$(MauiVersion)` 等表达式在 CPM 中必须验证求值顺序，参阅 [共享配置](shared-configuration.md)。不要无依据固定一个与 workload 不兼容的包版本。

按目标 restore/build，命令明确 TFM；必要时给 RID。注意 `build -f` 不一定将隐式 restore 收窄到单目标：采用该 SDK 支持的 `TargetFrameworks` 限定还原范围，再以相同范围 `--no-restore` 构建，并检查依赖图，不改源项目掩盖缺失工具链。

验证状态分别记录：生成、目标还原、目标编译、模拟器/设备运行、打包与签名。只安装 workload 未验证原生 SDK 时标为环境待确认。不能将所有目标直接交给同一个 CI runner。
