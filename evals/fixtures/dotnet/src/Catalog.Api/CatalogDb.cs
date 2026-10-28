using Microsoft.EntityFrameworkCore;
namespace Catalog.Api;
public sealed record CreateProduct(string Sku, int Quantity);
public sealed class Product
{
    public int Id { get; set; }
    public string Sku { get; set; } = "";
    public int Quantity { get; set; }
    public decimal Price { get; set; }
}
public sealed class CatalogDb(DbContextOptions<CatalogDb> options) : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    protected override void OnModelCreating(ModelBuilder model)
    {
        model.Entity<Product>().HasIndex(p => p.Sku).IsUnique();
    }
}
