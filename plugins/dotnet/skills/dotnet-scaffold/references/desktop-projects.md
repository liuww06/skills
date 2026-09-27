# WPF 与 WinForms

默认使用 `wpf` / `winforms` 官方模板，保留完整 Windows TFM、UseWPF/UseWindowsForms 及必要入口，不套用普通 `netX.0` 覆盖平台信息。只要求前端基础结构时保持一个应用项目，不增加 MVVM 或业务层。

WPF 仅选择 MVVM 后读取 [MVVM](mvvm.md)。普通 WPF 保留 App/MainWindow。WinForms 保留 Designer、资源文件与 partial 类协作，不为统一风格把控件初始化移出设计器约定。

代码与资源目录按实际内容增加。只有复用业务、独立测试或领域边界才拆库；UI 代码不得进入无平台的 Domain 项目。

编译默认在 Windows 验证。非 Windows 即使开启 EnableWindowsTargeting 并构建成功，也不能标为启动/绑定通过。UI 验证记录窗口、绑定或交互的实际证据；无交互桌面环境时只报告编译结果。

单文件发布按需选择 RID、框架依赖或自包含；不默认启用 trimming/AOT。发布通过不等于安装器、签名或目标机器运行通过。
