from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_no_observed_inbound_links_generates_heuristic_evidence():
    homepage = PageData(
        source_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        page_type="homepage",
        title="Home",
        meta_description="Homepage",
        h1=["Home"],
        canonical="https://example.com/",
        internal_links=[
            "https://example.com/about/"
        ],
    )

    about = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
        page_type="other",
        title="About",
        meta_description="About",
        h1=["About"],
        canonical="https://example.com/about/",
        internal_links=[
            "https://example.com/"
        ],
    )

    isolated = PageData(
        source_url="https://example.com/isolated/",
        final_url="https://example.com/isolated/",
        status_code=200,
        page_type="other",
        title="Isolated",
        meta_description="Isolated page",
        h1=["Isolated"],
        canonical="https://example.com/isolated/",
        internal_links=[
            "https://example.com/"
        ],
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            homepage,
            about,
            isolated,
        ],
        internal_link_graph={
            "https://example.com/": [
                "https://example.com/about/"
            ],
            "https://example.com/about/": [
                "https://example.com/"
            ],
            "https://example.com/isolated/": [
                "https://example.com/"
            ],
        },
    )

    evidence = analyze_search_readiness(
        site_data
    )

    inbound_evidence = [
        item
        for item in evidence
        if item.evidence_id
        == "no_observed_inbound_links"
    ]

    assert len(
        inbound_evidence
    ) == 1

    item = inbound_evidence[0]

    assert item.category == "internal_links"
    assert item.scope == "page"

    assert item.source_urls == [
        "https://example.com/isolated/"
    ]

    assert item.observed == {
        "observed_inbound_link_count": 0,
    }

    assert item.method == "heuristic"


if __name__ == "__main__":
    test_no_observed_inbound_links_generates_heuristic_evidence()

    print(
        "seo engine observed inbound links heuristic: OK"
    )