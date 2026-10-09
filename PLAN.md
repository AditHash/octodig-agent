# OctoDig Implementation Plan

**Status:** proposed roadmap  
**Goal:** move from a documented concept to a dependable, evidence-backed hybrid multi-agent research platform without losing the twelve report sections already established in SalesDig V2.

## What counts as success

A research run:
- Accepts company name and optionally canonical website, geography, and seller offerings.
- Resolves the target company or flags ambiguous identity.
- Covers all twelve mandatory report sections with meaningful section-level statuses.
- Keeps verified observations, inferred needs, and sales hypotheses separate.
- Links material claims and recommendations to recorded evidence.
- Produces validated JSON and readable Markdown.
- Reports run status, sources, token use, latency, and research gaps.
- Remains bounded by per-run budgets and safeguards.

## Phase 0 — Specification and evaluation fixtures

- [x] Establish project identity and first documentation.
- [x] Freeze the twelve-section minimum output contract.
- [ ] Choose 3–5 representative company test fixtures, including a sparse-information company and an ambiguous name.
- [ ] Create a test seller-offering catalog and expected evidence examples.
- [ ] Choose initial API providers/models based on tool support, quality, and measured cost, not price alone.

**Exit criteria:** shared schemas and reproducible quality checks; no assumptions about an already implemented backend.

## Phase 1 — Runnable CLI research POC

- [ ] Initialize a Python project with uv and environment-based settings.
- [ ] Create a single Deep Agent with a narrowly scoped research prompt and approved search tools.
- [ ] Accept company name, optional official website, seller offerings, and research depth.
- [ ] Capture provider citation annotations and original source metadata.
- [ ] Store research findings separately from the final generated narrative.
- [ ] Validate twelve section placeholders and explicit missing-data statuses.
- [ ] Stream progress/text locally and save Markdown + structured JSON.
- [ ] Record timing, tool actions, input/output/reasoning tokens and estimated provider cost.

**Exit criteria:** repeatable end-to-end CLI run with real source URLs, sensible factuality safeguards, and no fabricated unknown fields.

## Phase 2 — Hybrid multi-agent intelligence

- [ ] Introduce LangGraph's explicit workflow state and bounded transitions.
- [ ] Add specialist research tasks for company/market, people/signals, and technology.
- [ ] Permit parallel independent research; merge normalized findings via a shared evidence store.
- [ ] Add verification of source reachability, relevance, recency, contradictions, and claim support.
- [ ] Add opportunity analysis consuming verified findings and approved seller offerings.
- [ ] Let a lead agent request targeted follow-up research for important gaps, subject to budgets.
- [ ] Add deterministic coverage checks; never require an agent to fabricate a field.
- [ ] Compare single-agent versus hybrid execution on the same fixtures.

**Exit criteria:** comparable or better evidence and opportunity quality than Phase 1, with inspectable delegation and controlled costs.

## Phase 3 — FastAPI and durable jobs

- [ ] Expose validated research start, status, event-stream and report endpoints.
- [ ] Separate long-running jobs from request processes using a durable worker mechanism.
- [ ] Persist run events; support SSE reconnect using event IDs/cursors.
- [ ] Implement cancellation, bounded retries, timeout handling, idempotency, and explicit failure states.
- [ ] Add authentication and workspace-level authorization before multi-user deployment.
- [ ] Expose health endpoints and structured operational logs.

**Exit criteria:** clients can start research, reconnect to progress, and retrieve a final result after leaving the page.

## Phase 4 — Persistence and conversational intelligence

- [ ] Store companies, runs, evidence, sources, sections, and offering catalogs in PostgreSQL.
- [ ] Add LangGraph checkpointers for supported recovery and resumability.
- [ ] Add pgvector only where retrieval evaluations show a clear need.
- [ ] Support cited follow-up questions over a stored company's evidence.
- [ ] Track report version, source access date, and research freshness.

**Exit criteria:** research remains durable, auditable, and reproducible enough for later comparison.

## Phase 5 — Product hardening

- [ ] Red-team prompt injection and SSRF protection in all source-fetch tools.
- [ ] Add evidence-based factuality and opportunity-relevance evaluation suites.
- [ ] Track per-company cost, model calls, search-tool charges, search repetition, and p50/p95 latency.
- [ ] Benchmark standard vs deep modes and document trade-offs.
- [ ] Add CI, security checks, deployment templates, monitoring, and backup procedures.
- [ ] Evaluate a web UI and integrations only after the core contract is stable.

## Research modes

| Mode | Requirements | Research policy |
|---|---|---|
| Standard | All twelve sections | Focused research, smaller limits, few follow-ups |
| Deep | Same twelve sections | Additional targeted searches, corroboration, specialist delegation |

Both modes return the same schema; budget and depth vary. A recursion limit alone is **not** a monetary budget.

## Non-goals for early milestones

No autonomous outreach, mass scraping, CRM writes, guarantees of private tech-stack access, unfounded revenue estimates, or unrestricted agent browser/network capabilities.

## Release discipline

Prefer small reversible changes with tests. Update this plan and related contracts when design decisions change. Keep the existing SalesDig V2 system outside this repository.
