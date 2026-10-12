from types import SimpleNamespace

from octodig.services.research import _openai_usage


def test_openai_usage_collects_final_token_usage_and_search_calls() -> None:
    messages = [
        SimpleNamespace(
            usage_metadata={"input_tokens": 120, "output_tokens": 35, "output_token_details": {"reasoning": 9}},
            tool_calls=[{"name": "web_search"}, {"name": "other_tool"}],
        )
    ]

    assert _openai_usage(messages) == (120, 35, 9, 1)


def test_openai_usage_leaves_unknown_usage_explicit() -> None:
    assert _openai_usage([SimpleNamespace(usage_metadata=None, tool_calls=[])]) == (None, None, None, 0)
