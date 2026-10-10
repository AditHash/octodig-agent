from octodig.api import slugify
from octodig.schemas import OfferingCreate


def test_offering_contract_allows_reviewed_catalog_fields() -> None:
    offering = OfferingCreate(
        name="Customer support automation",
        description="Improve approved support workflows.",
        capabilities=["workflow design"],
        business_outcomes=["faster response"],
        approved=True,
    )
    assert offering.approved is True
    assert slugify(offering.name) == "customer-support-automation"
