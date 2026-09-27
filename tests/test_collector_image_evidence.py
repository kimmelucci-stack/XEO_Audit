from unittest.mock import Mock

from collector import fetch_page


def test_image_evidence_is_collected():
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
            <img
                src="/images/product.jpg"
                alt="Product image"
                width="800"
                height="600"
                loading="lazy"
            >
        </body>
    </html>
    """

    session = Mock()
    session.get.return_value = response

    page = fetch_page(
        session,
        "https://example.com/",
    )

    assert page.image_count == 1
    assert page.images_missing_alt == 0

    assert page.image_evidence == [
        {
            "src": "/images/product.jpg",
            "alt": "Product image",
            "width": "800",
            "height": "600",
            "loading": "lazy",
        }
    ]


if __name__ == "__main__":
    test_image_evidence_is_collected()

    print("collector image evidence: OK")