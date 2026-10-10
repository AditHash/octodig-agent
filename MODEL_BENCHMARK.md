# OctoDig: GPT vs Gemini Benchmark Plan

**Decision date:** 2026-10-09  
**Status:** planned methodology, **not** a published comparison result.

## Research question

Which OpenAI GPT and Google Gemini model/configuration gives OctoDig the most **accurate, source-grounded and seller-relevant** account report under acceptable latency and cost?

LangChain standardizes invocation, agent and tool interfaces, but provider-native search, citation metadata, context windows, structured-output modes, reasoning tokens and pricing **are not identical**.

## Three benchmark tracks

| Track | Inputs/tools controlled? | What it tells us |
|---|---|---|
| A. **Common-evidence model baseline** | Same curated source snippets, prompt, seller offerings and section schema; no search | Model reasoning and evidence use on an equal information base |
| B. **Shared-search agent baseline** | Same approved third-party search/retrieval tool, budgets and schema | Agent tool choice and research efficiency using comparable search access |
| C. **Native-search system comparison** | GPT uses supported OpenAI search grounding; Gemini uses supported Google Search grounding; separate cost accounting | End-to-end quality and expense of each provider's overall research stack |

**Never attribute a Track C difference solely to the model.** Native search providers return different pages, annotations and possibly different billable units.

## Initial candidate configuration

- Start with small/cost-focused models available to the API account; example defaults are `openai:gpt-5-nano` and `google_genai:gemini-2.5-flash-lite`.
- Model names, pricing, access and tool support must be verified at actual benchmark execution time.
- Use the **same company set**, geographic context, approved seller offerings, twelve-section output contract and evaluation rubric for each run.
- Run multiple trials, randomize provider order, and keep run timestamps as close as practicable for current-news tasks.
- Preserve versioned prompts and source snapshots where license/terms permit; record retrieval time.

## Inputs

Select at least five companies spanning rich documentation, modest public footprint, sparse information, ambiguous names, and recent news. Add a controlled fictional fixture for low-cost first-pass regression testing.

The committed [benchmark fixtures](fixtures/benchmark/README.md) provide this
initial set and its fictional seller catalog. They are prompt inputs only:
live-source evidence, snapshots, usage, quality reviews, and billed costs must
be recorded for every real run rather than copied into the fixture files.

Score the **same 12 sections** required by [docs/REPORT_CONTRACT.md](docs/REPORT_CONTRACT.md). Clearly distinguish factual evidence, inference, hypothesis and `not_found` outcomes. Any opportunity must map to a known seller offering; otherwise it is an unmatched suggestion.

## Measures per model/run

- Evidence-backed claim precision: manually check sampled claim ↔ actual source support.
- Company identity accuracy and contradictions.
- All twelve sections present with honest status (a not-found section is acceptable).
- Reasonable sales opportunities and outreach questions tied to evidence and approved offerings.
- Provider-specific citation provenance and verification of surfaced source links.
- Total duration; time to useful first response, if streaming.
- Reported input/output/reasoning and cached tokens (availability varies); **do not assume different tokenizers are directly comparable**.
- Model requests, tool/search actions, retries, estimated and **actual provider-billed** charges when available.
- Failure rate, rate limits, context truncation and inability to complete.

**Cost calculation** must include model calls **and separately billed search/grounding**; avoid inventing prices or counting non-billable internal steps as billed calls. Record actual pricing date/currency and provider plan.

## Evaluation process

1. Run Track A first to validate configuration and common prompting. [Example 05](examples/05_compare_providers.py) is a small, **fictional, no-search** smoke test; it does not constitute benchmark results.
2. Add a common search adapter and repeat the comparison (Track B).
3. Implement explicitly different OpenAI and Google native-grounding adapters; capture provider citations/usage (Track C).
4. Repeat standard/deep runs across the benchmark set.
5. Review factual claims against sources independently of LLM-as-judge.
6. Publish a table including failures, median latency, measured billed cost, citation support and report quality for each track.
7. Assign models per specialist only when measurements justify the extra complexity.

## Minimum reproducibility log

~~~json
{
  "benchmark_version": "0.1",
  "track": "A|B|C",
  "run_started_at": null,
  "company_fixture_id": null,
  "prompt_version": null,
  "report_schema_version": null,
  "model_id": null,
  "provider": null,
  "search_adapter": null,
  "tool_actions": null,
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "reasoning_tokens": null
  },
  "duration_ms": null,
  "provider_billed_cost": null,
  "quality_review": null
}
~~~

Null means **unknown or not recorded**, not zero.

## Engineering design

Use LangChain's `init_chat_model("openai:...")` and `init_chat_model("google_genai:...")` for shared model construction. A thin provider configuration module supplies credentials, model IDs and capability checks. Native search and grounding should live in distinct adapters; don't pass one vendor's hosted-tool schema to the other.

## References

- [LangChain models and provider interfaces](https://docs.langchain.com/oss/python/langchain/models)
- [LangChain Google GenAI integration](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai)
- [OctoDig evaluation plan](docs/EVALUATION.md)
