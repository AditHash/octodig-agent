from types import SimpleNamespace

from octodig.report_contract import Source, empty_report
from octodig.services.research import (
    ProviderCitation,
    _gemini_citations,
    _openai_citations,
    merge_provider_citations,
)


def test_openai_url_annotations_are_preserved_as_provider_citations() -> None:
    messages = [SimpleNamespace(content=[{
        "type": "output_text",
        "annotations": [{
            "type": "url_citation",
            "url": "https://example.com/announcement",
            "title": "Example announcement",
        }],
    }])]

    citations = _openai_citations(messages)

    assert citations == [ProviderCitation(
        url="https://example.com/announcement",
        title="Example announcement",
        provider="openai_web_search",
        locator="OpenAI hosted-search citation",
    )]


def test_gemini_grounding_chunks_are_preserved_as_provider_citations() -> None:
    grounding = SimpleNamespace(grounding_chunks=[
        SimpleNamespace(web=SimpleNamespace(uri="https://example.com/news", title="Example news")),
    ])

    citations = _gemini_citations(grounding)

    assert citations == [ProviderCitation(
        url="https://example.com/news",
        title="Example news",
        provider="gemini_google_search",
        locator="Gemini grounding citation",
    )]


def test_provider_citations_are_deduplicated_and_do_not_trust_unsafe_urls() -> None:
    report = empty_report("run_1", "Example", None, "standard")
    report.sources = [Source(
        id="model_source",
        url="https://example.com",
        retrieved_at="2026-01-01T00:00:00Z",
        provider="model",
    )]

    merge_provider_citations(report, [
        ProviderCitation("https://example.com", "Duplicate", "openai_web_search"),
        ProviderCitation("https://example.com/", "Normalized duplicate", "openai_web_search"),
        ProviderCitation("https://example.com/grounded", "Grounded", "openai_web_search"),
        ProviderCitation("http://example.com/insecure", "Insecure", "openai_web_search"),
        ProviderCitation("https://127.0.0.1/private", "Private", "openai_web_search"),
    ])

    assert [source.id for source in report.sources] == ["model_source", "provider_source_1"]
    source = report.sources[-1]
    assert str(source.url) == "https://example.com/grounded"
    assert source.provider == "openai_web_search"
    assert source.locator == "OpenAI hosted-search citation" or source.locator is None
