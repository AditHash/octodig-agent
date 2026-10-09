# Agent2Agent (A2A) Adoption Decision

**Decision date:** 2026-10-09  
**Decision:** **Defer A2A from OctoDig V0/V1.** Treat it as an **optional later experiment**, not a committed infrastructure dependency.

## Why?

OctoDig's first objective is reliable research, evidence integrity, twelve-section reporting and measured GPT/Gemini performance. Deep Agents' native `subagents=` mechanism already delegates to specialists inside one service. Having a GPT-based specialist and a Gemini-based specialist **does not by itself require A2A**; both can run in the same Python runtime.

A2A addresses a **different boundary**: communication, discovery and task exchange between independently deployed agent services, potentially written using different frameworks, languages, or organizations. It introduces capabilities such as Agent Cards, remote tasks, messages, artifacts and task progress/streaming. These are useful **only** when there is a real remote-agent relationship.

## Distinguish the concepts

| Technology | Purpose | First milestone |
|---|---|---|
| LangChain | Common model/tool interfaces | Use |
| Deep Agents | Planning, research and internal delegation | Use |
| LangGraph | Agent runtime; optional explicit outer workflow later | No custom graph in V0 |
| MCP | Connecting agents to external tools/services | Optional if an appropriate tool needs it |
| A2A | Agent-to-agent protocol across service boundaries | **Defer** |

MCP does not replace A2A, and A2A is not needed for ordinary tool use or in-process subagents.

## Current topology

~~~text
OctoDig Python process
   Lead Deep Agent
      |-- Company researcher (configured GPT or Gemini)
      |-- People & signals researcher (configured GPT or Gemini)
      |-- Technology researcher (configured GPT or Gemini)
   Shared source/claim schema and deterministic validation
~~~

No agent network, A2A server or A2A SDK should be installed for this design.

## Candidate future experiment (not implemented)

If there is a reason to run one specialist independently, isolate **one** agent as an A2A service and retain the lead researcher as an A2A client.

~~~text
OctoDig lead in Python (A2A client)
           |
       authenticated A2A
           |
   Remote specialist agent service
     - independently deployed
     - may use a different framework
     - returns task artifacts and source provenance
~~~

Possible exercise: OctoDig lead using Deep Agents communicates with a remote specialist built with a different agent framework, using an official A2A SDK and versioned contracts. This would demonstrate interoperability rather than artificially breaking one app into microservices.

## Adoption criteria

Adopt only after one or more of the following is demonstrated:
- A specialist needs separate deployment or independent scaling/ownership.
- We must call an agent owned by another team or vendor.
- Cross-framework collaboration provides value not available through normal Python interfaces.
- Isolation and permissions require a separate agent service.

An implementation proposal must document **agent discovery, authentication/authorization, TLS, task IDs, cancellation, idempotency, timeouts/retries, streaming/reconnection, artifact provenance, tenancy, audit logging, cost and operational overhead**. The specific protocol/version and SDK must be pinned and tested; do not assume older endpoint shapes match current A2A.

## Data boundary: preserve a simple internal contract

~~~python
from pydantic import BaseModel, Field

class ResearchTask(BaseModel):
    company: str
    topic: str
    instructions: str

class ResearchResult(BaseModel):
    findings: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
~~~

These are **internal example models**, not A2A wire objects. When needed, write a boundary adapter to map them to versioned A2A messages/artifacts and separately validate source provenance.

## Acceptance gate for the optional spike

Prototype one service, then compare it with the equivalent local subagent on end-to-end research accuracy, propagation of evidence, latency, deployment effort, failures, security and cost. If there is no measurable interoperability or isolation advantage, keep the simpler local architecture.

## References

- [A2A overview](https://a2a-protocol.org/latest/topics/what-is-a2a/)
- [A2A protocol specification](https://a2a-protocol.org/latest/specification/)
- [A2A roadmap](https://a2a-protocol.org/latest/roadmap/)
- [OctoDig architecture](ARCHITECTURE.md)
