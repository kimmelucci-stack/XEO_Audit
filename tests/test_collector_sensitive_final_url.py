from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


HOME = "https://example.com/"
START = "https://example.com/start"
SENSITIVE = "https://example.com/account/"


def test_sensitive_final_url_is_excluded():
    homepage = PageData(
        source_url=HOME,
        final_url=HOME,
        status_code=200,
        page_type="homepage",
    )

    redirected_page = PageData(
        source_url=START,
        final_url=SENSITIVE,
        status_code=200,
        page_type="other",
    )

    selected_urls = [
        HOME,
        START,
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
        return_value=selected_urls.copy(),
    ), patch(
        "collector.persist_page",
    ) as mocked_persist_page, patch(
        "collector.persist_manifest",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(HOME)

    assert site_data.pages_fetched == 1
    assert mocked_persist_page.call_count == 1

    assert any(
        "Final URL excluded by safety policy"
        in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_sensitive_final_url_is_excluded()

    print("collector sensitive final URL: OK")
