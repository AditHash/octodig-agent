# OctoDig

**OctoDig** is a planned open-source **agentic business-intelligence and B2B research platform**. The name reflects an octopus gathering information from many directions: multiple specialized agents investigate an account, reconcile evidence, and help a seller understand where a genuine opportunity may exist.

> **Current status: hosted application foundation in progress.** The repository now contains a FastAPI API, React workspace shell, PostgreSQL-backed research queue, and Docker images for frontend/API/worker. Provider research orchestration, complete seller knowledge, reports, chat, and exports are being implemented incrementally. The `examples/` directory remains educational only.

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
Initially: LangChain tools + Deep Agents (built on LangGraph)
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
Pydantic report validation and local artifacts

Later: FastAPI + durable jobs + optional custom LangGraph
       workflow + PostgreSQL/pgvector + SSE
~~~

This is **hybrid agentic orchestration**: agents choose research directions and delegate subtasks; application code still enforces identity, evidence schemas, permissions, budget limits, and report completeness. Not every box is a separate agent.

## Intended stack

- **Start now:** Python, LangChain, Deep Agents, Pydantic
- **Already underneath:** LangGraph runtime, used internally by agents
- **Later as needed:** FastAPI and an explicit custom LangGraph workflow
- **Provider-agnostic models:** OpenAI GPT and Google Gemini via LangChain `init_chat_model` (provider-native search remains separate)
- Benchmark both providers before choosing a default model or specialist assignments
- PostgreSQL and pgvector (later milestone)
- LangSmith for optional tracing and evaluations
- Server-Sent Events for progress streaming

## Try the learning examples

These are **small experiments**, not a full research product. Examples 01–03 make OpenAI API requests; example 05 can call **both** OpenAI and Gemini. Paid calls may incur charges, with additional web-search fees for examples 02–03.

~~~bash
uv sync
cp .env.example .env  # fill in OPENAI_API_KEY locally; never commit .env
uv run python examples/01_langchain_tools.py
uv run python examples/02_deep_research.py "Microsoft"
uv run python examples/03_subagents.py "Microsoft"
uv run python examples/04_validate_report.py
uv run python examples/05_compare_providers.py --provider both
uv run pytest
~~~

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`. See [examples/README.md](examples/README.md) for what each example demonstrates and safety limits.

### Why all three frameworks?

**LangChain** supplies models, tool interfaces and baseline agents. **Deep Agents** supplies a research harness, planning/context management and optional subagent delegation; it already runs on the **LangGraph runtime**. We will **not** write our own `StateGraph` in V0 solely for appearances. Add a custom outer LangGraph when explicit multi-stage state transitions, deterministic recovery/branching, and checkpoint boundaries are genuinely needed. Read [framework choices](docs/FRAMEWORK_CHOICES.md).

## Latest architecture decisions

- **GPT and Gemini:** keep prompts, agent logic, report schema and reusable tools provider-neutral. Use a provider adapter for authentication, capabilities, native search, citation metadata, token reporting and costs. Compare identical-input baselines **separately** from native-search end-to-end benchmarks.
- **A2A:** do **not** add Agent2Agent in V0/V1. Native Deep Agents subagents work inside the Python service even when using different model providers. Consider A2A only after an independently deployable agent or cross-framework integration is useful.
- **MCP:** optional tool connectivity; not the same concern as A2A agent-to-agent communication.

Read [MODEL_BENCHMARK.md](MODEL_BENCHMARK.md) and [docs/A2A_PROTOCOL.md](docs/A2A_PROTOCOL.md).

## Documentation

- [PLAN.md](PLAN.md) — staged implementation and acceptance criteria
- [AGENTS.md](AGENTS.md) — instructions for contributors and coding agents
- [Product requirements](docs/PRD.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Framework choices](docs/FRAMEWORK_CHOICES.md)
- [Runnable examples](examples/README.md)
- [Research output contract](docs/REPORT_CONTRACT.md)
- [API specification](docs/API.md)
- [Security and evidence policy](docs/SECURITY.md)
- [Evaluation plan](docs/EVALUATION.md)
- [GPT vs Gemini benchmark plan](MODEL_BENCHMARK.md)
- [A2A protocol adoption decision](docs/A2A_PROTOCOL.md)
- [Contributing](CONTRIBUTING.md)

## Guiding principles

1. **Evidence first:** sources back factual claims; inferences and hypotheses are labeled.
2. **Twelve-section guarantee:** coverage is checked in code; missing fields are not invented.
3. **Seller relevance:** match opportunities to actual approved offerings.
4. **Agent autonomy with guardrails:** no unbounded loops, secret exposure, unrestricted fetches, or silent writes.
5. **Observable research:** track latency, sources, token usage, estimated spend, and failures.
6. **Ship incrementally:** a reliable CLI research milestone precedes production APIs.

## Status and getting started

Start with [PLAN.md](PLAN.md), then run the [examples](examples/README.md). The examples do not prove the twelve-section report is evidence-verified or production-ready. Never commit credentials or customer-sensitive datasets.

## Application development

OctoDig uses an external PostgreSQL database with the `pgvector` extension; the
repository intentionally does not ship a database container. Copy `.env.example`
to `.env`, set a real `DATABASE_URL` and `JWT_SECRET`, then apply migrations and
start the API, worker, and frontend:

~~~bash
uv sync
uv run alembic upgrade head
uv run uvicorn octodig.api:app --reload
uv run python -m octodig.worker
cd frontend && npm install && npm run dev
~~~

For Docker deployment, provide the same external database values in `.env` and
run `docker compose up --build`. This starts only frontend, API, and worker.
