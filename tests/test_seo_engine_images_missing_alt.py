from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_images_missing_alt_generates_search_evidence():
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
        image_count=5,
        images_missing_alt=2,
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

    image_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "images_missing_alt"
    ]

    assert len(
        image_evidence
    ) == 1

    item = image_evidence[0]

    assert item.category == "images"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/about/"
    ]

    assert item.observed == {
        "image_count": 5,
        "images_missing_alt": 2,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_images_missing_alt_generates_search_evidence()

    print(
        "seo engine images missing alt evidence: OK"
    )