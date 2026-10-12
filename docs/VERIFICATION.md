# Frontend and backend verification

This review verifies the current application foundation, not production readiness.

## Checks executed

- 47 backend tests, including HTTP integration against isolated SQLite: registration,
  login, authenticated targets and offerings, workspace isolation, idempotent run
  submission, cancellation, worker report persistence, JSON and Markdown retrieval.
- Browser CORS preflight with Authorization, Content-Type and Idempotency-Key.
- Frontend clean install, TypeScript compilation and production Vite build.
- Frontend dependency audit: no reported vulnerabilities at verification time.
- Backend installed dependency audit (`pip-audit --local`): no known vulnerabilities.
- PostgreSQL migration SQL rendering, including a regression check that the
  idempotency column is added only once on a fresh database.
- Python compilation, Ruff correctness checks (`--select F`) and Git whitespace checks.

## Defects corrected

- Documented OCTODIG_* environment configuration was not loaded.
- CORS blocked the frontend's Idempotency-Key header.
- The initial migration imported evolving runtime models, duplicating columns
  introduced by subsequent revisions. Its PostgreSQL schema is now frozen.
- Research submission returned fewer fields than the frontend expected.
- The idempotency concurrency handler did not cover the initial database flush;
  equivalent decimal budgets could also incorrectly conflict.
- Docker builds ignored lockfiles. Both images now use locked installs.
- Production JWT secrets now require at least 32 bytes; blank optional values
  from the example environment file are treated as unconfigured.

## Remaining production gates

- PostgreSQL migration execution, concurrency, lease recovery and cancellation
  races require tests against a real PostgreSQL instance. SQLite cannot prove them.
- Docker startup was not tested: Docker Desktop is unavailable to this WSL distro.
- Browser interaction, responsive layouts and accessibility require browser tests;
  a successful production build does not prove those behaviors.
- Real OpenAI/Gemini research has not been verified in this review. Pricing
  reservations currently do not enforce actual token/search/model-call limits.
- Usage aggregation and native-search billing counts need provider-specific
  verification. Missing counts must not be presented as measured spend.
- Source citation provenance, reachability, claim support and approved-offering
  matching need stronger deterministic validation before facts are called verified.
- Worker recovery needs fencing/heartbeats to prevent a slow worker and a worker
  reclaiming its expired lease from both performing paid work.
- Frontend still needs report claim/opportunity rendering, persistent run history,
  reconnect after page reload, and complete navigation screens.
- The GitHub Actions workflow is committed locally; publication remains blocked
  by the active GitHub OAuth credential's missing workflow permission.

No paid provider calls or production deployments were performed by this review.
