from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_missing_meta_description_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
        page_type="other",
        title="About",
        meta_description=None,
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[page],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    meta_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "meta_description_missing"
    ]

    assert len(meta_evidence) == 1

    item = meta_evidence[0]

    assert item.category == "metadata"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "meta_description": None,
    }

    assert item.method == "deterministic"


if __name__ == "__main__":
    test_missing_meta_description_generates_search_evidence()

    print(
        "seo engine missing meta description evidence: OK"
    )