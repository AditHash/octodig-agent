"""Preflight spend reservation using operator-configured provider rates.

Rates are configuration, never copied from stale source code or guessed at run
time. Operators update them with their actual provider plan/pricing date.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProviderPricing:
    input_per_million: Decimal
    output_per_million: Decimal
    search_call: Decimal
    max_input_tokens: int
    max_output_tokens: int
    max_search_calls: int

    def worst_case_cost(self) -> Decimal:
        return (
            self.input_per_million * Decimal(self.max_input_tokens) / Decimal(1_000_000)
            + self.output_per_million * Decimal(self.max_output_tokens) / Decimal(1_000_000)
            + self.search_call * Decimal(self.max_search_calls)
        ).quantize(Decimal("0.000001"))


class BudgetExceededError(RuntimeError):
    pass


def require_budget(cap_usd: str, pricing: ProviderPricing) -> Decimal:
    cap = Decimal(cap_usd)
    reserved = pricing.worst_case_cost()
    if reserved > cap:
        raise BudgetExceededError(
            f"Configured worst-case provider cost ${reserved} exceeds run cap ${cap}."
        )
    return reserved
