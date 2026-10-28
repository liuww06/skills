using System.Net;
using System.Net.Http.Json;
using Catalog.Api;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using Xunit;

public sealed class CatalogFactory : WebApplicationFactory<Program>
{
    public string DatabasePath { get; } = Path.Combine(Path.GetTempPath(), $"catalog-{Guid.NewGuid()}.db");
    protected override void ConfigureWebHost(IWebHostBuilder builder) => builder.UseSetting("CatalogDatabase", DatabasePath);
    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        SqliteConnection.ClearAllPools();
        foreach (var suffix in new[] { "", "-wal", "-shm" }) File.Delete(DatabasePath + suffix);
    }
}
public sealed class ApiTests
{
    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public async Task RejectsInvalidQuantityWithoutPersisting(int quantity)
    {
        using var factory = new CatalogFactory();
        using var client = factory.CreateClient();
        Assert.Equal(HttpStatusCode.BadRequest, (await client.PostAsJsonAsync("/products", new CreateProduct("invalid", quantity))).StatusCode);
        await using var db = new CatalogDb(new DbContextOptionsBuilder<CatalogDb>().UseSqlite($"Data Source={factory.DatabasePath}").Options);
        Assert.Empty(await db.Products.ToListAsync());
    }
    [Fact]
    public async Task PersistsAndRejectsDuplicateSku()
    {
        using var factory = new CatalogFactory();
        using var client = factory.CreateClient();
        var created = await client.PostAsJsonAsync("/products", new CreateProduct("item-1", 3));
        Assert.Equal(HttpStatusCode.Created, created.StatusCode);
        var product = await client.GetFromJsonAsync<Product>(created.Headers.Location);
        Assert.NotNull(product);
        Assert.Equal(3, product.Quantity);
        Assert.Equal(HttpStatusCode.Conflict, (await client.PostAsJsonAsync("/products", new CreateProduct("item-1", 2))).StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/products/99999")).StatusCode);
    }
    [Fact]
    public async Task MigratesExistingRows()
    {
        var path = Path.Combine(Path.GetTempPath(), $"migration-{Guid.NewGuid()}.db");
        try
        {
            await using var db = new CatalogDb(new DbContextOptionsBuilder<CatalogDb>().UseSqlite($"Data Source={path};Pooling=False").Options);
            await db.GetService<IMigrator>().MigrateAsync("20260101000000_Initial");
            await db.Database.ExecuteSqlRawAsync("INSERT INTO Products (Sku, Quantity) VALUES ('legacy', 4)");
            await db.Database.MigrateAsync();
            var product = await db.Products.SingleAsync();
            Assert.Equal("legacy", product.Sku);
            Assert.Equal(4, product.Quantity);
            Assert.Equal(0m, product.Price);
        }
        finally { File.Delete(path); }
    }
}
