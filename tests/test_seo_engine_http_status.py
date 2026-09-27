from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_non_200_status_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/temporarily-moved/",
        final_url="https://example.com/temporarily-moved/",
        status_code=302,
        title="Temporarily moved",
        meta_description="Temporary redirect page",
        h1=[
            "Temporarily moved"
        ],
        canonical="https://example.com/temporarily-moved/",
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

    status_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "http_status_non_200"
    ]

    assert len(
        status_evidence
    ) == 1

    item = status_evidence[0]

    assert item.category == "technical"
    assert item.scope == "page"
    assert item.source_urls == [
        "https://example.com/temporarily-moved/"
    ]
    assert item.observed == {
        "source_url": "https://example.com/temporarily-moved/",
        "final_url": "https://example.com/temporarily-moved/",
        "status_code": 302,
    }
    assert item.method == "deterministic"


if __name__ == "__main__":
    test_non_200_status_generates_search_evidence()

    print(
        "seo engine HTTP status evidence: OK"
    )
