# Evaluation and Cost Measurement Plan

**Status:** proposed tests for OctoDig milestones.

Research quality must be measured independently of how polished its prose looks. We will benchmark both **single-agent Deep Research** and **hybrid specialist research** rather than assuming either design is better.

## Two independent provider comparison questions

1. **Model comparison:** with identical supplied evidence or a shared search provider, how do GPT and Gemini perform on the same prompts and twelve-section contract?
2. **End-to-end provider comparison:** with each vendor's native web search/grounding, which complete stack provides better trustworthy research per unit of time and cost? Search implementations are not controlled in this track.

Do **not** conflate these comparisons, or treat token counts from different tokenizers as directly equivalent dollar costs. The detailed protocol lives in [../MODEL_BENCHMARK.md](../MODEL_BENCHMARK.md).

## Benchmark dataset

Create representative target-company fixtures:
- Large public company with abundant official source material
- Medium company with product and careers pages
- Small company with sparse publicly available data
- Company name ambiguous across multiple businesses
- Company with a recently changed leadership/product situation
- A deliberately misleading or injected web page in a controlled test

Pair each target with a **known seller-offering catalog** so sales recommendations can be evaluated for relevance.

## Dimensions

| Dimension | Metric / method |
|---|---|
| Coverage | All 12 report keys exist, with honest statuses |
| Citation support | Percentage of sampled material claims supported by cited pages |
| Factuality | Incorrect or contradicted factual claims per report |
| Uncertainty handling | Appropriate use of missing/inferred/hypothesis labels |
| Sales relevance | Opportunities genuinely fit seller offering and target context |
| Timeliness | End-to-end p50/p95 run duration; time to first useful progress |
| Cost | Total provider billed spend, input/output/reasoning tokens, search calls |
| Efficiency | Repeated/avoidable searches, tool failures, agent retries |
| Robustness | Graceful partial report on missing sources and provider failures |
| Security | Injection, SSRF and authorization test success |

## Cost accounting

Track model call usage (including reasoning tokens when provider reports them), paid web-search calls/hosted-tool actions, model rate, caching effects, and final provider billing. Count internal web actions separately from billable tool calls: the two aren't always identical.

Define explicit **standard** and **deep** mode budgets and record:
- Max elapsed time
- Max model calls and tokens
- Max search tool charges/requests
- Max agent parallelism and follow-up cycles
- Actual or best-available estimated cost per run

Don't assume a graph recursion limit is a billing limit. A model may generate extra reasoning tokens even for a short final answer.

## Benchmark process

1. Fix the same company input, seller offering catalog and output contract.
2. Execute comparable runs using a single researcher and a hybrid orchestration.
3. Save versioned prompts, model IDs, search provider configuration, evidence and metrics.
4. Review a sample of factual claims against the cited source texts.
5. Check output usefulness and factual support, not only model-as-judge scores.
6. Record the winner *for each metric*, then decide trade-offs intentionally.

## Acceptance targets

Initial gates are qualitative until enough data exists for meaningful numeric thresholds:
- Zero missing mandatory section keys
- Zero unsupported claims intentionally labeled verified in reviewed samples
- No opportunities presented as seller-qualified without a seller-offering match
- Explicit gaps for missing public evidence
- Within configured run budgets
- Failed/cancelled runs leave interpretable records

Tighten targets after collecting a baseline from real tests.
