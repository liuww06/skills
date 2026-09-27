# 性能能力

“高性能”不是架构预设，也不是自动增加 Redis、消息队列或 AOT 的理由。微服务范围仍需先确认。

提取主要负载、运行环境、吞吐/延迟目标；可简短询问缺项，但未提供指标时仍可生成基础骨架，明确无性能验收阈值。对生成的 I/O 使用异步/取消，避免同步阻塞、无限队列、无界并发。默认内置日志与 HTTP 健康检查，不凭空创建业务端点。

## HTTP 冒烟负载

将 [smoke.js](../assets/performance/smoke.js) 复制为 `perf/smoke.js`，无需替换占位符。README 给出用户 shell 可执行的命令，例如：

```text
k6 run -e BASE_URL=http://127.0.0.1:5080 -e TARGET_PATH=/health -e VUS=2 -e DURATION=10s perf/smoke.js
```

脚本默认不设置性能阈值；只有已有目标时提供 `P95_MS` 和/或 `MAX_ERROR_RATE`（0..1）。`EXPECTED_STATUS` 默认 200，可指定实际契约状态码。目标必须是本地或用户明确授权的测试环境，不能默认向生产或第三方服务发起负载。

脚本采用少量虚拟用户和思考时间，适合冒烟，不是最大吞吐测量。k6 不存在时保留可运行脚本并说明未运行，不自动安装或上传云端结果。服务为 Worker/纯 gRPC 时不制造虚假 HTTP 业务负载，说明 HTTP 脚本不覆盖其工作负载，需要匹配协议的后续验证。

记录：日期、SDK、Release 配置、主机/容器资源、目标 URL/端点、并发、时长、吞吐、p95/p99、错误率及阈值。健康检查测量仅证明该端点表现，不能推断真实业务性能；Debug 或启动阶段结果不能作为正式性能结论。

裁剪、AOT、对象池、序列化、GC/Kestrel 调整仅在实际需求/测量支持时启用，并验证反射、平台及库兼容性。

依据：[ASP.NET Core 性能实践](https://learn.microsoft.com/en-us/aspnet/core/performance/performance-best-practices)、[k6 选项](https://grafana.com/docs/k6/latest/using-k6/k6-options/reference/)。
