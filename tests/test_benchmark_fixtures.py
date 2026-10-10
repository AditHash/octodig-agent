"""Committed benchmark inputs must remain complete and internally consistent."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from fixtures.benchmark.validate import CompanyCorpus, load_corpus


def test_benchmark_corpus_is_valid() -> None:
    companies, catalog = load_corpus()
    assert len(companies.fixtures) == 5
    assert len(catalog.offerings) == 4


def test_unknown_offering_id_is_rejected(tmp_path: Path) -> None:
    source_root = Path(__file__).parents[1] / "fixtures" / "benchmark"
    (tmp_path / "companies.json").write_text((source_root / "companies.json").read_text())
    (tmp_path / "seller_offerings.json").write_text(
        (source_root / "seller_offerings.json").read_text()
    )
    text = (tmp_path / "companies.json").read_text().replace(
        '"data-platform-modernization"', '"unknown-offering"', 1
    )
    (tmp_path / "companies.json").write_text(text)

    try:
        load_corpus(tmp_path)
    except ValueError as exc:
        assert "unknown offering IDs" in str(exc)
    else:
        raise AssertionError("unknown offering reference should be rejected")


def test_ambiguous_fixture_cannot_supply_a_canonical_website() -> None:
    with pytest.raises(ValidationError, match="cannot pre-resolve"):
        CompanyCorpus.model_validate({
            "fixture_version": "0.1",
            "purpose": "test",
            "fixtures": [
                {
                    "id": profile,
                    "company_name": "Example",
                    "official_website": "https://example.com" if profile == "ambiguous" else None,
                    "geography": "US",
                    "fixture_kind": "identity_ambiguity" if profile == "ambiguous" else "controlled_fictional",
                    "coverage_profile": profile,
                    "research_focus": "test",
                    "expected_evidence_types": [],
                    "allowed_offering_ids": [],
                    "evaluation_notes": ["test"]
                }
                for profile in ("rich_public", "medium_public", "ambiguous", "sparse", "recent_change")
            ]
        })
