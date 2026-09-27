from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


TEST_URL = "https://example.com/"


def test_storage_error_keeps_page_in_memory():
    homepage = PageData(
        source_url=TEST_URL,
        final_url=TEST_URL,
        status_code=200,
        page_type="homepage",
    )

    saved_manifest = Mock(spec=Path)

    with patch(
        "collector.fetch_robots_parser",
        return_value=(Mock(), True),
    ), patch(
        "collector.is_url_allowed",
        return_value=True,
    ), patch(
        "collector.fetch_page",
        return_value=homepage,
    ), patch(
        "collector.discover_sitemap_urls",
        return_value=([], []),
    ), patch(
        "collector.build_discovery_universe",
        return_value=[TEST_URL],
    ), patch(
        "collector.select_representative_sample",
        return_value=[TEST_URL],
    ), patch(
        "collector.persist_page",
        side_effect=OSError("disk write failed"),
    ), patch(
        "collector.persist_manifest",
        return_value=saved_manifest,
    ), patch(
        "collector.remove_stale_page_files",
    ):

        site_data = collect_site(TEST_URL)

    assert site_data.persistence_complete is False

    assert site_data.pages_fetched == 1

    assert len(site_data.pages) == 1

    assert site_data.pages[0].final_url == TEST_URL

    assert any(
        "STORAGE_ERROR" in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_storage_error_keeps_page_in_memory()

    print("collector storage fail-soft: OK")