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
do not replace backup restore drills, multi-host failure tests,
provider billing validation or production monitoring. No production deployment was
performed by these checks.

## Hosted deployment

Compose builds non-root API/worker and Nginx containers with read-only filesystems,
temporary scratch space, dropped capabilities and no privilege escalation. Database
credentials stay in the external environment. The API is reachable only inside the
Compose network. The frontend binds to `127.0.0.1:8080`; put an HTTPS ingress in
front of that address and configure the public HTTPS origin in
`OCTODIG_CORS_ORIGINS`. Set a random JWT secret of at least 32 bytes.

Request-limit defaults are 60 login attempts per minute per client/account, 10
registrations per hour per client and 20 new research submissions per minute per
workspace. Set `OCTODIG_AUTH_LOGIN_PER_MINUTE`, `OCTODIG_AUTH_REGISTER_PER_HOUR`
and `OCTODIG_RESEARCH_SUBMISSIONS_PER_MINUTE` for the deployment. Monitor 429s and
configure upstream abuse controls. A JWT-key rotation also resets opaque quota
identities and invalidates existing access tokens. Migration 0006 creates the quota
table; apply it before running this API/worker version.

After a reviewed backup and maintenance decision, apply the schema with
`docker compose --profile operations run --rm migrate`, then start API, worker and
frontend with `docker compose up -d --build`. Migration is a separate operation;
ordinary startup does not change the database schema. These are deployment
instructions, not commands already run against production.

Production readiness checks both database connectivity and the expected Alembic
revision. Liveness only reports that the API process responds. Monitor readiness,
restart counts, queue age, failed/reclaimed runs and reserved spend. A running
process or green frontend health check does not establish worker progress.

Application logs are newline-delimited JSON. API entries contain only method,
path (without query string), status, and duration; worker entries contain a run
ID, attempt, and scrubbed error code where applicable. Prompt text, provider
responses, authorization headers, request bodies, connection strings, and
exception messages are deliberately excluded.

The browser calls `/api` on the frontend origin. Nginx forwards those requests to
the API, limits request bodies, disables response buffering for events and sends
CSP, frame, MIME and referrer headers. Logs include method, path, status and latency,
excluding query strings and authorization headers. Access logs must still be
protected because paths can include opaque account/run identifiers. HTTPS ingress
owns certificates and HSTS. Trust forwarded client addresses only from explicitly
configured ingress IPs; never enable blanket proxy trust on a public API listener.

To exercise the built frontend through locally installed Nginx, build it with
`VITE_API_URL='' npm run build` in `frontend`, then set `OCTODIG_TEST_NGINX_BIN`
to that executable (and `OCTODIG_TEST_NGINX_MIME` if its MIME file is outside
`/etc/nginx/mime.types`) before running `npm run test:e2e`. This runs the committed
proxy configuration on loopback with offline API/worker fixtures, without Docker.

## Actual image smoke test

Build `octodig-api:verification` from the repository root and
`octodig-frontend:verification` from `frontend`. Set `OCTODIG_TEST_DATABASE_URL`
to a local disposable PostgreSQL database and `OCTODIG_CONTAINER_TEST_DATABASE_URL`
to the same database using a host the Docker engine can reach. Both names must
end in `_test`. Run `uv run python tests/container_smoke.py`; optionally set
`OCTODIG_TEST_DOCKER_BIN` when Docker's executable is outside PATH.

The harness verifies ownership of its random schema before applying migrations,
creates its own isolated Docker network, runs non-root API/worker/frontend with
read-only filesystems and dropped capabilities, and exercises authenticated
registration, catalog, queue, worker report persistence, history and export through
the actual frontend proxy. It uses an unconfigured-provider partial result, without
paid requests. It removes only its own containers, network, schema and temporary
environment file. It does not start a PostgreSQL container or publish host ports.

Base images are pinned to verified registry digests and uv to 0.12.21. Update these
pins with dependency review and image scanning before each release. The Nginx stable
version was checked against the [official image manifest](https://github.com/docker-library/official-images/blob/master/library/nginx).
