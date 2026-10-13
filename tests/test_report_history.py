from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from octodig.models import Base, ResearchRun, TargetAccount, User, Workspace
from octodig.report_contract import empty_report
from octodig.services.report_store import save_report


def test_reports_receive_monotonic_versions_per_target() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        workspace = Workspace(id="workspace_1", name="Test", slug="test")
        user = User(id="user_1", email="owner@example.com", name="Owner", password_hash="hash")
        target = TargetAccount(id="account_1", workspace_id=workspace.id, name="Example")
        session.add_all([workspace, user, target])
        first_run = ResearchRun(
            id="run_1", workspace_id=workspace.id, account_id=target.id,
            requested_by_id=user.id, provider="openai", mode="standard", max_cost_usd="1",
        )
        second_run = ResearchRun(
            id="run_2", workspace_id=workspace.id, account_id=target.id,
            requested_by_id=user.id, provider="openai", mode="standard", max_cost_usd="1",
        )
        session.add_all([first_run, second_run])
        first = empty_report(first_run.id, target.name, None, "standard")
        second = empty_report(second_run.id, target.name, None, "standard")

        first_stored = save_report(session, first_run, first)
        second_stored = save_report(session, second_run, second)

        assert first_stored.report_version == 1
        assert second_stored.report_version == 2
        assert first.metadata.report_version == 1
        assert second.metadata.report_version == 2
        assert first.metadata.generated_at is not None
        assert second.metadata.fresh_until is not None
