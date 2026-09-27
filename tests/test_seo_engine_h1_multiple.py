from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_multiple_h1_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
        page_type="other",
        title="About",
        meta_description="About example.com",
        h1=[
            "About",
            "Our Company",
        ],
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[page],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    h1_evidence = [
        item
        for item in evidence
        if item.evidence_id == "h1_multiple"
    ]

    assert len(h1_evidence) == 1

    item = h1_evidence[0]

    assert item.category == "headings"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "h1": [
            "About",
            "Our Company",
        ],
        "count": 2,
    }

    assert item.method == "deterministic"


if __name__ == "__main__":
    test_multiple_h1_generates_search_evidence()

    print(
        "seo engine multiple h1 evidence: OK"
    )
