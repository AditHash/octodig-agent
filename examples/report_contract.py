"""Minimal Pydantic section-coverage contract.

Demonstrates deterministic completeness; does NOT verify supporting evidence.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


SECTION_KEYS = (
    "company_overview",
    "business_model",
    "products_services",
    "market_position",
    "leadership_decision_makers",
    "recent_developments",
    "growth_hiring_signals",
    "technology_landscape",
    "business_challenges_priorities",
    "sales_opportunities",
    "outreach_preparation",
    "sources_evidence",
)

SectionStatus = Literal[
    "complete", "partial", "not_found", "insufficient_evidence"
]


class Section(BaseModel):
    status: SectionStatus
    notes: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    company_name: str = Field(min_length=1)
    sections: dict[str, Section]

    @model_validator(mode="after")
    def require_all_sections(self) -> "ResearchReport":
        expected, actual = set(SECTION_KEYS), set(self.sections)
        if actual != expected:
            raise ValueError(
                f"Incorrect report sections: missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
        return self


def empty_report(company_name: str) -> ResearchReport:
    """Create explicit NOT-RESEARCHED placeholders for all twelve sections."""
    return ResearchReport(
        company_name=company_name,
        sections={
            key: Section(
                status="insufficient_evidence",
                notes=["Not researched; placeholder only."],
            )
            for key in SECTION_KEYS
        },
    )
