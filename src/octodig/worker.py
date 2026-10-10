"""Worker entrypoint. Research execution is added after provider adapters land."""

import logging
import time

from .db import SessionLocal
from .models import ResearchRun, TargetAccount
from .services.jobs import claim_next_run
from .services.research import execute_research
from .settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_forever() -> None:
    settings = get_settings()
    logger.info("OctoDig worker started")
    while True:
        with SessionLocal() as session:
            run = claim_next_run(session)
        if run:
            logger.info("Claimed research run %s", run.id)
            with SessionLocal() as session:
                persisted = session.get(ResearchRun, run.id)
                target = session.get(TargetAccount, run.account_id)
                if persisted is not None and target is not None:
                    execute_research(session, persisted, target)
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
