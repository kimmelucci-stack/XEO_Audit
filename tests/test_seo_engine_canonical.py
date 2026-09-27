from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_missing_canonical_generates_search_evidence():
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
        canonical=None,
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
        == "canonical_missing"
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
        "canonical": None,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_missing_canonical_generates_search_evidence()

    print(
        "seo engine missing canonical evidence: OK"
    )