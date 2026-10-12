"""Isolated, offline API/worker fixture for browser acceptance tests."""

import sys
import tempfile
import threading
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from octodig.api import app
from octodig.db import get_session
from octodig.models import Base, TargetAccount
from octodig.report_contract import Claim, Source, empty_report
from octodig.services import evidence_gate, research
from octodig.services.budget import ProviderPricing
from octodig.services.jobs import claim_next_run


def fixture_report(run, target, offerings):
    report = empty_report(run.id, target.name, target.website, run.mode)
    report.target.identity_status = "resolved"
    report.sources = [Source(id="s1", url="https://example.com", title="Example official page",
                             retrieved_at="2026-10-01T00:00:00Z", provider="offline_fixture")]
    report.claims = [Claim(id="c1", section="company_overview",
                           statement="Example provides cloud software.",
                           classification="verified", source_ids=["s1"])]
    report.sections["company_overview"].claim_ids = ["c1"]
    return research.ProviderResult(report, input_tokens=100, output_tokens=50, search_calls=0)


def serve():
    with tempfile.TemporaryDirectory(prefix="octodig-browser-") as directory:
        engine = create_engine(f"sqlite:///{directory}/acceptance.db", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)

        def sessions():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = sessions
        research._pricing = lambda _: ProviderPricing(Decimal("1"), Decimal("2"), Decimal("0"), 1000, 500, 0)
        research._openai_report = fixture_report
        evidence_gate.fetch_public_text = lambda url: (url, "Example provides cloud software.")
        stopped = threading.Event()

        def work():
            while not stopped.wait(0.2):
                with Session(engine) as session:
                    run = claim_next_run(session)
                    if run:
                        research.execute_research(session, run, session.get(TargetAccount, run.account_id))

        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        try:
            uvicorn.run(app, host="127.0.0.1", port=8801)
        finally:
            stopped.set()
            worker.join(timeout=5)
            engine.dispose()


if __name__ == "__main__":
    serve()
