from unittest.mock import Mock

from collector import fetch_page


TEST_URL = "https://example.com/page"


def test_redirect_to_external_host_is_rejected():
    response = Mock()
    response.url = "https://external.com/page"
    response.status_code = 200
    response.headers = {
        "Content-Type": "text/html"
    }
    response.history = []
    response.text = "<html><body>Test</body></html>"

    session = Mock()
    session.get.return_value = response

    try:
        fetch_page(
            session,
            TEST_URL,
        )

    except ValueError as exc:
        assert "Redirect outside normalized host" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError for redirect to external host"
        )


if __name__ == "__main__":
    test_redirect_to_external_host_is_rejected()

    print("collector redirect safety: OK")
