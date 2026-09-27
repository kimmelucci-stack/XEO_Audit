from models import PageData, SiteData
from performance_engine import select_performance_sample


def test_performance_sample_selects_representative_urls():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            PageData(
                source_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                page_type="homepage",
            ),
            PageData(
                source_url="https://example.com/services/",
                final_url="https://example.com/services/",
                status_code=200,
                page_type="commercial",
            ),
            PageData(
                source_url="https://example.com/blog/",
                final_url="https://example.com/blog/",
                status_code=200,
                page_type="editorial",
            ),
            PageData(
                source_url="https://example.com/about/",
                final_url="https://example.com/about/",
                status_code=200,
                page_type="unclassified",
            ),
            PageData(
                source_url="https://example.com/extra/",
                final_url="https://example.com/extra/",
                status_code=200,
                page_type="unclassified",
            ),
        ],
    )

    sampled_urls = select_performance_sample(
        site_data
    )

    assert sampled_urls == [
        "https://example.com/",
        "https://example.com/services/",
        "https://example.com/blog/",
        "https://example.com/about/",
    ]


if __name__ == "__main__":
    test_performance_sample_selects_representative_urls()

    print(
        "performance sample selection: OK"
    )
