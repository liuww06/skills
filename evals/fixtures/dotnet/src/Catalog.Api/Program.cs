using Catalog.Api;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<CatalogDb>(options => options.UseSqlite(
    $"Data Source={builder.Configuration["CatalogDatabase"] ?? "catalog.db"}"));
var app = builder.Build();
using (var scope = app.Services.CreateScope())
    scope.ServiceProvider.GetRequiredService<CatalogDb>().Database.Migrate();
app.MapPost("/products", async (CreateProduct request, CatalogDb db) =>
{
    if (string.IsNullOrWhiteSpace(request.Sku) || request.Quantity <= 0)
        return Results.BadRequest();
    var product = new Product { Sku = request.Sku, Quantity = request.Quantity };
    db.Products.Add(product);
    try { await db.SaveChangesAsync(); }
    catch (DbUpdateException error) when (error.InnerException is Microsoft.Data.Sqlite.SqliteException { SqliteErrorCode: 19 })
    { return Results.Conflict(); }
    return Results.Created($"/products/{product.Id}", product);
});
app.MapGet("/products/{id:int}", async (int id, CatalogDb db) =>
    await db.Products.FindAsync(id) is { } product ? Results.Ok(product) : Results.NotFound());
app.Run();
public partial class Program { }
