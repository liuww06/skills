using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
namespace Catalog.Api.Migrations;
[DbContext(typeof(CatalogDb))]
public sealed class CatalogDbModelSnapshot : ModelSnapshot
{
    protected override void BuildModel(ModelBuilder model)
    {
        model.HasAnnotation("ProductVersion", "10.0.14");
        model.Entity("Catalog.Api.Product", entity =>
        {
            entity.Property<int>("Id").ValueGeneratedOnAdd().HasColumnType("INTEGER");
            entity.Property<decimal>("Price").HasColumnType("TEXT");
            entity.Property<int>("Quantity").HasColumnType("INTEGER");
            entity.Property<string>("Sku").IsRequired().HasColumnType("TEXT");
            entity.HasKey("Id");
            entity.HasIndex("Sku").IsUnique();
            entity.ToTable("Products");
        });
    }
}
