# OctoDig System Architecture (Proposed)

**Design:** hybrid agentic intelligence with deterministic control boundaries.

## Framework strategy: start simple

**Phase 1:** use LangChain for model/tool/agent interfaces and **Deep Agents** for the lead researcher, web research, context management, and optional declarative subagents. Deep Agents is **already implemented using LangChain agents on LangGraph's runtime**. We do **not** need to author a separate `StateGraph` to use it.

**Phase 2+ (conditional):** introduce an explicit outer LangGraph workflow **only if** concrete needs arise for deterministic cross-stage transitions, persistent checkpoints, independently retryable verification, bounded branching, or interruption/resumption. A custom graph should not duplicate the work of the Deep Agents harness. Application code must enforce reporting and security contracts in either design.

See [FRAMEWORK_CHOICES.md](FRAMEWORK_CHOICES.md) and [examples/README.md](../examples/README.md) for runnable building blocks.

## Provider-agnostic inference

Model selection and research orchestration are separate concerns. LangChain's `init_chat_model` can select OpenAI GPT or Google Gemini via a provider-prefixed model ID. The research and final report contracts should not branch on model vendor. Provider adapters handle credentials, native/third-party search capabilities, citation grounding, token-usage metadata and cost accounting. Mixed-model specialists are possible but **not automatic**, and should be decided after measured comparison.

~~~text
Company research request
          |
          v
Shared research prompts + report contract
          |
          v
Deep Agents + LangChain tool interfaces
          |
          v
Configured model (GPT / Gemini)
          |
          v
Provider-specific search / citation adapter (when needed)
          |
          v
Evidence store + deterministic twelve-section validation
~~~

Use separate benchmarks for identical provided evidence, a shared search backend, and provider-native web search. See [../MODEL_BENCHMARK.md](../MODEL_BENCHMARK.md).

## A2A is an extension, not a prerequisite

In-process specialist tasks use Deep Agents' built-in delegation. Using GPT and Gemini in the **same Python service** requires no Agent2Agent (A2A) protocol. A2A becomes interesting when one specialist is independently deployed, owned, permissioned or implemented in another framework. When that need is established, add an adapter translating internal task/result types to the protocol's agent discovery, remote tasks, and artifacts. Do not expose an A2A server by default. See [A2A_PROTOCOL.md](A2A_PROTOCOL.md).

## Main components

~~~text
Caller / future UI
      |
      v
FastAPI API: validation, auth, run orchestration, progress SSE
      |
      v
Deep Agents + LangChain tools (initial)
      |
      +--> optional custom LangGraph stages (later, if needed)
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

**LangGraph:** the runtime already used by Deep Agents and LangChain agents. A **custom** LangGraph graph is a later option for explicit state transitions, independently retryable stages, bounded branching, and checkpointing where configured.

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

## Suggested later-stage graph (not V0)

This diagram illustrates when an **outer** graph might become valuable; it is not an implementation requirement for the first agent.

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
