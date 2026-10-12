"""Real migrations, SKIP LOCKED, session locks and cancellation races."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import os
import subprocess
import sys
import time

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from octodig.api import cancel_run, database_ready
from octodig.models import Base, Membership, ResearchRun, RunStatus, TargetAccount, User, Workspace
from octodig.report_contract import empty_report
from octodig.services.budget import ProviderPricing
from octodig.services.jobs import claim_next_run, release_worker_lock
from octodig.services.research import ProviderResult, execute_research


def seed(engine, count=1):
    with Session(engine) as session:
        user = User(email="postgres@example.com", name="Test", password_hash="offline-fixture")
        workspace = Workspace(name="Test", slug="test")
        session.add_all([user, workspace])
        session.flush()
        target = TargetAccount(workspace_id=workspace.id, owner_user_id=user.id, name="Example")
        session.add(target)
        session.flush()
        runs = [ResearchRun(workspace_id=workspace.id, account_id=target.id,
                            requested_by_id=user.id, provider="openai", max_cost_usd="1") for _ in range(count)]
        session.add_all(runs)
        session.commit()
        return [run.id for run in runs]


def test_migrated_schema_contains_all_model_indexes(postgres_engine):
    inspector = inspect(postgres_engine)
    for table in Base.metadata.sorted_tables:
        actual = {item["name"] for item in inspector.get_indexes(table.name)}
        assert {index.name for index in table.indexes} <= actual, table.name


def test_concurrent_workers_claim_each_run_once(postgres_engine):
    ids = seed(postgres_engine, count=8)

    def claim(_):
        with postgres_engine.connect() as connection, Session(bind=connection) as session:
            run = claim_next_run(session)
            if run:
                run_id = run.id
                release_worker_lock(session, run_id)
                session.commit()
                return run_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(claim, range(8)))
    assert set(results) == set(ids)
    assert len(results) == len(set(results))


def test_expired_lease_cannot_reclaim_live_worker(postgres_engine):
    seed(postgres_engine, count=2)
    with postgres_engine.connect() as connection, Session(bind=connection) as first:
        run = claim_next_run(first)
        # Creation order ties are immaterial: fence whichever job was claimed.
        first_id = run.id
        with Session(postgres_engine) as other:
            other.get(ResearchRun, first_id).lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
            other.commit()
        with postgres_engine.connect() as second_connection, Session(bind=second_connection) as second:
            next_run = claim_next_run(second)
            assert next_run is not None and next_run.id != first_id
            release_worker_lock(second, next_run.id)
            second.commit()
            assert claim_next_run(second) is None
        release_worker_lock(first, first_id)
        first.commit()
    with postgres_engine.connect() as connection, Session(bind=connection) as recovery:
        reclaimed = claim_next_run(recovery)
        assert reclaimed.id == first_id
        assert reclaimed.attempts == 2
        release_worker_lock(recovery, reclaimed.id)
        recovery.commit()


def test_process_crash_releases_session_lock(postgres_engine):
    run_id = seed(postgres_engine)[0]
    # Child holds the actual queue lease and lock, then is killed before spending.
    script = """
import os, sys, time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from octodig.services.jobs import claim_next_run
engine = create_engine(os.environ['OCTODIG_CHILD_TEST_URL'], connect_args={'options': os.environ['OCTODIG_CHILD_TEST_OPTIONS']})
with engine.connect() as connection, Session(bind=connection) as session:
    run = claim_next_run(session)
    print(run.id, flush=True)
    time.sleep(30)
"""
    with postgres_engine.connect() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))
    environment = {**os.environ, "PYTHONPATH": "src", "OCTODIG_CHILD_TEST_OPTIONS": f"-csearch_path={schema}",
                   "OCTODIG_CHILD_TEST_URL": postgres_engine.url.render_as_string(hide_password=False)}
    process = subprocess.Popen([sys.executable, "-c", script], env=environment, stdout=subprocess.PIPE, text=True)
    try:
        import select as select_io
        assert select_io.select([process.stdout], [], [], 15)[0], "Worker failed to start"
        assert process.stdout.readline().strip() == run_id
        with Session(postgres_engine) as session:
            session.get(ResearchRun, run_id).lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
            session.commit()
        process.kill()
        process.wait(timeout=5)
        deadline = time.monotonic() + 5
        with postgres_engine.connect() as connection, Session(bind=connection) as session:
            run = None
            while run is None and time.monotonic() < deadline:
                run = claim_next_run(session)
                if run is None:
                    time.sleep(0.05)
            assert run is not None and run.id == run_id and run.attempts == 2
            release_worker_lock(session, run.id)
            session.commit()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()


def test_cancellation_during_verification_cannot_be_overwritten(postgres_engine, monkeypatch):
    run_id = seed(postgres_engine)[0]
    monkeypatch.setattr("octodig.services.research._pricing", lambda _: ProviderPricing(
        Decimal("1"), Decimal("2"), Decimal("0"), 1000, 500, 0))
    monkeypatch.setattr("octodig.services.research._openai_report", lambda run, target, _: ProviderResult(
        empty_report(run.id, target.name, target.website, run.mode)))

    def cancel_while_verifying(_):
        with Session(postgres_engine) as session:
            workspace_id = session.get(ResearchRun, run_id).workspace_id
            cancel_run(run_id, Membership(workspace_id=workspace_id), session)

    monkeypatch.setattr("octodig.services.research.verify_report_evidence", cancel_while_verifying)
    with postgres_engine.connect() as connection, Session(bind=connection) as session:
        run = claim_next_run(session)
        execute_research(session, run, session.get(TargetAccount, run.account_id))
        assert run.status == RunStatus.CANCELLED
        release_worker_lock(session, run.id)
        session.commit()


def test_migration_command_uses_environment_database(postgres_engine):
    with postgres_engine.connect() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))
    url = postgres_engine.url.update_query_dict({"options": f"-csearch_path={schema}"})
    result = subprocess.run(["alembic", "current"], capture_output=True, text=True, timeout=20,
        env={**os.environ, "OCTODIG_DATABASE_URL": url.render_as_string(hide_password=False)})
    assert result.returncode == 0, "Migration command failed using isolated database configuration"
    assert "(head)" in result.stdout


def test_production_readiness_accepts_migrated_database(postgres_engine, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr("octodig.api.settings", SimpleNamespace(environment="production"))
    with Session(postgres_engine) as session:
        assert database_ready(session) is True
