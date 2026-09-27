from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


HOME = "https://example.com/"
START = "https://example.com/blog/start"
DEEP = "https://example.com/services/deep"


def test_internal_links_discovered_during_crawl_are_added():
    homepage = PageData(
        source_url=HOME,
        final_url=HOME,
        status_code=200,
        page_type="homepage",
        internal_links=[START],
    )

    start_page = PageData(
        source_url=START,
        final_url=START,
        status_code=200,
        page_type="editorial",
        internal_links=[DEEP],
    )

    deep_page = PageData(
        source_url=DEEP,
        final_url=DEEP,
        status_code=200,
        page_type="commercial",
        internal_links=[],
    )

    saved_file = Mock(spec=Path)
    saved_file.name = "page.json"

    initial_selection = [
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
            start_page,
            deep_page,
        ],
    ) as mocked_fetch_page, patch(
        "collector.discover_sitemap_urls",
        return_value=([], []),
    ), patch(
        "collector.build_discovery_universe",
        return_value=initial_selection,
    ), patch(
        "collector.select_representative_sample",
        return_value=initial_selection.copy(),
    ), patch(
        "collector.persist_page",
        return_value=saved_file,
    ), patch(
        "collector.persist_manifest",
    ), patch(
        "collector.remove_stale_page_files",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(HOME)

    assert mocked_fetch_page.call_count == 3

    assert site_data.pages_fetched == 3

    assert any(
        page.final_url == DEEP
        for page in site_data.pages
    )

    assert HOME in site_data.internal_link_graph
    assert START in site_data.internal_link_graph
    assert DEEP in site_data.internal_link_graph

    assert (
        site_data.internal_link_graph[START]
        == [DEEP]
    )


if __name__ == "__main__":
    test_internal_links_discovered_during_crawl_are_added()

    print(
        "collector progressive discovery: OK"
    )