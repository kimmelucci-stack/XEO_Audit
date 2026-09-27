from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_x_robots_tag_generates_search_evidence():
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
        internal_links=[
            "https://example.com/"
        ],
        x_robots_tag="noarchive",
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

    x_robots_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "x_robots_tag_detected"
    ]

    assert len(
        x_robots_evidence
    ) == 1

    item = x_robots_evidence[0]

    assert item.category == "indexability"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "x_robots_tag": "noarchive",
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_x_robots_tag_generates_search_evidence()

    print(
        "seo engine x-robots-tag evidence: OK"
    )