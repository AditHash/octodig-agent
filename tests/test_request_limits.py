from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from octodig.models import Base, RequestQuota
from octodig.services.request_limits import consume_request_limit, expire_request_limits


def test_limits_count_failures_and_reset_without_storing_identity():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime(2026, 10, 12, 12, 0, 1, tzinfo=UTC)
    with Session(engine) as session:
        for _ in range(2):
            consume_request_limit(session, "login", "private-user@example.com", limit=2, window_seconds=60, now=now)
        with pytest.raises(HTTPException) as error:
            consume_request_limit(session, "login", "private-user@example.com", limit=2, window_seconds=60, now=now)
        assert error.value.status_code == 429
        assert error.value.headers["Retry-After"] == "59"
        quota = session.scalar(select(RequestQuota))
        assert len(quota.bucket_key) == 64
        assert "private-user" not in quota.bucket_key
        assert quota.attempts == 2
        consume_request_limit(session, "login", "private-user@example.com", limit=2,
                              window_seconds=60, now=now + timedelta(minutes=1))
        session.add(RequestQuota(bucket_key="expired", attempts=1, expires_at=datetime(2020, 1, 1, tzinfo=UTC)))
        session.commit()
        expire_request_limits(session)
        assert session.get(RequestQuota, "expired") is None
    engine.dispose()
