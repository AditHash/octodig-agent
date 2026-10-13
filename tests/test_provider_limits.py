from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from octodig.report_contract import empty_report
from octodig.services.research import OpenAIRunBudget, _openai_report, _pricing
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
    assert captured["subagents"] == []
    assert "ResearchReport" in captured["system_prompt"]
    monkeypatch.setattr(type(model), "get_num_tokens_from_messages", lambda *_: 1)
    request = SimpleNamespace(system_message=None, messages=[], model_settings={}, tools=[{"type": "web_search"}, {"type": "function", "name": "execute"}],
                              override=lambda **changes: changes)
    filtered = captured["middleware"][0].wrap_model_call(request, lambda value: value)
    assert filtered["tools"] == [{"type": "web_search"}]
    assert filtered["model_settings"]["max_tool_calls"] == 3
    assert filtered["model_settings"]["max_tokens"] == settings.research_max_output_tokens
    monkeypatch.setattr(type(model), "get_num_tokens_from_messages", lambda *_: settings.research_max_input_tokens + 1)
    with pytest.raises(BudgetExceededError):
        captured["middleware"][0].wrap_model_call(request, lambda _: pytest.fail("Provider must not be called"))


def test_deep_openai_registers_bounded_domain_specialists(monkeypatch):
    settings = Settings(_env_file=None, openai_api_key="dummy-verification-key")
    monkeypatch.setattr("octodig.services.research.get_settings", lambda: settings)
    captured = {}
    report = empty_report("run_deep", "Example", None, "deep")

    def agent(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(invoke=lambda *args, **kw: {"messages": [SimpleNamespace(
            content=report.model_dump_json(), usage_metadata=None, tool_calls=[
                {"name": "task", "args": {"subagent_type": name}}
                for name in ("company_market", "people_signals", "technology")
            ],
        )]})

    monkeypatch.setattr("octodig.services.research.create_deep_agent", agent)
    result = _openai_report(SimpleNamespace(id="run_deep", mode="deep"), SimpleNamespace(name="Example", website=None), [])
    assert result.model_calls == 0
    assert [spec["name"] for spec in captured["subagents"]] == [
        "company_market", "people_signals", "technology", "general-purpose",
    ]
    assert all(spec["tools"] == [{"type": "web_search"}] for spec in captured["subagents"])
    assert all(spec["middleware"][1].run_limit == 1 for spec in captured["subagents"])
    assert captured["middleware"][1].run_limit == 2
    assert result.delegates_used == ["company_market", "people_signals", "technology"]


def test_shared_agent_budget_enforces_parallel_run_ceiling():
    budget = OpenAIRunBudget(max_calls=5, max_input=100, max_output=100, max_search=3)
    def reserve():
        try:
            return budget.reserve(10, 20)
        except BudgetExceededError:
            return None

    with ThreadPoolExecutor(max_workers=12) as pool:
        reservations = list(pool.map(lambda _: reserve(), range(20)))
    successful = [reservation for reservation in reservations if reservation is not None]
    assert len(successful) == 5
    assert sum(search for _, search in successful) == 3
    assert budget.calls == 5
    assert budget.input_tokens == 50
    with pytest.raises(BudgetExceededError, match="model-call"):
        budget.reserve(1, 1)


def test_deep_openai_preflight_reserves_shared_budget(monkeypatch):
    settings = Settings(
        _env_file=None,
        openai_input_usd_per_million="1",
        openai_output_usd_per_million="2",
        openai_search_call_usd="0.01",
    )
    monkeypatch.setattr("octodig.services.research.get_settings", lambda: settings)
    standard = _pricing("openai", "standard")
    deep = _pricing("openai", "deep")
    assert standard.max_input_tokens == settings.research_max_input_tokens
    assert deep.max_input_tokens == settings.research_max_input_tokens * 5
    assert deep.max_output_tokens == settings.research_max_output_tokens * 5
    assert deep.max_search_calls == settings.research_max_search_calls
