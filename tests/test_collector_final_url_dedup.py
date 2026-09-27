from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


HOME = "https://example.com/"
SOURCE_A = "https://example.com/source-a"
SOURCE_B = "https://example.com/source-b"
FINAL = "https://example.com/final/"


def test_multiple_source_urls_share_one_final_page():
    homepage = PageData(
        source_url=HOME,
        final_url=HOME,
        status_code=200,
        page_type="homepage",
    )

    page_a = PageData(
        source_url=SOURCE_A,
        final_url=FINAL,
        status_code=200,
        page_type="other",
    )

    page_b = PageData(
        source_url=SOURCE_B,
        final_url=FINAL,
        status_code=200,
        page_type="other",
    )

    selected_urls = [
        HOME,
        SOURCE_A,
        SOURCE_B,
    ]

    homepage_file = Mock(spec=Path)
    homepage_file.name = "index.json"

    final_file = Mock(spec=Path)
    final_file.name = "final.json"

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
            page_a,
            page_b,
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
        side_effect=[
            homepage_file,
            final_file,
        ],
    ) as mocked_persist_page, patch(
        "collector.persist_manifest",
    ) as mocked_persist_manifest, patch(
        "collector.remove_stale_page_files",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(HOME)

    assert site_data.pages_fetched == 3

    assert len(site_data.pages) == 2

    assert {
        page.final_url
        for page in site_data.pages
    } == {
        HOME,
        FINAL,
    }

    assert mocked_persist_page.call_count == 2

    manifest_call = (
        mocked_persist_manifest.call_args.kwargs
    )

    manifest_pages = manifest_call[
        "page_files"
    ]

    assert len(manifest_pages) == 3

    assert (
        manifest_pages[SOURCE_A]["filename"]
        == "final.json"
    )

    assert (
        manifest_pages[SOURCE_B]["filename"]
        == "final.json"
    )

    assert (
        manifest_call["pages_fetched"]
        == 3
    )


if __name__ == "__main__":
    test_multiple_source_urls_share_one_final_page()

    print(
        "collector final URL dedup: OK"
    )