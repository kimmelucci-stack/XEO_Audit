from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_redirect_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/old-page/",
        final_url="https://example.com/new-page/",
        status_code=200,
        redirect_history=[
            "https://example.com/old-page/"
        ],
        title="New page",
        meta_description="New page on example.com",
        h1=[
            "New page"
        ],
        canonical="https://example.com/new-page/",
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

    redirect_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "redirect_detected"
    ]

    assert len(
        redirect_evidence
    ) == 1

    item = redirect_evidence[0]

    assert item.category == "technical"
    assert item.scope == "page"
    assert item.source_urls == [
        "https://example.com/new-page/"
    ]
    assert item.observed == {
        "source_url": "https://example.com/old-page/",
        "final_url": "https://example.com/new-page/",
        "redirect_history": [
            "https://example.com/old-page/"
        ],
        "redirect_count": 1,
    }
    assert item.method == "deterministic"


if __name__ == "__main__":
    test_redirect_generates_search_evidence()

    print(
        "seo engine redirect evidence: OK"
    )
