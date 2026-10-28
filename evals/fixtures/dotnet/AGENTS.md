# Maintenance fixture conventions

Use the pinned SDK and existing xUnit tests. Build and test from this directory with
`dotnet test Maintenance.slnx --logger trx --results-directory TestResults`.
Keep public contracts unless the task explicitly changes them. Preserve existing
user changes. Do not add packages or replace the test framework for routine fixes.

Pricing rounds to two decimal places using midpoint-to-even. Ten or more units
receive a 10 percent discount. Nonpositive quantities throw ArgumentOutOfRangeException.
Catalog uses SQLite in production for this fixture: HTTP input validation, unique
SKUs and migrations must use isolated SQLite databases, not EF InMemory.
Worker retries an item if processing previously failed, ignores completed duplicate
IDs, and exits promptly on host cancellation.
Checkout depends on Pricing and Contracts; neither dependency may reference Checkout.
