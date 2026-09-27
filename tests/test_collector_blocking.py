from pathlib import Path
from unittest.mock import Mock, patch

from collector import (
    TargetBlockedError,
    collect_site,
    get_with_retry,
)
from models import PageData


TEST_URL = "https://example.com"


def make_page(
    url: str,
    status_code: int,
) -> PageData:
    return PageData(
        source_url=url,
        final_url=url,
        status_code=status_code,
    )


def test_repeated_429_raises_target_blocked() -> None:
    session = Mock()

    response = Mock()
    response.status_code = 429
    response.headers = {}

    session.get.return_value = response

    with patch(
        "collector.time.sleep"
    ):
        try:
            get_with_retry(
                session,
                TEST_URL,
            )

        except TargetBlockedError as exc:
            assert "TARGET_BLOCKED" in str(exc)

        else:
            raise AssertionError(
                "Expected TargetBlockedError "
                "after repeated HTTP 429"
            )


def test_repeated_403_stops_site_crawl() -> None:
    homepage = make_page(
        TEST_URL,
        200,
    )

    blocked_one = make_page(
        "https://example.com/page-one",
        403,
    )

    blocked_two = make_page(
        "https://example.com/page-two",
        403,
    )

    selected_urls = [
        TEST_URL,
        "https://example.com/page-one",
        "https://example.com/page-two",
        "https://example.com/page-three",
    ]

    saved_file = Mock(
        spec=Path
    )
    saved_file.name = "index.json"

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
            blocked_one,
            blocked_two,
        ],
    ) as mocked_fetch_page, patch(
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
    ), patch(
        "collector.persist_manifest",
    ), patch(
        "collector.remove_stale_page_files",
    ), patch(
        "collector.time.sleep",
    ):

        site_data = collect_site(
            TEST_URL
        )

    assert mocked_fetch_page.call_count == 3

    assert site_data.pages_fetched == 1

    assert any(
        "TARGET_BLOCKED" in error["error"]
        for error in site_data.fetch_errors
    )


if __name__ == "__main__":
    test_repeated_429_raises_target_blocked()
    test_repeated_403_stops_site_crawl()

    print("collector blocking behavior: OK")