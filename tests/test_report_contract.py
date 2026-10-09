"""Offline tests: no API key required."""

import pytest
from pydantic import ValidationError

from examples.report_contract import (
    SECTION_KEYS,
    ResearchReport,
    Section,
    empty_report,
)


def test_blank_report_has_all_twelve_sections() -> None:
    report = empty_report("Example Company")
    assert len(report.sections) == 12
    assert set(report.sections) == set(SECTION_KEYS)
    assert all(s.status == "insufficient_evidence" for s in report.sections.values())


def test_missing_section_rejected() -> None:
    sections = empty_report("Example Company").model_dump()["sections"]
    sections.pop("sources_evidence")
    with pytest.raises(ValidationError, match="missing="):
        ResearchReport(company_name="Example Company", sections=sections)


def test_extra_section_rejected() -> None:
    sections = empty_report("Example Company").model_dump()["sections"]
    sections["invented"] = Section(status="complete")
    with pytest.raises(ValidationError, match="unexpected="):
        ResearchReport(company_name="Example Company", sections=sections)
