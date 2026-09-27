from unittest.mock import patch

from collector import collect_site


class DenyAllRobotsParser:
    def can_fetch(
        self,
        user_agent: str,
        url: str,
    ) -> bool:
        return False


def test_homepage_blocked_by_robots_is_not_fetched():
    robots_parser = DenyAllRobotsParser()

    with patch(
        "collector.fetch_robots_parser",
        return_value=(robots_parser, True),
    ), patch(
        "collector.fetch_page"
    ) as mocked_fetch_page:

        try:
            collect_site(
                "https://example.com"
            )

        except PermissionError as exc:
            assert "Homepage blocked by robots.txt" in str(exc)

        else:
            raise AssertionError(
                "Expected PermissionError when homepage "
                "is blocked by robots.txt"
            )

        mocked_fetch_page.assert_not_called()


if __name__ == "__main__":
    test_homepage_blocked_by_robots_is_not_fetched()
    print("collector robots gate: OK")