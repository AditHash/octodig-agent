# Proposed FastAPI Contract

**Status:** future design. **None of these endpoints are implemented yet.**

Prefix: /api/v1. OpenAPI paths, authentication strategy, and database schema will be finalized during Phase 3.

## Research lifecycle

| Method | Path | Expected behavior |
|---|---|---|
| POST | /research | Validate company and seller context; create durable run |
| GET | /research/{run_id} | Status, progress summary, timestamps, gaps |
| GET | /research/{run_id}/events | SSE progress and report-token stream |
| GET | /research/{run_id}/report | Validated JSON report or pending/error state |
| POST | /research/{run_id}/cancel | Request cancellation of active work |
| GET | /health | Liveness/health indication |

Later:
- POST /chat — grounded questions over saved research with citations
- GET /companies/{company_id}/history — stored report revisions

## Start research — illustrative request

~~~json
{
  "company_name": "Example Company",
  "website": "https://example.com",
  "mode": "standard",
  "seller_offerings": [
    {
      "id": "offering_ai_support",
      "name": "Support automation",
      "description": "Automate supported customer support workflows"
    }
  ]
}
~~~

Return HTTP 202 with generated run ID, status and URLs for status/events/report. The API must not hold the initiating HTTP request open until full research completes.

## Run status

Suggested states: **queued**, **running**, **completed**, **completed_partial**, **failed**, **cancel_requested**, **cancelled**.

Partial completion means all twelve report keys are represented but some have incomplete/no evidence. It is not the same as success with validated claims in every category.

## SSE event protocol

Each event should have stable event ID, timestamp, run ID, type and JSON data. Planned events:

- run.started
- research.planned
- agent.started
- source.discovered
- claim.recorded
- research.gap_detected
- research.follow_up
- report.delta
- report.ready
- run.completed
- run.failed
- run.cancelled

Never expose internal model chain-of-thought, raw credentials, or encrypted reasoning chunks over SSE. Streaming is for user-visible progress and content, not a substitute for durable checkpoints. Support reconnect through Last-Event-ID or an explicit cursor.

## Safety and multi-tenancy

Authorize workspace ownership on **every** run, event, artifact and company lookup. Use idempotency keys for job creation where possible, validate URLs and seller payload sizes, apply rate and budget limits, and scrub source contents before logging.

## Final report

GET /research/{run_id}/report returns a validated versioned envelope per [REPORT_CONTRACT.md](REPORT_CONTRACT.md). Clients render from structured sections and evidence IDs rather than scraping markdown to recover citations.

## Error model

Use consistent error codes such as invalid_company, ambiguous_identity, budget_exceeded, source_unavailable, provider_failure, validation_failed, unauthorized, and not_found. Preserve partial evidence where safe and clearly state whether a report is retrievable.
