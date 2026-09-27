from unittest.mock import Mock, patch

import requests

from collector import get_with_retry


TEST_URL = "https://example.com/test"


def make_response(
    status_code: int,
    headers: dict | None = None,
) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}

    return response


def test_429_retries_then_succeeds() -> None:
    session = Mock()

    rate_limited = make_response(
        429,
        {"Retry-After": "1"},
    )
    success = make_response(200)

    session.get.side_effect = [
        rate_limited,
        success,
    ]

    with patch("collector.time.sleep") as mocked_sleep:
        response = get_with_retry(
            session,
            TEST_URL,
        )

    assert response.status_code == 200
    assert session.get.call_count == 2
    mocked_sleep.assert_called_once_with(1.0)


def test_500_retries_then_succeeds() -> None:
    session = Mock()

    server_error = make_response(500)
    success = make_response(200)

    session.get.side_effect = [
        server_error,
        success,
    ]

    with patch("collector.time.sleep") as mocked_sleep:
        response = get_with_retry(
            session,
            TEST_URL,
        )

    assert response.status_code == 200
    assert session.get.call_count == 2
    mocked_sleep.assert_called_once_with(1)


def test_network_error_retries_then_succeeds() -> None:
    session = Mock()

    success = make_response(200)

    session.get.side_effect = [
        requests.ConnectionError(
            "temporary connection failure"
        ),
        success,
    ]

    with patch("collector.time.sleep") as mocked_sleep:
        response = get_with_retry(
            session,
            TEST_URL,
        )

    assert response.status_code == 200
    assert session.get.call_count == 2
    mocked_sleep.assert_called_once_with(1)


def test_403_does_not_retry() -> None:
    session = Mock()

    forbidden = make_response(403)
    session.get.return_value = forbidden

    with patch("collector.time.sleep") as mocked_sleep:
        response = get_with_retry(
            session,
            TEST_URL,
        )

    assert response.status_code == 403
    assert session.get.call_count == 1
    mocked_sleep.assert_not_called()


if __name__ == "__main__":
    test_429_retries_then_succeeds()
    test_500_retries_then_succeeds()
    test_network_error_retries_then_succeeds()
    test_403_does_not_retry()

    print("collector retry behavior: OK")