# 标准代码库布局

单应用默认一个解决方案、`src/<Name>/<Name>.csproj`。名称使用用户选择或合理 PascalCase，不自动添加 Company 前缀。没有业务边界就不拆程序集。

按内容增加目录：`tests/`、`samples/`、`docs/`、`deploy/`、`perf/`。不预置空目录或用于凑齐层数的项目；用户明确选择 Clean Architecture 时，其项目边界本身就是用途，允许尚无领域业务类型。

解决方案默认与代码库同名。创建顺序如下，也适用于只输出计划时的命令说明：

1. 用 [global.json 资产](../assets/config/global.json.template) 在目标根目录写入 SDK 基线，替换完整稳定 SDK 版本并保留 allowPrerelease=false。
2. 切换到该目录，执行 `dotnet --version` 确认解析结果，然后检查模板帮助。
3. 才执行下面的解决方案/项目命令。global.json 属于模板调用前置条件，不能排在“随后生成共享配置”中。

利用 CLI 添加实际生成的项目及引用。命令写入 README 时替换所有名称/路径占位符。

```text
dotnet new sln --name MyApp
dotnet new classlib --name MyApp --output src/MyApp --no-restore
dotnet sln <actual-solution-path> add src/MyApp/MyApp.csproj
```

区分磁盘路径和 solution folder；确认解决方案显示组织符合预期。不要为了 solution folder 移动已经生成正确的磁盘目录。

多服务使用 `services/<ServiceName>/src/`，测试放同服务下的 `tests/`，根解决方案作为开发入口，服务项目保持独立构建能力；细节见 [服务组织](microservices.md)。

README 保留：目录职责、SDK/平台前提、实际 restore/build/run/test 命令、所选能力的运行方式。库没有 `dotnet run`，无测试不列虚假的成功测试命令。首次创建独立仓库时通过 `dotnet new gitignore` 生成忽略规则，再按真实产物调整。

先用只读 Git 检查确认目标是否处于已有仓库。只有不属于任何已有仓库才 `git init`，不设置作者、不自动 commit/push。已有目录只含文档时也先检查文件冲突；不默认覆盖 README 或配置。首版不改造已有代码库。
