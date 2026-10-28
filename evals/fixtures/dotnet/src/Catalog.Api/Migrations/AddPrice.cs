using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
namespace Catalog.Api.Migrations;
[DbContext(typeof(CatalogDb))]
[Migration("20260201000000_AddPrice")]
public sealed class AddPrice : Migration
{
    protected override void Up(MigrationBuilder migration) => migration.AddColumn<decimal>(
        name: "Price", table: "Products", type: "TEXT", nullable: false, defaultValue: 0m);
    protected override void Down(MigrationBuilder migration) => migration.DropColumn("Price", "Products");
}
