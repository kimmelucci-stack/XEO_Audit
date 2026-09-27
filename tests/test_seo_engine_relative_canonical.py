from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_relative_self_canonical_does_not_generate_mismatch():
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
        canonical="/about/",
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

    mismatch_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "canonical_mismatch"
    ]

    external_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "canonical_external"
    ]

    assert mismatch_evidence == []
    assert external_evidence == []


if __name__ == "__main__":
    test_relative_self_canonical_does_not_generate_mismatch()

    print(
        "seo engine relative canonical normalization: OK"
    )