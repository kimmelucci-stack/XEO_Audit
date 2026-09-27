from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_missing_title_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
        page_type="other",
        title=None,
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[page],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    title_evidence = [
        item
        for item in evidence
        if item.evidence_id == "title_missing"
    ]

    assert len(title_evidence) == 1

    item = title_evidence[0]

    assert item.category == "metadata"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "title": None,
    }

    assert item.method == "deterministic"


if __name__ == "__main__":
    test_missing_title_generates_search_evidence()

    print(
        "seo engine missing title evidence: OK"
    )