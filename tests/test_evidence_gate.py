from octodig.report_contract import Claim, Source, empty_report
from octodig.services.evidence_gate import verify_report_evidence


def test_model_verified_labels_require_retrieved_support(monkeypatch):
    report = empty_report("run_1", "Example", "https://example.com", "standard")
    report.target.identity_status = "resolved"
    report.sources = [Source(id="s1", url="https://example.com", retrieved_at="2026-01-01T00:00:00Z", provider="test")]
    report.claims = [Claim(id="c1", section="company_overview", statement="We sell cloud software.", classification="verified", source_ids=["s1"]),
                     Claim(id="c2", section="company_overview", statement="Revenue is a billion dollars.", classification="verified", source_ids=["s1"])]
    monkeypatch.setattr("octodig.services.evidence_gate.fetch_public_text", lambda url: (url, "We sell cloud software."))
    verify_report_evidence(report)
    assert report.claims[0].verification_status == "supported"
    assert report.claims[1].classification == "hypothesis"
    assert report.claims[1].verification_status == "unsupported"
    assert any("c2" in gap for gap in report.gaps)
