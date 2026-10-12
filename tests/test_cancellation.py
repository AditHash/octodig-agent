from types import SimpleNamespace

from octodig.api import cancel_run
from octodig.models import RunStatus
from octodig.services.research import execute_research


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False

    def add(self, item) -> None:
        self.added.append(item)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, item) -> None:
        return None


def test_cancelling_queued_run_stops_it_before_worker_claim(monkeypatch) -> None:
    run = SimpleNamespace(id="run_1", status=RunStatus.QUEUED, ended_at=None)
    session = FakeSession()
    monkeypatch.setattr("octodig.api._owned_run", lambda *_: run)

    response = cancel_run("run_1", SimpleNamespace(workspace_id="workspace_1"), session)

    assert response.status == RunStatus.CANCELLED
    assert response.ended_at is not None
    assert session.committed
    assert session.added[0].event_type == "run.cancelled"


def test_cancelling_active_run_requests_safe_stop(monkeypatch) -> None:
    run = SimpleNamespace(id="run_1", status=RunStatus.RESEARCHING, ended_at=None)
    session = FakeSession()
    monkeypatch.setattr("octodig.api._owned_run", lambda *_: run)

    cancel_run("run_1", SimpleNamespace(workspace_id="workspace_1"), session)

    assert run.status == RunStatus.CANCEL_REQUESTED
    assert session.added[0].event_type == "run.cancel_requested"


def test_worker_honors_cancel_request_before_spending(monkeypatch) -> None:
    run = SimpleNamespace(
        id="run_1",
        status=RunStatus.CANCEL_REQUESTED,
        lease_expires_at=None,
        ended_at=None,
    )
    session = FakeSession()
    monkeypatch.setattr(
        "octodig.services.research._pricing",
        lambda _: (_ for _ in ()).throw(AssertionError("pricing must not be read for cancelled work")),
    )

    execute_research(session, run, SimpleNamespace())

    assert run.status == RunStatus.CANCELLED
    assert session.committed
    assert session.added[0].event_type == "run.cancelled"
