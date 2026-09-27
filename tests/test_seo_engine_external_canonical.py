from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_external_canonical_generates_search_evidence():
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
        canonical="https://other-domain.com/about/",
        internal_links=[
            "https://example.com/"
        ],
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

    external_canonical_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "canonical_external"
    ]

    assert len(
        external_canonical_evidence
    ) == 1

    item = external_canonical_evidence[0]

    assert item.category == "canonical"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "final_url": "https://example.com/about/",
        "canonical": "https://other-domain.com/about/",
    }

    assert item.method == "deterministic"


if __name__ == "__main__":
    test_external_canonical_generates_search_evidence()

    print(
        "seo engine external canonical evidence: OK"
    )