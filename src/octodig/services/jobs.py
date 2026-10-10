"""PostgreSQL-backed durable research queue. No Redis/Celery required."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ResearchEvent, ResearchRun, RunStatus
from ..settings import get_settings


def claim_next_run(session: Session) -> ResearchRun | None:
    """Lease one queued run. SKIP LOCKED permits multiple worker processes."""
    now = datetime.now(UTC)
    statement = (
        select(ResearchRun)
        .where(
            ResearchRun.status == RunStatus.QUEUED,
            (ResearchRun.lease_expires_at.is_(None)) | (ResearchRun.lease_expires_at < now),
        )
        .order_by(ResearchRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    run = session.scalar(statement)
    if run is None:
        return None
    run.status = RunStatus.RESEARCHING
    run.attempts += 1
    run.started_at = run.started_at or now
    run.lease_expires_at = now + timedelta(seconds=get_settings().run_lease_seconds)
    session.add(ResearchEvent(run_id=run.id, event_type="run.started", data={"attempt": run.attempts}))
    session.commit()
    return run
