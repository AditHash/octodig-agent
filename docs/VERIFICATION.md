# Frontend and backend verification

This review verifies the current application foundation, not production readiness.

## Checks executed

- 87 backend tests with the PostgreSQL suite enabled, including HTTP integration
  against both isolated SQLite and PostgreSQL: registration,
  login, authenticated targets and offerings, workspace isolation, idempotent run
  submission, cancellation, worker report persistence, JSON and Markdown retrieval.
- Browser CORS preflight with Authorization, Content-Type and Idempotency-Key.
- Frontend clean install, TypeScript compilation and production Vite build.
- Frontend dependency audit: no reported vulnerabilities at verification time.
- Backend installed dependency audit (`pip-audit --local`): no known vulnerabilities.
- PostgreSQL migration SQL rendering, including a regression check that the
  idempotency column is added only once on a fresh database.
- Python compilation, Ruff correctness checks (`--select F`) and Git whitespace checks.
- Chromium acceptance test against the real frontend, API and offline worker:
  workspace registration, seller approval, target creation, research completion,
  twelve-section evidence display, Markdown download, saved report after reload,
  and workspace profile. Run `cd frontend && npm run test:e2e` after installing
  Chromium with `npx playwright install chromium`. The disposable SQLite fixture
  makes no paid provider calls and does not connect to the operator database.
- Production frontend acceptance through locally installed Nginx: same-origin API
  routing, complete owner workflow, CSP/referrer/MIME headers and oversized request
  rejection. Four browser checks passed across desktop and mobile. WCAG A/AA scans
  reported no violations on sign-in, dashboard and report fixture screens; keyboard
  target creation and horizontal overflow checks passed.
- Actual Docker image builds and an isolated container smoke test passed through
  Docker Desktop's Windows client: external PostgreSQL, migrations, production
  readiness, non-root/read-only API and frontend, worker queue execution, registration,
  approved catalog, partial report persistence, saved history and Markdown export.
  The smoke test disabled provider keys, created no DB container or host ports,
  and removed its own containers, network, random schema and temporary environment.

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

- PostgreSQL integration passed against an isolated PostgreSQL 16 database, including
  all migrations, schema indexes, eight concurrent worker claims, live-worker lease
  fencing, killed-process lock release, cancellation during evidence verification,
  and HTTP ownership/persistence workflows. Multi-host outages and stress testing
  remain release gates.
- Operator-specific HTTPS ingress, image scanning, backup restore drills and
  multi-host deployment remain release gates. Individual hardened images were tested;
  a production deployment was not performed.
- Manual screen-reader review, extended keyboard journeys and representative long
  reports need coverage beyond automated desktop/mobile fixture checks.
- Real OpenAI/Gemini research has not been verified. Configured ceilings are
  implemented below; native grounding tokens and provider billing remain unproven.
  No provider keys or pricing rates were configured in this verification environment.
- Usage aggregation and native-search billing counts need provider-specific
  verification. Missing counts must not be presented as measured spend.
- Quote support is checked through safe retrieval. Source authenticity, conflicting
  claims and independent company identity still require stronger quality gates.
- Worker advisory locking passed real PostgreSQL contention and killed-process tests.
  Network partitions during paid calls and long-duration load remain unverified.
- Frontend renders claims, opportunities, exports, saved history and navigation.
- The GitHub Actions workflow is committed locally; publication remains blocked
  by the active GitHub OAuth credential's missing workflow permission.

No paid provider calls or production deployments were performed by this review.

## Subsequent implementation

The worker now persists budget reservations before spending, subtracts earlier
reservations on recovery, and uses a PostgreSQL session advisory lock to prevent
concurrent paid execution of a leased run. OpenAI requests set an output ceiling,
hosted-tool call ceiling, timeout and zero retries; middleware bounds model calls
and input size and removes filesystem/delegation tools. Deep OpenAI mode now
offers company/market, people/signals, and technology specialists through native
Deep Agents delegation. A single atomic budget is shared by the lead and
delegates, and the report records aggregate model-call usage. The generic default
delegate is explicitly restricted to the same search-only tools and one-call
limit. Gemini sets output and
input ceilings and timeout with retries disabled. Its native-search query cap and
billing equivalence still require provider-specific work.

Source retrieval validates DNS and every redirect, pins the connection IP while
verifying the TLS hostname, and bounds response size and retrieval time. Model
verified labels now require a literal statement match in retrieved visible text.
This checks quote support; it does not establish independent factual truth or
resolve conflicting sources. Unmatched statements are explicitly downgraded.

Lease cancellation/exhaustion and preserved retry reservations have state transition
tests. Real PostgreSQL tests additionally exercise lock contention and process death.
Run `OCTODIG_TEST_DATABASE_URL=... uv run pytest` against a disposable database whose
name ends in `_test`; each test owns a random schema and removes only that schema.
Without this setting, the eight PostgreSQL tests are skipped and SQLite HTTP tests run.

These checks found and corrected migration configuration ignoring the operator's
database URL and nine missing evidence/report indexes (migration 0005).

Deployment adds non-root users, read-only runtime filesystems, private API networking,
explicit migration operation, same-origin routing and allowlisted build contexts.
Production readiness rejects an outdated schema; JWT validation requires expiry;
production CORS origins require HTTPS. DB connection and pool waits are bounded.

Request admission now uses atomic PostgreSQL counters shared across API processes.
Tests cover concurrent limits, failed-password counting, ignored spoofed forwarded
headers, registration throttling, idempotent research retries and scrubbed storage
failure responses. Counter identities are HMAC digests and expired counters are
removed by the worker. Fixed-window boundary bursts and upstream abuse protection
are documented in [SECURITY.md](SECURITY.md).

OpenAI URL-citation annotations and Gemini grounding chunks are now retained as
provider-labelled source appendix records. They are not automatically linked to
claims or treated as verified; public-HTTPS validation and the bounded retrieval
gate remain mandatory before a claim can be supported. Synthetic adapter tests
cover citation extraction, de-duplication, and rejection of insecure or private
destinations. Live-provider citation payload formats still require release-time
verification with configured non-production provider credentials.

The evidence gate also prevents a section from remaining `complete` when no
claim in that section survived source verification. It downgrades those
sections to `insufficient_evidence`, or to `partial` when verified support is
mixed, and records the reason as a visible gap.

The authenticated frontend consumes the run SSE stream with cursor-based
reconnection and refreshes authoritative run status after each event. Workers
emit queue, provider-call, source-verification and report-ready milestones;
the browser workflow verifies the visible ready state before opening the report.
