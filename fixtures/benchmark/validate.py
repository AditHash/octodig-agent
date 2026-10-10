"""Validate committed benchmark inputs without making network or model calls."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, model_validator


ROOT = Path(__file__).parent
REQUIRED_PROFILES = {
    "rich_public",
    "medium_public",
    "ambiguous",
    "sparse",
    "recent_change",
}


class Fixture(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    company_name: str = Field(min_length=1)
    official_website: HttpUrl | None
    geography: str = Field(min_length=1)
    fixture_kind: str
    coverage_profile: str
    research_focus: str = Field(min_length=1)
    expected_evidence_types: list[str]
    allowed_offering_ids: list[str]
    evaluation_notes: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_fixture_rules(self) -> "Fixture":
        if self.coverage_profile == "ambiguous" and self.official_website is not None:
            raise ValueError("ambiguous fixtures cannot pre-resolve an official website")
        if self.coverage_profile == "sparse" and self.fixture_kind != "controlled_fictional":
            raise ValueError("sparse fixture must be controlled_fictional")
        if self.fixture_kind == "controlled_fictional" and self.official_website:
            if urlparse(str(self.official_website)).hostname != "example.invalid":
                raise ValueError("controlled fictional fixtures must use example.invalid")
        return self


class CompanyCorpus(BaseModel):
    fixture_version: str
    purpose: str
    fixtures: list[Fixture] = Field(min_length=5)

    @model_validator(mode="after")
    def validate_coverage(self) -> "CompanyCorpus":
        ids = [fixture.id for fixture in self.fixtures]
        if len(ids) != len(set(ids)):
            raise ValueError("fixture IDs must be unique")
        profiles = {fixture.coverage_profile for fixture in self.fixtures}
        missing = REQUIRED_PROFILES - profiles
        if missing:
            raise ValueError(f"missing required coverage profiles: {sorted(missing)}")
        return self


class Offering(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    eligible_signals: list[str] = Field(min_length=1)
    discovery_questions: list[str] = Field(min_length=1)


class OfferingCatalog(BaseModel):
    catalog_version: str
    seller_name: str = Field(min_length=1)
    offerings: list[Offering] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ids(self) -> "OfferingCatalog":
        ids = [offering.id for offering in self.offerings]
        if len(ids) != len(set(ids)):
            raise ValueError("offering IDs must be unique")
        return self


def load_corpus(root: Path = ROOT) -> tuple[CompanyCorpus, OfferingCatalog]:
    """Load and cross-validate both committed benchmark inputs."""
    companies = CompanyCorpus.model_validate_json((root / "companies.json").read_text())
    catalog = OfferingCatalog.model_validate_json((root / "seller_offerings.json").read_text())
    catalog_ids = {offering.id for offering in catalog.offerings}
    unknown = {
        offering_id
        for fixture in companies.fixtures
        for offering_id in fixture.allowed_offering_ids
        if offering_id not in catalog_ids
    }
    if unknown:
        raise ValueError(f"fixture refers to unknown offering IDs: {sorted(unknown)}")
    return companies, catalog


def main() -> None:
    companies, catalog = load_corpus()
    print(
        f"Valid benchmark corpus: {len(companies.fixtures)} fixtures, "
        f"{len(catalog.offerings)} seller offerings."
    )


if __name__ == "__main__":
    main()
