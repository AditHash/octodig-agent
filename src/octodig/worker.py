"""Worker entrypoint. Research execution is added after provider adapters land."""

import time

from sqlalchemy.orm import Session

from .db import engine
from .models import TargetAccount
from .observability import configure_logging
from .services.jobs import claim_next_run, release_worker_lock
from .services.research import execute_research
from .settings import get_settings
from .services.request_limits import expire_request_limits

logger = configure_logging().getChild("worker")


def run_forever() -> None:
    settings = get_settings()
    logger.info("worker_started", extra={"event": "worker_started"})
    last_cleanup = 0.0
    while True:
        try:
            # A dedicated connection retains the advisory lock across commits.
            with engine.connect() as connection, Session(bind=connection) as session:
                if time.monotonic() - last_cleanup >= 60:
                    expire_request_limits(session)
                    last_cleanup = time.monotonic()
                run = claim_next_run(session)
                if run:
                    try:
                        logger.info("run_claimed", extra={"event": "run_claimed", "run_id": run.id, "attempt": run.attempts})
                        target = session.get(TargetAccount, run.account_id)
                        if target is not None:
                            execute_research(session, run, target)
                            logger.info("run_finished", extra={
                                "event": "run_finished", "run_id": run.id,
                                "attempt": run.attempts, "error_code": run.error_code,
                            })
                    finally:
                        session.rollback()
                        release_worker_lock(session, run.id)
                        session.commit()
        except Exception:
            # Log no provider exception text, prompts, credentials or DB URLs.
            logger.error("worker_operation_failed", extra={"event": "worker_operation_failed"})
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
