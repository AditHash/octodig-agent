# Research Report and Evidence Contract

**Status:** v0 contract implemented in `src/octodig/report_contract.py`. This
document remains the external behavior specification; FastAPI report endpoints
and database persistence are added incrementally around the same contract.

## Section coverage — required keys

All reports address twelve canonical keys:

| Key | Report section |
|---|---|
| company_overview | Company overview |
| business_model | Business model |
| products_services | Products and services |
| market_position | Market position |
| leadership_decision_makers | Leadership and decision-makers |
| recent_developments | Recent developments |
| growth_hiring_signals | Growth and hiring signals |
| technology_landscape | Technology landscape |
| business_challenges_priorities | Business challenges and priorities |
| sales_opportunities | Sales opportunities |
| outreach_preparation | Outreach preparation |
| sources_evidence | Sources and evidence |

Section status: **complete**, **partial**, **not_found**, **insufficient_evidence**. A section can exist with zero findings, provided gaps explain why.

## Distinct concepts

**Evidence classification** describes what a claim means:
- **verified:** directly supported by accessible, relevant evidence.
- **inferred:** reasonable interpretation based on stated observations, not directly asserted by the source.
- **hypothesis:** a proposed need or use case requiring discovery/validation.

**Verification status** describes whether references were checked and whether they support the claim; it is separate from classification.

**Section status** describes completeness relative to requested coverage, not source reliability.

Never label an LLM's unverified output verified solely because it includes a citation-looking URL.

## Suggested JSON envelope

~~~json
{
  "schema_version": "0.1",
  "run_id": "run_example",
  "target": {
    "name": "Example Company",
    "website": "https://example.com",
    "identity_status": "resolved"
  },
  "mode": "standard",
  "sections": {
    "company_overview": {
      "status": "partial",
      "claim_ids": ["claim_1"],
      "gaps": ["Public revenue figure not found"]
    }
  },
  "claims": [
    {
      "id": "claim_1",
      "section": "company_overview",
      "statement": "The company offers enterprise software.",
      "classification": "verified",
      "verification_status": "supported",
      "source_ids": ["source_1"]
    }
  ],
  "sources": [
    {
      "id": "source_1",
      "url": "https://example.com",
      "title": "Company homepage",
      "publisher": "Example Company",
      "published_at": null,
      "retrieved_at": "2026-10-09T00:00:00Z"
    }
  ],
  "opportunities": [],
  "gaps": [],
  "metadata": {
    "duration_ms": null,
    "input_tokens": null,
    "output_tokens": null,
    "estimated_cost_usd": null
  }
}
~~~

**Important:** The JSON above abbreviates the sections object for readability. **Real report payloads must contain every one of the twelve keys**, including empty/insufficient sections. Example Company and URLs are placeholders, not real company research.

## Source expectations

Each source should record:
- Stable ID and canonical URL
- Human-readable title/publisher when available
- Publication date when reliably known; retrieved_at for successful fetches
- Content availability and retrieval status
- Optional short quote/locator supporting linked claims
- De-duplication key and provenance (tool/provider)

Sources must not be invented, even when the final Markdown looks plausible. Source URLs or annotations are not proof the claimed fact is present on the page.

## Opportunity contract

Each sales opportunity should specify:
- Business problem / observed signal
- Whether need is stated, inferred, or hypothetical
- Proposed solution/use case and seller offering ID if known
- Supporting claim IDs and gaps
- Priority with a transparent rationale, not a fabricated probability
- Expected benefits as qualitative hypotheses unless verified
- At least one discovery question

When no approved seller catalog is supplied, label ideas as **unmatched suggestions**, not seller-qualified opportunities.

## Output production

1. Agents gather and normalize claims/sources.
2. Code links, deduplicates and checks references; model-assisted verification may flag unsupported content.
3. Opportunity analysis consumes normalized evidence and seller context.
4. A deterministic coverage validator materializes all twelve section keys and rejects malformed payloads.
5. Markdown/HTML rendering is downstream from the validated structured report.

A missing section is a validation error; a present section with status not_found is an honest research outcome.

## Future evolution

Maintain schema_version and explicit migrations for breaking changes. Store raw provider annotations separately from normalized citation objects when useful. Avoid storing encrypted provider reasoning payloads in logs and report artifacts.
