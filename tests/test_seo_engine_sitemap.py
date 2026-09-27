from models import SiteData
from seo_engine import analyze_search_readiness


def test_detected_sitemap_generates_search_evidence():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        robots_txt_available=True,
        sitemap_files=[
            "https://example.com/sitemap.xml"
        ],
        sitemap_page_urls=[
            "https://example.com/",
            "https://example.com/about/",
        ],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    sitemap_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "sitemap_detected"
    ]

    assert len(
        sitemap_evidence
    ) == 1

    item = sitemap_evidence[0]

    assert item.category == "technical"
    assert item.scope == "site"
    assert item.source_urls == [
        "https://example.com/sitemap.xml"
    ]
    assert item.observed == {
        "sitemap_files": [
            "https://example.com/sitemap.xml"
        ],
        "sitemap_file_count": 1,
        "sitemap_page_url_count": 2,
    }
    assert item.method == "deterministic"


def test_unavailable_sitemap_generates_search_evidence():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        robots_txt_available=True,
        sitemap_files=[],
        sitemap_page_urls=[],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    sitemap_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "sitemap_unavailable"
    ]

    assert len(
        sitemap_evidence
    ) == 1

    item = sitemap_evidence[0]

    assert item.category == "technical"
    assert item.scope == "site"
    assert item.source_urls == []
    assert item.observed == {
        "sitemap_files": [],
        "sitemap_page_url_count": 0,
    }
    assert item.method == "deterministic"


if __name__ == "__main__":
    test_detected_sitemap_generates_search_evidence()
    test_unavailable_sitemap_generates_search_evidence()

    print(
        "seo engine sitemap evidence: OK"
    )
