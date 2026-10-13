"""Application-owned verification; model labels never establish claim support."""

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit

from ..report_contract import (
    ClaimClassification,
    ResearchReport,
    SectionStatus,
    VerificationStatus,
)
from .source_fetch import SourceFetchError, fetch_public_text


@dataclass(frozen=True)
class VerificationSummary:
    attempted_sources: int
    retrieved_sources: int


def verify_report_evidence(report: ResearchReport, *, max_sources: int = 6) -> VerificationSummary:
    documents = {}
    destinations = {}
    attempted_sources = min(len(report.sources), max_sources)
    for source in report.sources[:max_sources]:
        try:
            final_url, text = fetch_public_text(str(source.url))
            documents[source.id] = text.casefold()
            destinations[source.id] = final_url
            source.retrieved_at = datetime.now(UTC)
        except (SourceFetchError, ValueError):
            report.gaps.append(f"Source {source.id} could not be safely retrieved for verification.")
    if len(report.sources) > max_sources:
        report.gaps.append("Source verification limit reached; additional citations remain unverified.")
    if not report.target.website:
        report.target.identity_status = "unresolved"
        report.gaps.append("No canonical website supplied; target identity requires review.")
    else:
        domain = report.target.website.host.lower().removeprefix("www.")
        primary = any(source.id in documents and
                      urlsplit(destinations[source.id]).hostname.lower().removeprefix("www.") == domain
                      for source in report.sources)
        if not primary:
            report.target.identity_status = "unresolved"
            report.gaps.append("Official website evidence was not retrieved; target identity remains unresolved.")
    for claim in report.claims:
        if claim.classification != ClaimClassification.VERIFIED:
            # Inferences and hypotheses cannot acquire factual verification by a model label.
            claim.verification_status = VerificationStatus.UNCHECKED
            continue
        statement = " ".join(claim.statement.split()).casefold()
        supported = report.target.identity_status == "resolved" and any(statement in documents.get(source_id, "") for source_id in claim.source_ids)
        if supported:
            claim.verification_status = VerificationStatus.SUPPORTED
        else:
            claim.classification = ClaimClassification.HYPOTHESIS
            claim.verification_status = VerificationStatus.UNSUPPORTED
            gap = f"Claim {claim.id} is unverified: its statement was not located in safely retrieved evidence."
            report.gaps.append(gap)
            report.sections[claim.section].gaps.append(gap)
    claims = {claim.id: claim for claim in report.claims}
    for section_key, section in report.sections.items():
        if section.status != SectionStatus.COMPLETE:
            continue
        section_claims = [claims[claim_id] for claim_id in section.claim_ids]
        supported_claims = [
            claim
            for claim in section_claims
            if claim.verification_status == VerificationStatus.SUPPORTED
        ]
        unsupported_claims = [
            claim
            for claim in section_claims
            if claim.verification_status == VerificationStatus.UNSUPPORTED
        ]
        if not supported_claims:
            section.status = SectionStatus.INSUFFICIENT_EVIDENCE
            gap = "Section cannot be complete without a supported verified claim."
        elif unsupported_claims:
            section.status = SectionStatus.PARTIAL
            gap = "Section has verified claims that could not be supported by retrieved evidence."
        else:
            continue
        if gap not in section.gaps:
            section.gaps.append(gap)
        if gap not in report.gaps:
            report.gaps.append(f"{section_key}: {gap}")
    for opportunity in report.opportunities:
        if opportunity.need_kind == ClaimClassification.VERIFIED and (
            not opportunity.supporting_claim_ids or any(
                claims[claim_id].verification_status != VerificationStatus.SUPPORTED
                for claim_id in opportunity.supporting_claim_ids
            )
        ):
            opportunity.need_kind = ClaimClassification.HYPOTHESIS
            opportunity.gaps.append("Need is not established by verified supporting evidence.")
    return VerificationSummary(attempted_sources=attempted_sources, retrieved_sources=len(documents))
