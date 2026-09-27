from unittest.mock import Mock

from collector import fetch_page


def test_internal_link_anchor_text_is_collected():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200
    response.headers = {
        "Content-Type": "text/html"
    }
    response.history = []
    response.text = """
    <html>
        <body>
            <a href="/services/seo">
                SEO Audit
            </a>
        </body>
    </html>
    """

    session = Mock()
    session.get.return_value = response

    page = fetch_page(
        session,
        "https://example.com/",
    )

    print(page.internal_links)
    print(page.internal_link_anchors)

    assert page.internal_links == [
        "https://example.com/services/seo"
    ]

    assert page.internal_link_anchors == [
        {
            "url": "https://example.com/services/seo",
            "anchor_text": "SEO Audit",
        }
    ]


if __name__ == "__main__":
    test_internal_link_anchor_text_is_collected()

    print("collector anchor text: OK")