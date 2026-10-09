# OctoDig Python Learning Examples

These are **self-contained lessons**, not a FastAPI server or production-ready OctoDig workflow. Examples 01–03 use paid model APIs. Examples 02–03 additionally enable OpenAI's hosted web search, which can incur separate charges. **Do not run unattended.**

## Environment (Python 3.11+)

Install [uv](https://docs.astral.sh/uv/) and then run from the repository root:

~~~bash
uv sync
cp .env.example .env
~~~

On Windows PowerShell, run `Copy-Item .env.example .env`. Edit **only your local .env** and provide `OPENAI_API_KEY`; do not commit it. The default demonstration model is `openai:gpt-5-nano`. Set `OCTODIG_MODEL` in .env to change it. These examples are documented for OpenAI; swapping provider requires changing the provider-native search tool and installing its integration.

~~~bash
uv run python examples/01_langchain_tools.py
uv run python examples/02_deep_research.py "Microsoft" --website https://www.microsoft.com
uv run python examples/03_subagents.py "Microsoft"
uv run python examples/04_validate_report.py
uv run pytest
~~~

## What each example teaches

| Example | Lesson | Important limitation |
|---|---|---|
| `01_langchain_tools.py` | LangChain `@tool` + `create_agent` and a **sample local** seller catalog | No internet research; catalog is fictional |
| `02_deep_research.py` | `create_deep_agent` + provider-native search + Markdown output | A model-written Markdown report is **not** verified evidence |
| `03_subagents.py` | Lead Deep Agent with two specialist subagents | Model may choose whether to delegate; no fixed workflow/parallelism guarantee |
| `04_validate_report.py` | Pydantic schema and deterministic coverage of 12 sections | Placeholder sections are not researched facts |
| `report_contract.py` | Reusable minimal schema used by 04 and tests | Teaching schema, not the final production report envelope |

## Framework lesson

The 01 example shows LangChain's agent/tools foundation. The 02 and 03 examples build Deep Agents **without defining a custom LangGraph graph**. Deep Agents already uses LangGraph under the hood. Add your own `StateGraph` later only for workflows that need explicit stage orchestration or recovery. See [framework choices](../docs/FRAMEWORK_CHOICES.md).

## Source integrity and safety

- Hosted web search delivers provider-generated search results/annotations. Neither automatically verifies that a URL exists **nor** that its content supports a statement.
- The examples **do not** implement citation verification, URL safety for direct HTTP fetches, customer-data handling, per-action billing enforcement, access control, or durable jobs.
- Treat generated claims and opportunities as **unverified**. Check important claims against original sources before sharing a report.
- `recursion_limit` bounds graph steps, **not dollar cost**. Set API account budgets and watch usage, especially for delegated searches.
- `output/` and `.env` are ignored by Git. Do not upload raw credentials, secret search content, or private personal details.

See [PLAN.md](../PLAN.md) for the subsequent production work.
