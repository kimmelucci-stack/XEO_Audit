from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_no_internal_links_generates_search_evidence():
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
        canonical="https://example.com/about/",
        internal_links=[],
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

    internal_link_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "no_internal_links"
    ]

    assert len(
        internal_link_evidence
    ) == 1

    item = internal_link_evidence[0]

    assert item.category == "internal_links"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "internal_link_count": 0,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_no_internal_links_generates_search_evidence()

    print(
        "seo engine no internal links evidence: OK"
    )
