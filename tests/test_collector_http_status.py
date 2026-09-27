from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


TEST_URL = "https://example.com/"
MISSING_URL = "https://example.com/missing"


def test_404_is_excluded_from_eligible_pages():
    homepage = PageData(
        source_url=TEST_URL,
        final_url=TEST_URL,
        status_code=200,
        page_type="homepage",
    )

    missing_page = PageData(
        source_url=MISSING_URL,
        final_url=MISSING_URL,
        status_code=404,
        page_type="other",
    )

    saved_file = Mock(spec=Path)
    saved_file.name = "index.json"

    selected_urls = [
        TEST_URL,
        MISSING_URL,
    ]

    with patch(
        "collector.fetch_robots_parser",
        return_value=(Mock(), True),
    ), patch(
        "collector.is_url_allowed",
        return_value=True,
    ), patch(
        "collector.fetch_page",
        side_effect=[
            homepage,
            missing_page,
        ],
    ), patch(
        "collector.discover_sitemap_urls",
        return_value=([], []),
    ), patch(
        "collector.build_discovery_universe",
        return_value=selected_urls,
    ), patch(
        "collector.select_representative_sample",
        return_value=selected_urls,
    ), patch(
        "collector.persist_page",
        return_value=saved_file,
    ) as mocked_persist_page, patch(
        "collector.persist_manifest",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(TEST_URL)

    assert site_data.pages_fetched == 1
    assert len(site_data.pages) == 1
    assert mocked_persist_page.call_count == 1

    assert any(
        "HTTP 404" in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_404_is_excluded_from_eligible_pages()

    print("collector HTTP status eligibility: OK")