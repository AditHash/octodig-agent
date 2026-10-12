# Database operations and verification

OctoDig uses an external PostgreSQL service. Do not point tests at a customer or
production database. No Docker database is included or required.

## Migration workflow

`uv run alembic current` and `uv run alembic upgrade head` now read
`OCTODIG_DATABASE_URL` / `DATABASE_URL` from the same settings as the application.
Supply credentials through the local environment or a secret manager. Do not place
connection strings in shell history, source files, issue bodies or logs.

Back up or snapshot a shared database before applying a migration. Apply migrations
once through the release job before starting the new API and worker versions.
Migration 0005 adds nine indexes without changing report data. Index creation can
block writes; plan a maintenance window for an already large database. Do not
automatically downgrade a shared database after a failed deployment.

For a rollback, first stop new research submissions and workers, restore the previous
application image, and check that it supports the current additive schema. Database
restores require an explicit recovery decision; validate backups in a separate
environment and record recovery time and data loss window before release.

## Reproducible PostgreSQL tests

Create a disposable PostgreSQL database named, for example, `octodig_test`. Its user
needs permission to create schemas. Set `OCTODIG_TEST_DATABASE_URL` in the test
process environment, then run `uv run pytest`.

The suite migrates an isolated random schema per test. It tests authenticated API
flows, report persistence, concurrent worker claims, lease expiry while a live
worker retains its lock, killed-process recovery and cancellation during verification.
Cleanup drops only the schema that test created. Tests never call paid providers.

The worker must connect directly to PostgreSQL or through a session-pooling proxy.
Transaction pooling cannot preserve its session advisory lock across commits.
An interrupted DB connection can release that lock even while an external provider
request is still in flight. Persisted reservations bound retry authorization, but
do not prove exactly-once external billing during a network partition.

## Release evidence still needed

Use [VERIFICATION.md](VERIFICATION.md) as the release checklist. Successful tests
do not replace backup restore drills, container startup, multi-host failure tests,
provider billing validation or production monitoring. No production deployment was
performed by these checks.
