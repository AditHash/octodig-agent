from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from octodig.report_contract import (
    Claim,
    ClaimClassification,
    ReportSection,
    SectionStatus,
    Source,
    empty_report,
)


def test_empty_production_report_has_all_sections() -> None:
    report = empty_report("run_1", "Example", "https://example.com", "standard")
    assert len(report.sections) == 12
    assert all(section.status == SectionStatus.INSUFFICIENT_EVIDENCE for section in report.sections.values())


def test_verified_claim_requires_a_source() -> None:
    report = empty_report("run_1", "Example", None, "standard")
    report.claims = [
        Claim(
            id="claim_1",
            section="company_overview",
            statement="Example operates software.",
            classification=ClaimClassification.VERIFIED,
        )
    ]
    report.sections["company_overview"] = ReportSection(status=SectionStatus.PARTIAL, claim_ids=["claim_1"])
    with pytest.raises(ValidationError, match="verified claims require"):
        type(report).model_validate(report.model_dump())


def test_claim_source_and_section_links_are_validated() -> None:
    report = empty_report("run_1", "Example", None, "standard")
    report.sources = [Source(id="source_1", url="https://example.com", retrieved_at=datetime.now(UTC), provider="test")]
    report.claims = [Claim(id="claim_1", section="company_overview", statement="Example is a company.", classification="verified", source_ids=["source_1"])]
    report.sections["company_overview"] = ReportSection(status="partial", claim_ids=["claim_1"])
    assert type(report).model_validate(report.model_dump()).claims[0].id == "claim_1"
