"""Worker entrypoint. Research execution is added after provider adapters land."""

import logging
import time

from sqlalchemy.orm import Session

from .db import engine
from .models import TargetAccount
from .services.jobs import claim_next_run, release_worker_lock
from .services.research import execute_research
from .settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_forever() -> None:
    settings = get_settings()
    logger.info("OctoDig worker started")
    while True:
        try:
            # A dedicated connection retains the advisory lock across commits.
            with engine.connect() as connection, Session(bind=connection) as session:
                run = claim_next_run(session)
                if run:
                    try:
                        logger.info("Claimed research run %s", run.id)
                        target = session.get(TargetAccount, run.account_id)
                        if target is not None:
                            execute_research(session, run, target)
                    finally:
                        session.rollback()
                        release_worker_lock(session, run.id)
                        session.commit()
        except Exception:
            # Log no provider exception text, prompts, credentials or DB URLs.
            logger.error("Worker operation failed; retrying after poll interval")
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
