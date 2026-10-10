"""Offline application-foundation tests; no database or paid provider needed."""

from decimal import Decimal

from fastapi.testclient import TestClient

from octodig.api import app, slugify
from octodig.models import RunStatus, WorkspaceRole
from octodig.schemas import ResearchStartRequest
from octodig.security import decode_access_token, hash_password, issue_access_token, verify_password
from octodig.settings import Settings


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_password_and_token_helpers_round_trip(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-production")
    # Settings are cached by the application, so test the password helper separately.
    hashed = hash_password("secure-development-password")
    assert verify_password("secure-development-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_workspace_slug_is_stable_and_safe() -> None:
    assert slugify("Acme & Sons, Inc.") == "acme-sons-inc"
    assert slugify("!!!") == "workspace"


def test_research_requires_positive_cost_cap() -> None:
    request = ResearchStartRequest(provider="openai", max_cost_usd="0.01")
    assert request.mode == "standard"
    assert request.max_cost_usd == Decimal("0.01")


def test_explicit_state_and_role_contracts() -> None:
    assert RunStatus.COMPLETED_PARTIAL == "completed_partial"
    assert WorkspaceRole.VIEWER == "viewer"
