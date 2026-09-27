from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_internal_links_missing_anchor_text_generate_evidence():
    page = PageData(
        source_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        title="Home",
        meta_description="Home page",
        h1=[
            "Home"
        ],
        canonical="https://example.com/",
        internal_links=[
            "https://example.com/services/",
            "https://example.com/about/",
        ],
        internal_link_anchors=[
            {
                "url": "https://example.com/services/",
                "anchor_text": "",
            },
            {
                "url": "https://example.com/about/",
                "anchor_text": "About",
            },
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

    anchor_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "internal_links_missing_anchor_text"
    ]

    assert len(
        anchor_evidence
    ) == 1

    item = anchor_evidence[0]

    assert item.category == "internal_links"
    assert item.scope == "page"
    assert item.source_urls == [
        "https://example.com/"
    ]
    assert item.observed == {
        "count": 1,
        "links": [
            {
                "url": "https://example.com/services/",
                "anchor_text": "",
            }
        ],
    }
    assert item.method == "deterministic"


if __name__ == "__main__":
    test_internal_links_missing_anchor_text_generate_evidence()

    print(
        "seo engine internal link anchor text evidence: OK"
    )
