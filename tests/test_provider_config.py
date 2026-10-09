"""Provider registry and usage normalization tests; no live API calls."""

import pytest

from examples.provider_config import get_provider_config, summarize_usage


def test_gpt_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("OCTODIG_GPT_MODEL", "openai:gpt-5-nano")
    config = get_provider_config("gpt")
    assert config.model == "openai:gpt-5-nano"


def test_gemini_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    monkeypatch.setenv("OCTODIG_GEMINI_MODEL", "google_genai:gemini-2.5-flash-lite")
    config = get_provider_config("gemini")
    assert config.key == "gemini"


def test_missing_credential_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        get_provider_config("gemini")


def test_unknown_usage_remains_unknown() -> None:
    data = summarize_usage(None)
    assert data["input_tokens"] is None
    assert data["reasoning_tokens"] is None


def test_provider_specific_reasoning_usage() -> None:
    data = summarize_usage({
        "input_tokens": 150,
        "output_tokens": 20,
        "total_tokens": 170,
        "output_token_details": {"reasoning": 8},
    })
    assert data["reasoning_tokens"] == 8
