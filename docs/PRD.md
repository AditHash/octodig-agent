# OctoDig Product Requirements (Draft)

**Product:** evidence-driven, agentic company research and sales preparation.  
**Lifecycle:** design draft; no implementation assumed.

## Problem

Account research is fragmented across official sites, credible news, public job listings, company announcements, and other sources. Sales teams need a consolidated profile and sound business hypotheses, but generated research can be slow, repetitive, generic, or misleading if sources and uncertainty are lost.

## Personas

- Sales development representative preparing an account
- Account executive identifying timely reasons to engage
- Solution architect mapping customer needs to approved offerings
- Business/market analyst validating company developments

## Inputs

**Required:** target company name.

**Optional:** canonical website, geography, industry, seller organization, approved seller offerings/services, research question, mode (standard/deep), permitted sources, and configured run budget.

Resolve ambiguous company identities before assigning findings to an entity. When no seller-offering catalog exists, do not imply recommendations are matched to actual seller capabilities.

## Minimum deliverable — twelve sections

1. **Company overview:** name, verified website, ownership, industry, headquarters, reach, employee count and revenue only when publicly supported.
2. **Business model:** customers, distribution, channels, revenue model and operating model where available.
3. **Products and services:** main offerings, segments, business uses and differentiators.
4. **Market position:** competitors, positioning, target regions and defensible competitive context.
5. **Leadership and decision-makers:** role-relevant executives, publicly available professional roles and source links; no private contacts.
6. **Recent developments:** dated product launches, funding, acquisitions, partnerships, expansions and other relevant news.
7. **Growth and hiring signals:** dated, publicly evidenced job openings, growth plans or investments.
8. **Technology landscape:** explicitly disclosed tools, cloud services, integrations, data/AI programs; mark uncertain stacks as unverified.
9. **Business challenges and priorities:** stated priorities versus evidence-based inferences versus hypothetical pain points.
10. **Sales opportunities:** seller-relevant use cases, evidence, fit rationale, prioritization and potential value.
11. **Outreach preparation:** discovery questions, meeting brief, suggested talking points and possible objections.
12. **Sources and evidence:** supporting links, publisher, publication/retrieval dates when available, and information gaps.

Each section returns status **complete**, **partial**, **not_found**, or **insufficient_evidence**; all sections appear even when empty.

## Product behavior

- Research public data with model-selected but restricted tools.
- Cross-check important findings; surface contradictory sources.
- Label the epistemic status of each claim: verified, inferred, or hypothesis.
- Use seller-approved offerings to ground recommendations.
- Stream visible progress and provide final machine-readable plus human-readable outputs.
- Store evidence and run-level metrics for auditing and later retrieval.
- Support standard and deep modes with the same report contract.

## Nonfunctional expectations

- Bounded provider/tool expense and time per run.
- Support reconnect and persistent job state in the API stage.
- Source safety: SSRF defenses, page limits, prompt-injection resistance, and fetch provenance.
- Versioned schema, stable identifiers, tests, and evaluation fixtures.
- Privacy-aware treatment of public professional data and customer-specific research.

## Out of scope initially

Mass-contact enrichment, private-data acquisition, unrestricted scraping, automated outreach, direct CRM writes, automated purchasing, and claims of assured ROI.

## Acceptance

An acceptable V0 researches at least one company from input through output; generates all twelve sections with source-aware, appropriately qualified content; and exposes token/tool usage and gaps. See [PLAN.md](../PLAN.md) for phased milestones and [REPORT_CONTRACT.md](REPORT_CONTRACT.md) for schema expectations.
