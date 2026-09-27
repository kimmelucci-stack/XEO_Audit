from unittest.mock import Mock

from collector import fetch_page, normalize_url


def test_normalize_url_removes_fragment():
    assert (
        normalize_url(
            "https://Example.com/page#section-one"
        )
        == "https://example.com/page"
    )


def test_fetch_page_deduplicates_fragment_links():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200
    response.headers = {
        "Content-Type": "text/html"
    }
    response.history = []
    response.text = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <a href="/page#one">One</a>
            <a href="/page#two">Two</a>
            <a href="/page">Three</a>
        </body>
    </html>
    """

    session = Mock()
    session.get.return_value = response

    page = fetch_page(
        session,
        "https://example.com/"
    )

    assert page.internal_links == [
        "https://example.com/page"
    ]


if __name__ == "__main__":
    test_normalize_url_removes_fragment()
    test_fetch_page_deduplicates_fragment_links()

    print(
        "collector URL normalization and dedup: OK"
    )