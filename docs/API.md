# FastAPI Contract

**Status:** implemented hosted API contract. Prefix: `/api/v1`.

All application endpoints except health checks require a bearer access token and
enforce the caller's workspace boundary.

## Research lifecycle

| Method | Path | Expected behavior |
|---|---|---|
| POST | /targets/{target_id}/research | Validate request; create/reuse a durable run |
| GET | /runs | Workspace-scoped saved run history |
| GET | /runs/{run_id} | Current status, provider, mode, attempt count and error code |
| GET | /runs/{run_id}/events | Reconnectable SSE progress stream |
| GET | /runs/{run_id}/report | Validated report JSON after persistence |
| GET | /runs/{run_id}/report.md | Rendered Markdown after persistence |
| POST | /runs/{run_id}/cancel | Cancel queued work or request active cancellation |
| GET | /health/live | Process liveness |
| GET | /health/ready | Database and production-migration readiness |

Later:
- POST /chat — grounded questions over saved research with citations
- GET /companies/{company_id}/history — stored report revisions

## Start research — illustrative request

`GET /api/v1/runs?limit=50&offset=0` returns workspace-scoped saved run history.
`GET /api/v1/me` returns the authenticated user's workspace profile and role.
The frontend restores history after reload and can reopen status and stored reports.

The hosted endpoint is `POST /api/v1/targets/{target_id}/research`. Send a
client-generated `Idempotency-Key` header for every user action that may be
retried. Reusing the key with identical input returns the original run; reuse
with different input returns HTTP 409 and never starts another paid run.

~~~json
{
  "provider": "openai",
  "mode": "standard",
  "max_cost_usd": "0.0500"
}
~~~

Return HTTP 202 with generated run ID, status and URLs for status/events/report. The API must not hold the initiating HTTP request open until full research completes.

## Run status

States: **queued**, **researching**, **normalizing**, **matching**,
**rendering**, **completed**, **completed_partial**, **failed**,
**cancel_requested**, **cancelled**, and **budget_exceeded**.

Partial completion means all twelve report keys are represented but some have incomplete/no evidence. It is not the same as success with validated claims in every category.

## SSE event protocol

Each event has a stable ID, type and JSON metadata. The stream accepts the
`after` cursor to resume after a delivered event. The frontend uses `fetch` with
the bearer token because browser `EventSource` cannot attach an Authorization
header. If a reverse proxy closes a stream, the frontend reconnects with that
cursor and refreshes run status from the durable API.

Current events include:

- run.queued
- run.started
- run.reclaimed
- budget.reserved
- research.provider_call_started
- research.evidence_verification_started
- report.ready
- run.partial
- run.failed
- run.cancel_requested
- run.cancelled

Never expose internal model chain-of-thought, raw credentials, or encrypted reasoning chunks over SSE. Streaming is for user-visible progress, not a substitute for durable checkpoints.

## Safety and multi-tenancy

Authorize workspace ownership on **every** run, event, artifact and company lookup. Use idempotency keys for job creation where possible, validate URLs and seller payload sizes, apply rate and budget limits, and scrub source contents before logging.

## Final report

`GET /runs/{run_id}/report` returns a validated versioned envelope per
[REPORT_CONTRACT.md](REPORT_CONTRACT.md). Clients render structured sections and
evidence IDs rather than scraping Markdown to recover citations.

## Error model

Use consistent error codes such as invalid_company, ambiguous_identity, budget_exceeded, source_unavailable, provider_failure, validation_failed, unauthorized, and not_found. Preserve partial evidence where safe and clearly state whether a report is retrievable.
