# OctoDig

**OctoDig** is a planned open-source **agentic business-intelligence and B2B research platform**. The name reflects an octopus gathering information from many directions: multiple specialized agents investigate an account, reconcile evidence, and help a seller understand where a genuine opportunity may exist.

> **Current status: documentation / design phase.** No working OctoDig application is included in this repository yet. Features, architecture, and API routes described here are targets, not implemented capabilities.

OctoDig is the new Python-based successor concept to SalesDig V2. V3 is a **separate repository and new implementation**, not a direct rewrite of the existing Node.js app.

## What it will do

Given a target company and, optionally, its website and the seller's approved offerings, OctoDig will create an evidence-backed account research report, surface uncertainties, suggest qualified sales opportunities, and prepare tailored outreach questions.

### Required report sections

Every completed research attempt must address **all twelve** sections (including an honest "insufficient evidence" result when data is missing):

1. Company overview
2. Business model
3. Products and services
4. Market position
5. Leadership and decision-makers
6. Recent developments
7. Growth and hiring signals
8. Technology landscape
9. Business challenges and priorities
10. Sales opportunities
11. Outreach preparation
12. Sources and evidence

See [the report contract](docs/REPORT_CONTRACT.md) for the evidence model and section statuses.

## Architecture at a glance

~~~text
Client / CLI
    |
    v
FastAPI: request validation, research jobs, status, SSE
    |
    v
LangGraph: durable and bounded research lifecycle
    |
    +-- Deep Agents lead researcher: planning, delegation, gap analysis
    |       +-- Company & market research
    |       +-- Leadership, news & hiring research
    |       +-- Technology research
    |
    +-- Evidence normalization + verification
    +-- Seller-specific opportunity analysis
    +-- Coverage and quality gates
    +-- Report assembly
    |
    v
Persistence: PostgreSQL, pgvector, reports, run events
~~~

This is **hybrid agentic orchestration**: agents choose research directions and delegate subtasks; application code still enforces identity, evidence schemas, permissions, budget limits, and report completeness. Not every box is a separate agent.

## Intended stack

- Python, FastAPI, Pydantic
- LangChain, LangGraph, Deep Agents
- Configurable OpenAI / Gemini integrations
- PostgreSQL and pgvector (later milestone)
- LangSmith for optional tracing and evaluations
- Server-Sent Events for progress streaming

## Documentation

- [PLAN.md](PLAN.md) — staged implementation and acceptance criteria
- [AGENTS.md](AGENTS.md) — instructions for contributors and coding agents
- [Product requirements](docs/PRD.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Research output contract](docs/REPORT_CONTRACT.md)
- [API specification](docs/API.md)
- [Security and evidence policy](docs/SECURITY.md)
- [Evaluation plan](docs/EVALUATION.md)
- [Contributing](CONTRIBUTING.md)

## Guiding principles

1. **Evidence first:** sources back factual claims; inferences and hypotheses are labeled.
2. **Twelve-section guarantee:** coverage is checked in code; missing fields are not invented.
3. **Seller relevance:** match opportunities to actual approved offerings.
4. **Agent autonomy with guardrails:** no unbounded loops, secret exposure, unrestricted fetches, or silent writes.
5. **Observable research:** track latency, sources, token usage, estimated spend, and failures.
6. **Ship incrementally:** a reliable CLI research milestone precedes production APIs.

## Status and getting started

Start with [PLAN.md](PLAN.md). There are currently no installation or run commands because the implementation has not been added. Never commit credentials or customer-sensitive datasets.
