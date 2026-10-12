from types import SimpleNamespace

from octodig.api import same_research_request
from octodig.schemas import ResearchStartRequest


def test_idempotency_requires_the_same_paid_research_request() -> None:
    run = SimpleNamespace(account_id="account_1", provider="openai", mode="standard", max_cost_usd="0.0500")
    matching = ResearchStartRequest(provider="openai", mode="standard", max_cost_usd="0.0500")
    changed = ResearchStartRequest(provider="gemini", mode="standard", max_cost_usd="0.0500")

    assert same_research_request(run, "account_1", matching)
    assert not same_research_request(run, "account_1", changed)
