"""PostgreSQL-backed durable research queue. No Redis/Celery required."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..models import ResearchEvent, ResearchRun, RunStatus
from ..settings import get_settings


def claim_next_run(session: Session) -> ResearchRun | None:
    """Lease queued or expired work. SKIP LOCKED permits multiple workers."""
    now = datetime.now(UTC)
    settings = get_settings()
    exhausted = session.scalar(
        select(ResearchRun)
        .where(
            ResearchRun.status == RunStatus.RESEARCHING,
            ResearchRun.lease_expires_at < now,
            ResearchRun.attempts >= settings.run_max_attempts,
        )
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if exhausted is not None:
        exhausted.status = RunStatus.FAILED
        exhausted.error_code = "retry_exhausted"
        exhausted.ended_at = now
        exhausted.lease_expires_at = None
        session.add(ResearchEvent(run_id=exhausted.id, event_type="run.failed", data={"error_code": "retry_exhausted"}))
        session.commit()
        return None
    statement = (
        select(ResearchRun)
        .where(
            or_(
                ResearchRun.status == RunStatus.QUEUED,
                and_(ResearchRun.status == RunStatus.RESEARCHING, ResearchRun.lease_expires_at < now),
            ),
            ResearchRun.attempts < settings.run_max_attempts,
        )
        .order_by(ResearchRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    run = session.scalar(statement)
    if run is None:
        return None
    reclaimed = run.status == RunStatus.RESEARCHING
    run.status = RunStatus.RESEARCHING
    run.attempts += 1
    run.started_at = run.started_at or now
    run.lease_expires_at = now + timedelta(seconds=settings.run_lease_seconds)
    session.add(ResearchEvent(
        run_id=run.id,
        event_type="run.reclaimed" if reclaimed else "run.started",
        data={"attempt": run.attempts},
    ))
    session.commit()
    return run
