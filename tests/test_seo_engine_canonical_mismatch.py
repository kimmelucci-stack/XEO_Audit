from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_canonical_mismatch_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
        page_type="other",
        title="About",
        meta_description="About example.com",
        h1=[
            "About"
        ],
        canonical="https://example.com/company/",
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            page
        ],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    canonical_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "canonical_mismatch"
    ]

    assert len(
        canonical_evidence
    ) == 1

    item = canonical_evidence[0]

    assert item.category == "canonical"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "final_url": "https://example.com/about/",
        "canonical": "https://example.com/company/",
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_canonical_mismatch_generates_search_evidence()

    print(
        "seo engine canonical mismatch evidence: OK"
    )