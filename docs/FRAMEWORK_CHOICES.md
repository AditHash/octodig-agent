# Why LangChain + Deep Agents First, Instead of Writing LangGraph Immediately?

**Decision:** OctoDig V0 builds on LangChain + Deep Agents. We may introduce a **custom outer LangGraph workflow later** when evidence, reliability and operational requirements justify its complexity. This is not a choice between mutually exclusive libraries.

## How the layers fit

| Layer | Responsibility in OctoDig | When |
|---|---|---|
| **LangChain** | Model integrations, tools, agent interfaces and middleware | From first experiment |
| **Deep Agents** | Deep research harness: context management, tool use, optional planning/delegation, specialized subagents | From first experiment |
| **LangGraph runtime** | The underlying graph execution, streaming and state mechanisms used by these agents | Already there indirectly |
| **Custom LangGraph StateGraph** | Application-specific, independently retryable stages and deterministic branching | Only when we have a clear requirement |
| **FastAPI/application code** | HTTP API, authorization, validation, persistence, budgets, deterministic report coverage | Introduce incrementally |

Deep Agents' `create_deep_agent(...)` builds an agent that runs on LangGraph via LangChain's agent foundation. We do **not** need to assemble a `StateGraph` merely to get a functioning Deep Agent.

## Examples in this repository

- [01_langchain_tools.py](../examples/01_langchain_tools.py) — simple LangChain agent with a local, bounded tool.
- [02_deep_research.py](../examples/02_deep_research.py) — Deep Agent with OpenAI hosted web search; a **research experiment**, not verified production output.
- [03_subagents.py](../examples/03_subagents.py) — Deep Agents lead with specialized subagents using `subagents=`.
- [04_validate_report.py](../examples/04_validate_report.py) — no-LLM Pydantic validation for the mandatory twelve-section minimum.

Examples use the **same underlying runtime** without writing a manual graph. The models may or may not delegate to a subagent on a given run; delegation is a model choice.

## When *not* to add a custom graph

- One-off research questions and a single main agent.
- Basic subagent delegation handled by Deep Agents' built-in `task` capability.
- A basic CLI that reads arguments, invokes a researcher and validates the output in Python.
- "We need to look agentic" or "LangGraph must be in the stack" with no execution need.

## When to consider a custom graph

- Enforced, separately checkpointed **identity resolution → evidence collection → verification → opportunities → final report** stages.
- Independent retries for failed stages without paying to repeat successful research.
- Conditional re-research based on a deterministic twelve-section coverage gate.
- Human approval, pause/resume, or persisted multi-day asynchronous workflow state.
- Predictable execution, budgets and cancellation across multiple worker processes.

Before adding one, write an ADR explaining: the missing requirement, a simpler alternative, state schema, retry semantics, persistence strategy, evaluation metric and rollback strategy.

## Evidence is still enforced outside the agent

An agent saying "verified" is not proof. Store normalized claim/source records and validate their provenance. A section may be `insufficient_evidence`; it may not be omitted. The deterministic contract is in [REPORT_CONTRACT.md](REPORT_CONTRACT.md).

## Source documentation

- [Deep Agents Python quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep Agents subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

Review provider/tool support and SDK versions before shipping; these APIs evolve.
