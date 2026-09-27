# 配套测试

测试是按需能力。用户要求时默认 xUnit，先检查所选 SDK 的 `xunit` 模板和包版本。使用模板匹配的运行器，不混用 VSTest/Microsoft.Testing.Platform 参数，也不为一个测试项目默认改变整个 SDK 的 test runner。

单元测试只引用所测逻辑项目；集成测试根据真实宿主与外部依赖另建项目，不强制两类同时存在。多服务测试归所属服务。测试包保留模板 PrivateAssets/IncludeAssets 等元数据并纳入 CPM。

删除模板无行为的空测试。对实际生成行为测试：ViewModel 属性变化、用户提供的不变量、服务健康端点或依赖注入组合。没有可测行为且用户只要测试骨架时保留项目并明确“尚无测试用例”，不能把 0 tests 描述为通过。

HTTP 集成测试需要 WebApplicationFactory 时使用与目标框架匹配的 Microsoft.AspNetCore.Mvc.Testing；必要时公开宿主 Program 给测试。不要通过真实生产连接测试数据库、消息或认证。

README 列具体 `dotnet test <project-or-solution>` 或所选运行器要求的命令；平台混合时限定项目，记录用例数量与结果。不要以假断言满足覆盖率或测试成功要求。
