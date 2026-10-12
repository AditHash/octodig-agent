"""PostgreSQL-backed durable research queue. No Redis/Celery required."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from ..models import ResearchEvent, ResearchRun, RunStatus
from ..settings import get_settings


def acquire_worker_lock(session: Session, run_id: str) -> bool:
    """Session-level PostgreSQL lock fences paid work across lease expiry.

    The worker must bind its session to a dedicated connection, retaining the
    lock through commits, and release it before returning that connection.
    """
    if session.get_bind().dialect.name != "postgresql":
        return True
    return bool(session.scalar(text("SELECT pg_try_advisory_lock(hashtextextended(:run_id, 0))"), {"run_id": run_id}))


def release_worker_lock(session: Session, run_id: str) -> None:
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_unlock(hashtextextended(:run_id, 0))"), {"run_id": run_id})


def claim_next_run(session: Session) -> ResearchRun | None:
    """Lease queued or expired work. SKIP LOCKED permits multiple workers."""
    now = datetime.now(UTC)
    settings = get_settings()
    cancelled = session.scalar(select(ResearchRun).where(
        ResearchRun.status == RunStatus.CANCEL_REQUESTED,
        ResearchRun.lease_expires_at < now,
    ).with_for_update(skip_locked=True).limit(1))
    if cancelled is not None and acquire_worker_lock(session, cancelled.id):
        cancelled.status = RunStatus.CANCELLED
        cancelled.ended_at = now
        cancelled.lease_expires_at = None
        session.add(ResearchEvent(run_id=cancelled.id, event_type="run.cancelled", data={"recovered": True}))
        session.commit()
        release_worker_lock(session, cancelled.id)
        return None
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
    if exhausted is not None and acquire_worker_lock(session, exhausted.id):
        exhausted.status = RunStatus.FAILED
        exhausted.error_code = "retry_exhausted"
        exhausted.ended_at = now
        exhausted.lease_expires_at = None
        session.add(ResearchEvent(run_id=exhausted.id, event_type="run.failed", data={"error_code": "retry_exhausted"}))
        session.commit()
        release_worker_lock(session, exhausted.id)
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
    run = None
    for offset in range(10):
        candidate = session.scalar(statement.offset(offset))
        if candidate is None:
            break
        if acquire_worker_lock(session, candidate.id):
            run = candidate
            break
    if run is None:
        session.rollback()
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
