from types import SimpleNamespace

from octodig.report_contract import empty_report
from octodig.services.research import _openai_report
from octodig.settings import Settings
from octodig.services.budget import BudgetExceededError
import pytest


def test_openai_request_has_provider_and_agent_limits(monkeypatch):
    settings = Settings(_env_file=None, openai_api_key="dummy-verification-key")
    monkeypatch.setattr("octodig.services.research.get_settings", lambda: settings)
    captured = {}
    report = empty_report("run_1", "Example", None, "standard")

    def agent(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(invoke=lambda *args, **kw: {"messages": [SimpleNamespace(
            content=report.model_dump_json(), usage_metadata=None, tool_calls=[],
        )]})

    monkeypatch.setattr("octodig.services.research.create_deep_agent", agent)
    result = _openai_report(SimpleNamespace(id="run_1", mode="standard"), SimpleNamespace(name="Example", website=None), [])
    assert result.report.run_id == "run_1"
    model = captured["model"]
    assert model.max_tokens == settings.research_max_output_tokens
    assert model.max_retries == 0
    assert model.request_timeout == settings.provider_timeout_seconds
    assert model.model_kwargs["max_tool_calls"] == settings.research_max_search_calls
    assert captured["middleware"][1].run_limit == 1
    assert "ResearchReport" in captured["system_prompt"]
    monkeypatch.setattr(type(model), "get_num_tokens_from_messages", lambda *_: 1)
    request = SimpleNamespace(system_message=None, messages=[], tools=[{"type": "web_search"}, {"type": "function", "name": "execute"}],
                              override=lambda **changes: changes)
    filtered = captured["middleware"][0].wrap_model_call(request, lambda value: value)
    assert filtered["tools"] == [{"type": "web_search"}]
    monkeypatch.setattr(type(model), "get_num_tokens_from_messages", lambda *_: settings.research_max_input_tokens + 1)
    with pytest.raises(BudgetExceededError):
        captured["middleware"][0].wrap_model_call(request, lambda _: pytest.fail("Provider must not be called"))
