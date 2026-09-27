from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


TEST_URL = "https://example.com/"


def test_final_url_blocked_by_robots_is_excluded():
    homepage = PageData(
        source_url=TEST_URL,
        final_url=TEST_URL,
        status_code=200,
        page_type="homepage",
    )

    redirected_page = PageData(
        source_url="https://example.com/start",
        final_url="https://example.com/private/",
        status_code=200,
        page_type="other",
    )

    selected_urls = [
        TEST_URL,
        "https://example.com/start",
    ]

    robots_parser = Mock()

    with patch(
        "collector.fetch_robots_parser",
        return_value=(robots_parser, True),
    ), patch(
        "collector.is_url_allowed",
        side_effect=[
            True,
            True,
            False,
        ],
    ), patch(
        "collector.fetch_page",
        side_effect=[
            homepage,
            redirected_page,
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
    ) as mocked_persist_page, patch(
        "collector.persist_manifest",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(TEST_URL)

    assert len(site_data.pages) == 1

    assert mocked_persist_page.call_count == 1

    assert any(
        "Final URL blocked by robots.txt" in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_final_url_blocked_by_robots_is_excluded()

    print("collector final URL safety: OK")