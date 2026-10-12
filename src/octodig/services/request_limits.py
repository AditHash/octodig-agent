"""Atomic PostgreSQL request throttles, with SQLite support for offline checks."""

import hashlib
import hmac
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..models import RequestQuota
from ..settings import get_settings


def consume_request_limit(session: Session, namespace: str, identity: str, *, limit: int,
                          window_seconds: int, now: datetime | None = None) -> None:
    """Commit the attempt before costly work, including failed authentication.

    Fixed windows permit a boundary burst of up to twice the configured count.
    The database, rather than process-local memory, arbitrates concurrent attempts.
    """
    timestamp = int((now or datetime.now(UTC)).timestamp())
    window = timestamp // window_seconds
    key = hmac.new(get_settings().jwt_secret.get_secret_value().encode(),
                   f"{namespace}\0{identity}\0{window}".encode(), hashlib.sha256).hexdigest()
    expires_at = datetime.fromtimestamp((window + 1) * window_seconds, UTC)
    dialect = session.get_bind().dialect.name
    if dialect not in {"postgresql", "sqlite"}:
        raise RuntimeError("Request throttling requires PostgreSQL")
    insert = postgres_insert if dialect == "postgresql" else sqlite_insert
    statement = insert(RequestQuota).values(bucket_key=key, attempts=1, expires_at=expires_at)
    statement = statement.on_conflict_do_update(
        index_elements=[RequestQuota.bucket_key],
        set_={"attempts": RequestQuota.attempts + 1},
        where=RequestQuota.attempts < limit,
    ).returning(RequestQuota.attempts)
    admitted = session.scalar(statement)
    session.commit()
    if admitted is None:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.",
                            headers={"Retry-After": str(max(1, (window + 1) * window_seconds - timestamp))})


def expire_request_limits(session: Session) -> None:
    session.execute(delete(RequestQuota).where(RequestQuota.expires_at < datetime.now(UTC)))
    session.commit()
