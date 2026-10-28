using Pricing;
using Xunit;
public sealed class PriceTests
{
    [Theory]
    [InlineData(9, 90)]
    [InlineData(10, 90)]
    [InlineData(11, 99)]
    public void DiscountBoundary(int quantity, decimal expected) => Assert.Equal(expected, PriceCalculator.Total(10m, quantity));
    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public void RejectsNonpositiveQuantity(int quantity) => Assert.Throws<ArgumentOutOfRangeException>(() => PriceCalculator.Total(10m, quantity));
    [Fact]
    public void RoundsToEven() => Assert.Equal(10.00m, PriceCalculator.Total(10.005m, 1));
}
