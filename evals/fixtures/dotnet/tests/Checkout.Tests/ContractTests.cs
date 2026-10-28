using Checkout;
using System.Text.Json;
using Xunit;
public sealed class ContractTests
{
    [Fact]
    public void SerializedReceiptContract()
    {
        var receipt = new OrderService().Place(10m, 10);
        using var document = JsonDocument.Parse(JsonSerializer.Serialize(receipt));
        Assert.Equal(90m, document.RootElement.GetProperty("amount").GetDecimal());
        Assert.Equal("CNY", document.RootElement.GetProperty("currency").GetString());
        Assert.Equal(2, document.RootElement.EnumerateObject().Count());
    }
}
