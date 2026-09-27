from unittest.mock import Mock

from collector import build_discovery_universe
from models import PageData


def test_discovery_uses_homepage_and_sitemap_links():
    homepage = PageData(
        source_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        internal_links=[
            "https://example.com/services/",
            "https://example.com/blog/",
        ],
    )

    robots_parser = Mock()
    robots_parser.can_fetch.return_value = True

    sitemap_urls = [
        "https://example.com/products/",
    ]

    discovered = build_discovery_universe(
        homepage=homepage,
        sitemap_urls=sitemap_urls,
        robots_parser=robots_parser,
    )

    assert "https://example.com/" in discovered
    assert "https://example.com/services/" in discovered
    assert "https://example.com/blog/" in discovered
    assert "https://example.com/products/" in discovered


if __name__ == "__main__":
    test_discovery_uses_homepage_and_sitemap_links()

    print("collector discovery baseline: OK")