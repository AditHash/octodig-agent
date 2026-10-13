from octodig.settings import Settings
import pytest


def test_documented_environment_variables_are_loaded(monkeypatch):
    monkeypatch.setenv("OCTODIG_ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "verification-secret-with-adequate-length")
    monkeypatch.setenv("OCTODIG_CORS_ORIGINS", "https://app.example.com,https://admin.example.com")
    monkeypatch.setenv("OCTODIG_OPENAI_INPUT_USD_PER_MILLION", "1.25")
    settings = Settings(_env_file=None)
    assert settings.environment == "production"
    assert len(settings.cors_origins) == 2
    assert str(settings.openai_input_usd_per_million) == "1.25"


def test_blank_example_configuration_does_not_prevent_startup(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OCTODIG_OPENAI_INPUT_USD_PER_MILLION", "")
    settings = Settings(_env_file=None)
    assert settings.openai_api_key is None
    assert settings.openai_input_usd_per_million is None


def test_production_requires_https_origins():
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(_env_file=None, environment="production", jwt_secret="offline-test-secret-with-at-least-32-bytes",
                 cors_origins=["http://app.example.com"])
