import pytest

from octodig.services.research import ResearchProviderError, _json_object


def test_extracts_fenced_json_provider_output() -> None:
    assert _json_object("```json\n{\"run_id\": \"run_1\"}\n```") == {"run_id": "run_1"}


def test_rejects_non_json_provider_output() -> None:
    with pytest.raises(ResearchProviderError, match="malformed"):
        _json_object("This is not a report")
