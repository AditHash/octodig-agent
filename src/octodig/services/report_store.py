"""Persist a validated report with its normalized evidence lineage."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ClaimEvidence, ResearchClaim, ResearchRun, ResearchSource, StoredReport
from ..report_contract import ResearchReport


def save_report(session: Session, run: ResearchRun, report: ResearchReport, markdown: str | None = None) -> StoredReport:
    if report.run_id != run.id:
        raise ValueError("report run_id does not match persistence target")
    if session.scalar(select(StoredReport.id).where(StoredReport.run_id == run.id)) is not None:
        raise ValueError("a report already exists for this run")
    for source in report.sources:
        session.add(ResearchSource(
            id=source.id, workspace_id=run.workspace_id, account_id=run.account_id, run_id=run.id,
            canonical_url=str(source.url), title=source.title, publisher=source.publisher,
            published_at=source.published_at, retrieved_at=source.retrieved_at,
            provider=source.provider, locator=source.locator,
        ))
    for claim in report.claims:
        session.add(ResearchClaim(
            id=claim.id, workspace_id=run.workspace_id, account_id=run.account_id, run_id=run.id,
            section=claim.section, statement=claim.statement, classification=claim.classification.value,
            verification_status=claim.verification_status.value, rationale=claim.rationale,
        ))
        for source_id in claim.source_ids:
            session.add(ClaimEvidence(claim_id=claim.id, source_id=source_id))
    stored = StoredReport(
        workspace_id=run.workspace_id, account_id=run.account_id, run_id=run.id,
        schema_version=report.schema_version, payload=report.model_dump(mode="json"), markdown=markdown,
    )
    session.add(stored)
    return stored
