using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
namespace Catalog.Api.Migrations;
[DbContext(typeof(CatalogDb))]
[Migration("20260101000000_Initial")]
public sealed class Initial : Migration
{
    protected override void Up(MigrationBuilder migration) => migration.Sql("""
        CREATE TABLE "Products" (
          "Id" INTEGER NOT NULL CONSTRAINT "PK_Products" PRIMARY KEY AUTOINCREMENT,
          "Sku" TEXT NOT NULL, "Quantity" INTEGER NOT NULL);
        CREATE UNIQUE INDEX "IX_Products_Sku" ON "Products" ("Sku");
        """);
    protected override void Down(MigrationBuilder migration) => migration.DropTable("Products");
}
