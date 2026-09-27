from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_nofollow_generates_search_evidence():
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
        robots_nofollow=True,
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

    nofollow_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "nofollow_detected"
    ]

    assert len(
        nofollow_evidence
    ) == 1

    item = nofollow_evidence[0]

    assert item.category == "indexability"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "robots_nofollow": True,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_nofollow_generates_search_evidence()

    print(
        "seo engine nofollow evidence: OK"
    )