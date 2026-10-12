from decimal import Decimal

import pytest

from octodig.services.budget import BudgetExceededError, ProviderPricing, require_budget


def pricing() -> ProviderPricing:
    return ProviderPricing(Decimal("1"), Decimal("2"), Decimal("0.01"), 1_000, 500, 2)


def test_budget_reserves_worst_case_cost() -> None:
    assert require_budget("1", pricing()) == Decimal("0.022000")


def test_budget_rejects_underfunded_run_before_provider_call() -> None:
    with pytest.raises(BudgetExceededError, match="exceeds"):
        require_budget("0.01", pricing())


def test_usage_cost_uses_actual_tokens_and_searches() -> None:
    assert pricing().usage_cost(500, 100, 1) == Decimal("0.010700")
