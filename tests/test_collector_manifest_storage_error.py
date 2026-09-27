from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


TEST_URL = "https://example.com/"


def test_manifest_storage_error_keeps_site_data():
    homepage = PageData(
        source_url=TEST_URL,
        final_url=TEST_URL,
        status_code=200,
        page_type="homepage",
    )

    saved_file = Mock(spec=Path)
    saved_file.name = "index.json"

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
        return_value=saved_file,
    ), patch(
        "collector.persist_manifest",
        side_effect=OSError(
            "manifest disk error"
        ),
    ), patch(
        "collector.remove_stale_page_files",
    ):

        site_data = collect_site(
            TEST_URL
        )

    assert site_data.pages_fetched == 1

    assert len(
        site_data.pages
    ) == 1

    assert (
        site_data.persistence_complete
        is False
    )

    assert any(
        (
            "STORAGE_ERROR: "
            "manifest write failed"
        )
        in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_manifest_storage_error_keeps_site_data()

    print(
        "collector manifest storage fail-soft: OK"
    )