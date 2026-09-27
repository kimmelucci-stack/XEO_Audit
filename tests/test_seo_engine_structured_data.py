from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_structured_data_generates_search_evidence():
    page = PageData(
        source_url="https://example.com/product/",
        final_url="https://example.com/product/",
        status_code=200,
        page_type="commercial",
        title="Product",
        meta_description="Product description",
        h1=[
            "Product"
        ],
        canonical="https://example.com/product/",
        internal_links=[
            "https://example.com/"
        ],
        structured_data_types=[
            "Product",
            "BreadcrumbList",
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

    structured_data_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "structured_data_detected"
    ]

    assert len(
        structured_data_evidence
    ) == 1

    item = structured_data_evidence[0]

    assert item.category == "structured_data"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/product/"
    ]

    assert item.observed == {
        "structured_data_types": [
            "Product",
            "BreadcrumbList",
        ],
        "count": 2,
    }

    assert (
        item.method
        == "deterministic"
    )


if __name__ == "__main__":
    test_structured_data_generates_search_evidence()

    print(
        "seo engine structured data evidence: OK"
    )