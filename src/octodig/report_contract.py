"""Validated, provider-neutral research report contract.

This contract deliberately stores normalized evidence rather than raw provider
responses. It is shared by the worker, persistence layer, API, and renderer.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


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


class SectionStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ClaimClassification(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    HYPOTHESIS = "hypothesis"


class VerificationStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    UNCHECKED = "unchecked"


class Source(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    url: HttpUrl
    title: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=300)
    published_at: datetime | None = None
    retrieved_at: datetime
    provider: str = Field(min_length=1, max_length=64)
    locator: str | None = Field(default=None, max_length=2000)


class Claim(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    section: str
    statement: str = Field(min_length=1, max_length=4000)
    classification: ClaimClassification
    verification_status: VerificationStatus = VerificationStatus.UNCHECKED
    source_ids: list[str] = Field(default_factory=list)
    rationale: str | None = Field(default=None, max_length=2000)

    @field_validator("section")
    @classmethod
    def known_section(cls, value: str) -> str:
        if value not in SECTION_KEYS:
            raise ValueError("claim section must be a canonical report section")
        return value


class ReportSection(BaseModel):
    status: SectionStatus
    claim_ids: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class Opportunity(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(min_length=1, max_length=300)
    need_kind: ClaimClassification
    offering_id: str | None = None
    supporting_claim_ids: list[str] = Field(default_factory=list)
    priority: str = Field(min_length=1, max_length=40)
    rationale: str = Field(min_length=1, max_length=2000)
    gaps: list[str] = Field(default_factory=list)
    discovery_questions: list[str] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def require_unmatched_context(self) -> "Opportunity":
        if self.offering_id is None and "unmatched" not in self.gaps:
            raise ValueError("unmatched suggestions must include an unmatched gap")
        return self


class ReportTarget(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website: HttpUrl | None = None
    identity_status: str = Field(pattern=r"^(resolved|ambiguous|unresolved)$")


class ReportMetadata(BaseModel):
    duration_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: str | None = None


class ResearchReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "0.1"
    run_id: str = Field(min_length=1)
    target: ReportTarget
    mode: str = Field(pattern=r"^(standard|deep)$")
    sections: dict[str, ReportSection]
    claims: list[Claim] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    metadata: ReportMetadata = Field(default_factory=ReportMetadata)

    @model_validator(mode="after")
    def validate_references_and_coverage(self) -> "ResearchReport":
        actual = set(self.sections)
        expected = set(SECTION_KEYS)
        if actual != expected:
            raise ValueError(
                f"incorrect report sections: missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
        source_ids = {source.id for source in self.sources}
        claim_ids = {claim.id for claim in self.claims}
        if len(claim_ids) != len(self.claims):
            raise ValueError("claim IDs must be unique")
        if len(source_ids) != len(self.sources):
            raise ValueError("source IDs must be unique")
        for claim in self.claims:
            if unknown := set(claim.source_ids) - source_ids:
                raise ValueError(f"claim {claim.id} references unknown sources: {sorted(unknown)}")
            if claim.classification == ClaimClassification.VERIFIED and not claim.source_ids:
                raise ValueError("verified claims require at least one source")
        for key, section in self.sections.items():
            if unknown := set(section.claim_ids) - claim_ids:
                raise ValueError(f"section {key} references unknown claims: {sorted(unknown)}")
            if any(claim.section != key for claim in self.claims if claim.id in section.claim_ids):
                raise ValueError(f"section {key} includes a claim from another section")
        for opportunity in self.opportunities:
            if unknown := set(opportunity.supporting_claim_ids) - claim_ids:
                raise ValueError(f"opportunity {opportunity.id} references unknown claims: {sorted(unknown)}")
        return self


def empty_report(run_id: str, name: str, website: str | None, mode: str) -> ResearchReport:
    """Create an honest twelve-section report before research begins."""
    return ResearchReport(
        run_id=run_id,
        target=ReportTarget(name=name, website=website, identity_status="unresolved"),
        mode=mode,
        sections={
            key: ReportSection(
                status=SectionStatus.INSUFFICIENT_EVIDENCE,
                gaps=["Research has not produced evidence for this section."],
            )
            for key in SECTION_KEYS
        },
        gaps=["Research has not completed."],
    )
