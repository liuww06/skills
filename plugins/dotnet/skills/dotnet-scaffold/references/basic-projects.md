# Console、Class Library、Worker

| 类型 | 官方模板 | 最小产物 |
|---|---|---|
| Console | console | 单个可运行项目；不为普通命令行默认加入 Generic Host 或参数库 |
| Class Library | classlib | 单个库项目；保留用户领域名称，没有需求不制造公共 API |
| Worker | worker | 官方 BackgroundService/Host 生命周期，支持停止令牌 |

检查模板帮助后传入名称、目录、C# 和所需 TFM。标准结构可删除本次模板生成且没有用途的 Class1/演示逻辑；原始模式保留官方输出。

库：内部引用与 NuGet 发布是独立能力。默认不生成 samples、测试或包发布工作流；启用打包时参阅 [交付](delivery.md)，选择与消费者兼容的 TFM，不因为 SDK 较新就排除实际消费者。

Console：没有业务时保留最少入口。仅用户要求完整演示时补真实演示，不引入无用 Service/Manager/Helper 层。

Worker：保留取消和优雅停止，不能空转或用阻塞 sleep 替代异步等待。没有具体任务时模板心跳可作为启动骨架，说明尚未实现业务。Windows Service、systemd、容器是部署选项，按需配置；不自动注册系统服务。

验证：Console 有限运行并检查退出码；Worker 检查启动日志后停止自己启动的进程；库 build，通过不代表业务测试。显式包引用（如 Worker Hosting）纳入标准布局 CPM。
