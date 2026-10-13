from octodig.report_contract import Claim, ClaimClassification, ReportSection, ResearchReport, ReportTarget, SectionStatus, Source, ToolAction
from octodig.services.markdown import render_markdown


def test_markdown_renderer_preserves_sections_claim_labels_and_sources() -> None:
    section_keys = (
        "company_overview", "business_model", "products_services", "market_position",
        "leadership_decision_makers", "recent_developments", "growth_hiring_signals",
        "technology_landscape", "business_challenges_priorities", "sales_opportunities",
        "outreach_preparation", "sources_evidence",
    )
    report = ResearchReport(
        run_id="run_1",
        target=ReportTarget(name="Example", identity_status="resolved"),
        mode="standard",
        sections={key: ReportSection(status=SectionStatus.NOT_FOUND) for key in section_keys},
        claims=[Claim(id="claim_1", section="company_overview", statement="Example is public.", classification=ClaimClassification.VERIFIED, source_ids=["source_1"])],
        sources=[Source(id="source_1", url="https://example.com", retrieved_at="2026-01-01T00:00:00Z", provider="test")],
    )
    report.sections["company_overview"] = ReportSection(status=SectionStatus.COMPLETE, claim_ids=["claim_1"])
    report.metadata.tool_actions = [ToolAction(name="web_search", provider="openai", calls=2)]

    markdown = render_markdown(report)

    assert "## Company Overview" in markdown
    assert "**verified** — Example is public. ([source_1])" in markdown
    assert "[source_1]" in markdown
    assert "Tool actions: openai:web_search (2)" in markdown
