# SDK、模板与平台

## 选择并使 SDK 生效

优先用户要求，再看祖先配置及消费工具约束。新建默认选择仍受支持的稳定 LTS；核对 [.NET 支持政策](https://dotnet.microsoft.com/en-us/platform/support/policy)，不把本机最高版本等同于合适版本，也不写死“最新版本”。离线时记录依据和未核实事项。SDK 版本与项目 TFM 分开选择。

检查 `dotnet --list-sdks`，从目标工作目录检查 `global.json` 及 `dotnet --version`。标准布局先将 [global.json 模板](../assets/config/global.json.template) 中 `{{SDK_VERSION}}` 替换为完整稳定 SDK 版本，再检查生效版本，最后调用模板。`latestFeature` 允许同 major/minor 的更新 feature band/patch，不是精确锁定。

原始模式不默认添加 global.json：若当前解析版本满足选择则直接生成；否则使用可验证的独立 SDK 环境，或先向用户说明必须增加 SDK 配置，不能声称 CLI 自动使用了选定 SDK。显式指定的 SDK 不可用时报告缺项，不能静默改用其他版本。

检查祖先 `Directory.Build.*`、`Directory.Packages.props`、NuGet.Config、.editorconfig 和 Git 边界，记录目标目录是否真正独立。CLI 从工作目录解析 SDK，传入项目路径并不保证解析起点改变；参见 [global.json](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json)。

## 调用前检查

```text
dotnet new list
dotnet new <template> --help
dotnet workload list
```

按所选 SDK 帮助选择参数，不从历史示例猜测可用选项。`--framework` 使用模板支持的完整值；`--no-restore` 仅在模板支持时添加。明确 `--language C#`（模板支持时），避免语言歧义。不要使用 `--force` 覆盖用户文件。

解决方案格式以模板帮助与消费工具为准；SDK 默认 `.slnx` 但工具需 `.sln` 时使用支持的格式参数。后续使用实际路径，不能硬编码默认后缀。Blazor 等模板可能同时生成多个项目，递归清点后加入解决方案。

## 平台约束

| 类型 | 验证前提 |
|---|---|
| 普通库、Console、Worker、Web | 对应 SDK/runtime；第三方原生依赖另查 |
| WPF、WinForms | 默认 Windows + WindowsDesktop targeting pack/runtime；非 Windows 的 EnableWindowsTargeting 只可能帮助编译，不能验证 UI |
| MAUI | 对应 workload、TFM、原生 SDK/JDK/Xcode、必要签名环境；详见 MAUI 参考 |

区分生成文件、还原、编译、运行、打包、签名及发布。发现 workload 不代表整条原生工具链可用。CI 与开发机的 SDK/TFM、目标架构都要匹配。

沙箱若禁止写默认 CLI 缓存，可为本次验证进程设置可写的 `DOTNET_CLI_HOME`、NuGet 缓存目录并记录；不要写入生成项目的永久环境配置，也不要修改用户全局设置。
