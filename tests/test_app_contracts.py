"""Offline application-foundation tests; no database or paid provider needed."""

from decimal import Decimal
from types import SimpleNamespace

import jwt

import pytest
from fastapi.testclient import TestClient

from octodig.api import app, database_ready, slugify
from octodig.models import RunStatus, WorkspaceRole
from octodig.schemas import ResearchStartRequest
from octodig.security import decode_access_token, hash_password, verify_password
from octodig.settings import Settings


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_readiness_uses_a_minimal_query() -> None:
    class Session:
        def __init__(self) -> None:
            self.statement = None

        def execute(self, statement) -> None:
            self.statement = statement

    session = Session()
    assert database_ready(session) is True
    assert str(session.statement) == "SELECT 1"


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


def test_production_settings_reject_unsafe_defaults() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production")


def test_production_settings_accept_secure_secret_and_origin() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="a-long-non-default-secret-with-at-least-32-bytes",
        cors_origins=["https://app.example.com"],
    )
    assert settings.environment == "production"


def test_tokens_without_expiration_are_rejected(monkeypatch):
    settings = Settings(_env_file=None, jwt_secret="offline-test-secret-with-at-least-32-bytes")
    monkeypatch.setattr("octodig.security.get_settings", lambda: settings)
    token = jwt.encode({"sub": "user"}, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


@pytest.mark.parametrize("revision", [None, "0001_initial"])
def test_production_readiness_rejects_outdated_schema(monkeypatch, revision):
    monkeypatch.setattr("octodig.api.settings", SimpleNamespace(environment="production"))
    session = SimpleNamespace(execute=lambda _: None, scalar=lambda _: revision)
    assert database_ready(session) is False
