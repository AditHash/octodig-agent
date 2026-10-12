"""Exercise HTTP transport and ownership against an isolated relational database.

SQLite tests application behavior; PostgreSQL migrations require separate checks.
"""

import pytest
from contextlib import contextmanager
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from octodig.api import app
from octodig.db import Base, get_session
from octodig.models import ResearchRun, RunStatus, TargetAccount
from octodig.report_contract import empty_report
from octodig.services.research import ProviderResult, execute_research
from octodig.services.budget import ProviderPricing
from octodig.settings import Settings
from decimal import Decimal


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("octodig.security.get_settings", lambda: Settings(
        _env_file=None, jwt_secret="offline-test-secret-with-at-least-32-bytes",
    ))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def register(client, email):
    response = client.post("/api/v1/auth/register", json={
        "email": email, "name": "Test Owner", "workspace_name": "Test Workspace",
        "password": "test-password-long-enough",
    })
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_authenticated_workflow_and_tenant_isolation(client):
    first = register(client, "owner1@example.com")
    second = register(client, "owner2@example.com")
    login = client.post("/api/v1/auth/login", json={
        "email": "owner1@example.com", "password": "test-password-long-enough",
    })
    assert login.status_code == 200
    assert client.get("/api/v1/targets").status_code == 401
    target = client.post("/api/v1/targets", headers=first, json={
        "name": "Example Account", "website": "https://example.com",
    })
    assert target.status_code == 201
    target_id = target.json()["id"]
    assert len(client.get("/api/v1/targets", headers=first).json()) == 1
    assert client.get("/api/v1/targets", headers=second).json() == []
    offering = client.post("/api/v1/offerings", headers=first, json={
        "name": "Cloud Review", "description": "Cloud infrastructure review", "approved": True,
    })
    assert offering.status_code == 201
    assert client.get("/api/v1/offerings", headers=second).json() == []
    request = {"provider": "openai", "max_cost_usd": "0.0500"}
    headers = {**first, "Idempotency-Key": "test-action"}
    path = f"/api/v1/targets/{target_id}/research"
    queued = client.post(path, headers=headers, json=request)
    assert queued.status_code == 202, queued.text
    run_id = queued.json()["id"]
    retry = client.post(path, headers=headers, json={**request, "max_cost_usd": "0.05"})
    assert retry.status_code == 202
    assert retry.json()["id"] == run_id
    assert client.post(path, headers=headers, json={**request, "provider": "gemini"}).status_code == 409
    assert client.post(path, headers=second, json=request).status_code == 404
    assert client.get(f"/api/v1/runs/{run_id}", headers=second).status_code == 404
    assert client.get(f"/api/v1/runs/{run_id}/report", headers=second).status_code == 404
    cancelled = client.post(f"/api/v1/runs/{run_id}/cancel", headers=first)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get("/health/ready").status_code == 200


def test_browser_preflight_allows_idempotency_header(client):
    response = client.options("/api/v1/targets/target/research", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type,Idempotency-Key",
    })
    assert response.status_code == 200, response.text


def test_worker_report_is_retrievable_only_by_owning_workspace(client, monkeypatch):
    first = register(client, "report-owner@example.com")
    second = register(client, "other-owner@example.com")
    target_id = client.post("/api/v1/targets", headers=first, json={"name": "Example"}).json()["id"]
    queued = client.post(f"/api/v1/targets/{target_id}/research", headers=first,
                         json={"provider": "openai", "max_cost_usd": "1"})
    run_id = queued.json()["id"]
    assert queued.json()["attempts"] == 0
    monkeypatch.setattr("octodig.services.research._pricing", lambda _: ProviderPricing(
        Decimal("1"), Decimal("2"), Decimal("0"), 1000, 500, 0
    ))
    monkeypatch.setattr("octodig.services.research._openai_report", lambda run, target, offerings: ProviderResult(
        empty_report(run.id, target.name, target.website, run.mode), input_tokens=100, output_tokens=50
    ))
    with contextmanager(app.dependency_overrides[get_session])() as session:
        run = session.get(ResearchRun, run_id)
        run.status = RunStatus.RESEARCHING
        session.commit()
        execute_research(session, run, session.get(TargetAccount, target_id))
    report = client.get(f"/api/v1/runs/{run_id}/report", headers=first)
    assert report.status_code == 200
    assert len(report.json()["sections"]) == 12
    assert report.json()["metadata"]["input_tokens"] == 100
    markdown = client.get(f"/api/v1/runs/{run_id}/report.md", headers=first)
    assert markdown.status_code == 200
    assert "Account research: Example" in markdown.text
    assert client.get(f"/api/v1/runs/{run_id}/report", headers=second).status_code == 404
    assert client.get(f"/api/v1/runs/{run_id}/report.md", headers=second).status_code == 404
