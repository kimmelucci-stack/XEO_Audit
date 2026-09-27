from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_duplicate_title_generates_site_evidence():
    page_a = PageData(
        source_url="https://example.com/page-a/",
        final_url="https://example.com/page-a/",
        status_code=200,
        page_type="other",
        title="Same Title",
        meta_description="Page A",
        h1=["Page A"],
        canonical="https://example.com/page-a/",
    )

    page_b = PageData(
        source_url="https://example.com/page-b/",
        final_url="https://example.com/page-b/",
        status_code=200,
        page_type="other",
        title="Same Title",
        meta_description="Page B",
        h1=["Page B"],
        canonical="https://example.com/page-b/",
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            page_a,
            page_b,
        ],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    duplicate_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "duplicate_title"
    ]

    assert len(
        duplicate_evidence
    ) == 1

    item = duplicate_evidence[0]

    assert item.category == "metadata"
    assert item.scope == "site"

    assert item.source_urls == [
        "https://example.com/page-a/",
        "https://example.com/page-b/",
    ]

    assert item.observed == {
        "title": "Same Title",
        "count": 2,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_duplicate_title_generates_site_evidence()

    print(
        "seo engine duplicate title evidence: OK"
    )