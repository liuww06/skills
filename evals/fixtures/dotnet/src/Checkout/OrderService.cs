using Contracts;
using Pricing;
namespace Checkout;
public sealed class OrderService
{
    public Receipt Place(decimal unitPrice, int quantity) => new(PriceCalculator.Total(unitPrice, quantity), "CNY");
}
