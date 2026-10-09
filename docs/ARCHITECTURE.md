# OctoDig System Architecture (Proposed)

**Design:** hybrid agentic intelligence with deterministic control boundaries.

## Main components

~~~text
Caller / future UI
      |
      v
FastAPI API: validation, auth, run orchestration, progress SSE
      |
      v
Durable job executor + LangGraph workflow
      |
      +--> Identity resolution / research planning
      |
      +--> Parallel evidence gathering (when useful)
      |      +-- Company & market specialist
      |      +-- People, news & hiring specialist
      |      +-- Technology specialist
      |
      +--> Evidence normalization, deduplication, verification
      |
      +--> Opportunity specialist + seller offerings catalog
      |
      +--> Coverage validator ---- missing critical evidence?
      |                                  |
      |                         bounded follow-up task
      |
      +--> Report assembler + final schema validation
      |
      v
PostgreSQL (runs, event journal, sources, facts, reports)
pgvector (optional evidence retrieval)
Object/artifact storage (optional large reports)
~~~

## Separation of responsibilities

**LangGraph:** explicit state transitions, dependencies, bounded loops, retry boundaries, checkpointing where configured, and deterministic completion gates.

**Deep Agents:** open-ended planning, tool selection, targeted web research, scratch/workspace management, and delegation to specialist tasks.

**FastAPI:** routes, auth/workspace checks, schema validation, job lifecycle, SSE transport, cancellation and idempotency.

**Application services:** source validation, evidence normalization, claim linking, report validation, budget enforcement, database writes.

The lead agent may choose additional research, but cannot skip required output coverage or bypass budgets. Parallelism is used only for independent tasks, not as a requirement to run every specialist every time.

## Conceptual specialists

- **Company/market:** company identity, overview, customers, business model, offerings and competitors.
- **People/signals:** leadership, new announcements, expansions, hiring and dated buying signals.
- **Technology:** publicly stated infrastructure, tools, integrations and AI/cloud initiatives.
- **Verification (model-assisted + code):** compare claims to available evidence, detect contradictions and unsupported assertions.
- **Opportunity analyst:** map validated findings and hypothesized needs to approved seller offerings.
- **Lead:** plan work, delegate, assess research gaps, request bounded follow-up and consolidate results.

These responsibilities may be grouped or split in implementation. Do not equate "six responsibilities" with "six LLMs".

## Suggested graph

~~~text
Resolve company -> Plan -> Gather (parallel) -> Normalize/verify
                                                 |
                                                 v
                                        Analyze opportunities
                                                 |
                                                 v
                                       Check 12-section coverage
                                        /                \
                             gaps within budget       good or budget exhausted
                                    |                        |
                              Targeted research         Assemble report
                                    |                        |
                                   verify               Persist + finish
~~~

## Core data contracts (proposed)

- **ResearchRun:** run_id, workspace_id, target, mode, timestamps, status, limits, spend measurements.
- **Source:** source_id, canonical URL, publisher, published_at?, retrieved_at, content type, fetch status.
- **Claim:** claim_id, text, section_id, classification, cited source IDs, verification status, conflicts.
- **Opportunity:** seller offering ID?, business hypothesis, supporting claim IDs, benefit, priority and questions.
- **Report:** report schema version, all twelve section records, source appendix, gaps and generation metadata.

Research agents hand off these objects, not entire private conversation histories. Use stable IDs so every opportunity is inspectable from its source claims.

## Execution model

Early CLI POC: in-process execution and local JSON/Markdown artifacts.

Later API: create a durable run, enqueue worker task, persist checkpoint + events, stream progress through SSE, retrieve completed report independently of the initiating HTTP connection. A disconnected SSE client should **not** cancel underlying research.

## Evidence handling

- Search result summaries are leads, not sufficient verification on their own.
- Preserve source URLs and timestamps; prefer primary evidence.
- If a cited source does not substantiate a claim, downgrade or reject the claim.
- Treat model confidence scores as assessments, never independent evidence.
- Keep complete/partial/not-found statuses separate from epistemic claim labels.

## Failure and budget policy

Model/provider outages, blocked sources, contradictory evidence, and exhausted budgets are first-class run outcomes. Save partial findings and report incompleteness rather than generating unsupported replacements. Set per-run limits on tool calls, concurrency, model spend, token estimates, wall-clock time, and follow-up cycles.

## Non-negotiable boundaries

No user secrets in agent memory; no unrestricted network tools; no external side effects without authorized application services; no uncontrolled prompt injection from retrieved pages.

See [SECURITY.md](SECURITY.md), [REPORT_CONTRACT.md](REPORT_CONTRACT.md), and [API.md](API.md).
