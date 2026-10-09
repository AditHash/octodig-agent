# Contributing to OctoDig

OctoDig is currently in the design/documentation stage. Code changes should follow the planned milestones in [PLAN.md](PLAN.md).

## Before proposing a change

1. Read [README.md](README.md), [AGENTS.md](AGENTS.md), and the relevant documents under docs/.
2. Explain which planned milestone, requirement, or observed problem the change addresses.
3. Keep the twelve-section report contract and evidence provenance intact.
4. Prefer small, reviewable pull requests and include tests with implementation changes.
5. Update the relevant Markdown specification if an API, schema, security rule, or architecture assumption changes.

## Coding approach (once implementation begins)

Use typed, testable Python; small FastAPI route handlers; narrow agent tools; and Pydantic output validation. Keep paid provider credentials in local environment variables or secret managers. Do not commit .env files, auth tokens, real customer data, or opaque provider reasoning payloads.

## Reporting issues

Include expected vs actual behavior, affected milestone, minimal reproducible steps, redacted logs, and model/provider version when relevant. Never post secret keys or private personal/company information in an issue.

## Design decisions

Architecture changes should explain trade-offs in evidence quality, latency, cost, reliability, and operational complexity. Agent count alone is not a measure of system capability.

No license has been selected in this documentation pass; avoid assuming a particular open-source license until repository ownership chooses one.
