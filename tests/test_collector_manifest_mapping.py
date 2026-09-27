from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


SOURCE_URL = "https://example.com/"
FINAL_URL = "https://example.com/home/"


def test_manifest_tracks_source_final_and_filename():
    homepage = PageData(
        source_url=SOURCE_URL,
        final_url=FINAL_URL,
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
        return_value=[FINAL_URL],
    ), patch(
        "collector.select_representative_sample",
        return_value=[FINAL_URL],
    ), patch(
        "collector.persist_page",
        return_value=saved_file,
    ), patch(
        "collector.persist_manifest",
    ) as mocked_manifest, patch(
        "collector.remove_stale_page_files",
    ):

        collect_site(SOURCE_URL)

    page_files = mocked_manifest.call_args.kwargs[
        "page_files"
    ]

    assert page_files == {
        SOURCE_URL: {
            "source_url": SOURCE_URL,
            "final_url": FINAL_URL,
            "filename": "index.json",
        }
    }


if __name__ == "__main__":
    test_manifest_tracks_source_final_and_filename()

    print(
        "collector manifest mapping: OK"
    )