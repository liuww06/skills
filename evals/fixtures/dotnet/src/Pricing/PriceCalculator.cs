namespace Pricing;

public static class PriceCalculator
{
    public static decimal Total(decimal unitPrice, int quantity)
    {
        if (quantity <= 0) throw new ArgumentOutOfRangeException(nameof(quantity));
        if (unitPrice < 0) throw new ArgumentOutOfRangeException(nameof(unitPrice));
        var subtotal = unitPrice * quantity;
        var discounted = quantity >= 10 ? subtotal * 0.9m : subtotal;
        return decimal.Round(discounted, 2, MidpointRounding.ToEven);
    }
}
