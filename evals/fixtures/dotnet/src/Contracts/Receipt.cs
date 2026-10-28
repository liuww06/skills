using System.Text.Json.Serialization;
namespace Contracts;
public sealed record Receipt(
    [property: JsonPropertyName("amount")] decimal Amount,
    [property: JsonPropertyName("currency")] string Currency);
