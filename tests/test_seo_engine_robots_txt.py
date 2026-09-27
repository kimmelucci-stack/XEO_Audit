from models import SiteData
from seo_engine import analyze_search_readiness


def test_unavailable_robots_txt_generates_search_evidence():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        robots_txt_url="https://example.com/robots.txt",
        robots_txt_available=False,
        sitemap_files=[
            "https://example.com/sitemap.xml"
        ],
    )

    evidence = analyze_search_readiness(
        site_data
    )

    robots_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "robots_txt_unavailable"
    ]

    assert len(
        robots_evidence
    ) == 1

    item = robots_evidence[0]

    assert item.category == "technical"
    assert item.scope == "site"
    assert item.source_urls == [
        "https://example.com/robots.txt"
    ]
    assert item.observed == {
        "robots_txt_url": "https://example.com/robots.txt",
        "robots_txt_available": False,
    }
    assert item.method == "deterministic"


if __name__ == "__main__":
    test_unavailable_robots_txt_generates_search_evidence()

    print(
        "seo engine robots.txt evidence: OK"
    )
