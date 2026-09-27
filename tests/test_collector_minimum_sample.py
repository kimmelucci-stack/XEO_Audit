from pathlib import Path
from unittest.mock import Mock, patch

from collector import collect_site
from models import PageData


HOME = "https://example.com/"


def make_url(index: int) -> str:
    return f"https://example.com/page-{index}/"


def make_page(
    source_url: str,
    status_code: int,
) -> PageData:
    return PageData(
        source_url=source_url,
        final_url=source_url,
        status_code=status_code,
        page_type="other",
    )


def test_collector_reaches_minimum_when_valid_reserve_exists():
    discovery_urls = [
        HOME,
        *[
            make_url(index)
            for index in range(1, 60)
        ],
    ]

    selected_urls = discovery_urls[:50]

    homepage = make_page(
        HOME,
        200,
    )
    homepage.page_type = "homepage"

    def fake_fetch_page(
        session,
        url,
    ):
        if url == HOME:
            return homepage

        index = int(
            url.rstrip("/")
            .split("-")[-1]
        )

        # First 20 pages in the selected sample
        # are valid:
        #
        # HOME + page-1 ... page-19 = 20
        if index <= 19:
            return make_page(
                url,
                200,
            )

        # page-20 ... page-49 are invalid.
        if index <= 49:
            return make_page(
                url,
                404,
            )

        # page-50 ... page-59 are valid reserve
        # candidates in discovery_universe.
        return make_page(
            url,
            200,
        )

    def fake_persist_page(
        page,
    ):
        saved_file = Mock(
            spec=Path
        )

        saved_file.name = (
            page.final_url
            .rstrip("/")
            .split("/")[-1]
            + ".json"
        )

        if page.final_url == HOME:
            saved_file.name = "index.json"

        return saved_file

    with patch(
        "collector.fetch_robots_parser",
        return_value=(Mock(), True),
    ), patch(
        "collector.is_url_allowed",
        return_value=True,
    ), patch(
        "collector.fetch_page",
        side_effect=fake_fetch_page,
    ), patch(
        "collector.discover_sitemap_urls",
        return_value=([], []),
    ), patch(
        "collector.build_discovery_universe",
        return_value=discovery_urls,
    ), patch(
        "collector.select_representative_sample",
        return_value=selected_urls.copy(),
    ), patch(
        "collector.persist_page",
        side_effect=fake_persist_page,
    ), patch(
        "collector.persist_manifest",
    ), patch(
        "collector.remove_stale_page_files",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(
            HOME
        )

    print(
        f"Discovered: "
        f"{site_data.pages_discovered}"
    )

    print(
        f"Selected: "
        f"{site_data.pages_selected}"
    )

    print(
        f"Fetched: "
        f"{site_data.pages_fetched}"
    )

    print(
        f"Unique pages: "
        f"{len(site_data.pages)}"
    )

    assert (
        site_data.pages_discovered
        >= 25
    )

    assert (
        len(site_data.pages)
        >= 25
    )


if __name__ == "__main__":
    test_collector_reaches_minimum_when_valid_reserve_exists()

    print(
        "collector minimum sample: OK"
    )