"""Small provider/model registry for a fair no-search learning baseline.

Only models listed here are supported by example 05. Native web search is not
portable; never mix provider-specific built-in search tools in this baseline.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    key: str
    model: str
    api_key_env: str


def get_provider_config(provider: str) -> ProviderConfig:
    registry = {
        "gpt": ProviderConfig(
            key="gpt",
            model=os.getenv("OCTODIG_GPT_MODEL") or "openai:gpt-5-nano",
            api_key_env="OPENAI_API_KEY",
        ),
        "gemini": ProviderConfig(
            key="gemini",
            model=os.getenv("OCTODIG_GEMINI_MODEL") or "google_genai:gemini-2.5-flash-lite",
            api_key_env="GOOGLE_API_KEY",
        ),
    }
    if provider not in registry:
        raise ValueError(f"Unknown provider {provider!r}; use 'gpt' or 'gemini'.")
    config = registry[provider]
    expected_prefix = "openai:" if provider == "gpt" else "google_genai:"
    if not config.model.startswith(expected_prefix):
        raise ValueError(
            f"{provider} example expects a model starting with {expected_prefix!r}."
        )
    if not os.getenv(config.api_key_env):
        raise ValueError(
            f"Missing {config.api_key_env}; add it to the local .env file."
        )
    return config


def summarize_usage(usage: dict | None) -> dict[str, int | None]:
    """Preserve unknown token counts as null instead of inventing zeros."""
    usage = usage or {}
    details = usage.get("output_token_details") or {}
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "reasoning_tokens": details.get("reasoning") if isinstance(details, dict) else None,
    }
