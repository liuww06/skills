using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Queue.Worker;
using Xunit;
public sealed class WorkerTests
{
    private static IHost Create(WorkQueue queue) => new HostBuilder()
        .ConfigureServices(services => services.AddSingleton(queue).AddHostedService<QueueWorker>()).Build();
    [Fact]
    public async Task DeduplicatesCompletedItems()
    {
        var queue = new WorkQueue();
        using var host = Create(queue);
        queue.Input.Writer.TryWrite("order-1");
        queue.Input.Writer.TryWrite("order-1");
        queue.Input.Writer.TryComplete();
        await host.StartAsync();
        var actual = new List<string>();
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        await foreach (var id in queue.Completed.Reader.ReadAllAsync(deadline.Token)) actual.Add(id);
        Assert.Equal(new[] { "order-1" }, actual);
        await host.StopAsync().WaitAsync(TimeSpan.FromSeconds(2));
    }
    [Fact]
    public async Task RecoversAndRetriesAfterFailure()
    {
        var queue = new WorkQueue();
        var calls = 0;
        queue.Process = (_, _) => ++calls == 1 ? Task.FromException(new InvalidOperationException("transient")) : Task.CompletedTask;
        using var host = Create(queue);
        queue.Input.Writer.TryWrite("order-2");
        queue.Input.Writer.TryWrite("order-2");
        queue.Input.Writer.TryComplete();
        await host.StartAsync();
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        Assert.Equal("order-2", await queue.Completed.Reader.ReadAsync(deadline.Token));
        await queue.Completed.Reader.Completion.WaitAsync(deadline.Token);
        Assert.Single(queue.Errors);
        await host.StopAsync().WaitAsync(TimeSpan.FromSeconds(2));
    }
    [Fact]
    public async Task StopsWhileWaitingForInput()
    {
        var queue = new WorkQueue();
        using var host = Create(queue);
        await host.StartAsync();
        await queue.Started.Task.WaitAsync(TimeSpan.FromSeconds(5));
        await host.StopAsync().WaitAsync(TimeSpan.FromSeconds(2));
        Assert.True(queue.Completed.Reader.Completion.IsCompletedSuccessfully);
    }
}
