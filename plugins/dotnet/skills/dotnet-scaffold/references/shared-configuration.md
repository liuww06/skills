# 共享配置与 CPM

仅用于标准布局，先确认配置影响范围。新解决方案不等于新配置范围；不修改祖先配置，不向已有项目上方放置新配置。已有中央配置被新文件遮蔽时，先判断影响和显式导入关系；无法隔离时选择新目录。

## 配置资产

| 资产 | 输出文件 | 规则 |
|---|---|---|
| [global.json.template](../assets/config/global.json.template) | global.json | 先替换唯一占位符 `{{SDK_VERSION}}`，调用模板前落盘 |
| [Directory.Build.props.template](../assets/config/Directory.Build.props.template) | Directory.Build.props | C# Nullable/ImplicitUsings；保留模板显式覆盖，不集中 TFM |
| [editorconfig.template](../assets/config/editorconfig.template) | .editorconfig | 基本格式，不扩大分析器/警告策略 |
| [Directory.Packages.props.template](../assets/config/Directory.Packages.props.template) | Directory.Packages.props | 仅有显式包依赖时复制，并填入实际 PackageVersion |

不额外设置 TreatWarningsAsErrors、AnalysisLevel、IsPackable、AOT、裁剪或单文件发布。打包属性放入需要打包的项目。Directory.Build.targets、NuGet.Config 仅在有明确用途时编写，不生成空文件或通用包源配置。

Windows 官方模板可能带 BOM/CRLF，与这里的 UTF-8/LF 风格不同。标准布局对本次新生成源码应用所选格式后，再运行 `dotnet format --verify-no-changes`；不要只复制 .editorconfig 就声称模板已经符合它。原始模式不自动格式化官方输出，既有文件不在格式化范围内。

Directory.Build.props 自动查找最近文件，且较早导入；其中引用后定义属性可能为空。CPM 默认也只自动导入最近的 Directory.Packages.props。检查项目、祖先及显式 Import，不假定多级自动合并。必要时使用 `dotnet msbuild <project> /pp:<output>` 检查导入顺序和求值位置。

## 新生成项目的 CPM 转换

1. 清点所有生成项目（含 `.Client`、测试）中的显式 PackageReference；包含 ItemGroup/Item 自身条件，版本属性或子元素及其他元数据。
2. 无显式包时不生成中央文件。否则启用 `ManagePackageVersionsCentrally`，将实际版本放入 PackageVersion。
3. 同包同版本复用；同包不同版本先判断是否需要条件版本。不能通过取最高版本、覆盖或删掉差异来“统一”。只有仓库策略允许且确有用途才采用 VersionOverride；它不是常规转换方式。
4. 版本迁移后移除 PackageReference 的 Version 属性/子元素；保留引用的 Condition、PrivateAssets、IncludeAssets、ExcludeAssets 等元数据。VersionOverride 如已明确使用须单独处理，不误删。
5. 版本表达式在新导入位置未必可用。特别检查项目内属性、`$(MauiVersion)`、TFM 条件和 `MSBuildThisFileDirectory`；不要仅把文本搬到中央文件就认为语义相同。必要时重新安排定义位置或使用核实过的明确版本；不能确认则报告未完成转换。
6. 在每个目标 TFM/必要配置上 restore；检查求值后的版本与依赖图。重复有效 PackageVersion、缺失版本、降级均须处理，不以单个框架通过代替整个范围。

保留包版本选择的来源：官方模板、用户指定或核实的稳定包。新加第三方包先核实其版本/TFM 兼容性，不采用浮动版本。不要把 SDK 隐式依赖集中列出，不默认传递依赖固定，不自动升级其他包。

存在多个 NuGet 包源时，CPM 可能提示源映射问题；依据实际依赖与包源补映射，不能默认清空企业源、复制凭据或直接抑制告警。

依据：[CPM](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management)、[目录配置与导入顺序](https://learn.microsoft.com/en-us/visualstudio/msbuild/customize-by-directory)。
