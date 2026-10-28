using Queue.Worker;
var builder = Host.CreateApplicationBuilder(args);
builder.Services.AddSingleton<WorkQueue>();
builder.Services.AddHostedService<QueueWorker>();
await builder.Build().RunAsync();
