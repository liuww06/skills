using System.Collections.Concurrent;
using System.Threading.Channels;
namespace Queue.Worker;
public sealed class WorkQueue
{
    public TaskCompletionSource Started { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
    public Channel<string> Input { get; } = Channel.CreateUnbounded<string>();
    public Channel<string> Completed { get; } = Channel.CreateUnbounded<string>();
    public ConcurrentQueue<Exception> Errors { get; } = new();
    public Func<string, CancellationToken, Task> Process { get; set; } = (_, _) => Task.CompletedTask;
}
public sealed class QueueWorker(WorkQueue queue) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        queue.Started.TrySetResult();
        var completed = new HashSet<string>();
        try
        {
            await foreach (var id in queue.Input.Reader.ReadAllAsync(stoppingToken))
            {
                if (completed.Contains(id)) continue;
                try
                {
                    await queue.Process(id, stoppingToken);
                    completed.Add(id);
                    await queue.Completed.Writer.WriteAsync(id, stoppingToken);
                }
                catch (InvalidOperationException error) { queue.Errors.Enqueue(error); }
            }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { }
        finally { queue.Completed.Writer.TryComplete(); }
    }
}
