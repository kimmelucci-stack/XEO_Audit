from providers.google import GooglePerformanceProvider


class FakeResponse:
    def __init__(
        self,
        status_code,
        payload,
    ):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.get_calls = []
        self.post_calls = []

    def get(
        self,
        url,
        params,
        timeout,
    ):
        self.get_calls.append({
            "url": url,
            "params": params,
            "timeout": timeout,
        })

        return FakeResponse(
            200,
            {
                "lighthouseResult": {
                    "categories": {
                        "performance": {
                            "score": 0.82,
                        }
                    },
                    "audits": {
                        "first-contentful-paint": {
                            "numericValue": 1200,
                            "displayValue": "1.2 s",
                            "score": 0.9,
                        },
                        "largest-contentful-paint": {
                            "numericValue": 2400,
                            "displayValue": "2.4 s",
                            "score": 0.8,
                        },
                        "unused-javascript": {
                            "title": "Reduce unused JavaScript",
                            "score": 0.5,
                            "displayValue": "120 KiB",
                            "details": {
                                "type": "opportunity",
                            },
                        },
                    },
                }
            },
        )

    def post(
        self,
        url,
        params,
        json,
        timeout,
    ):
        self.post_calls.append({
            "url": url,
            "params": params,
            "json": json,
            "timeout": timeout,
        })

        return FakeResponse(
            200,
            {
                "record": {
                    "key": {
                        "url": "https://example.com/",
                    },
                    "metrics": {
                        "largest_contentful_paint": {
                            "percentiles": {
                                "p75": 2500,
                            },
                            "histogram": [
                                {
                                    "start": 0,
                                    "end": 2500,
                                    "density": 0.75,
                                }
                            ],
                        }
                    },
                }
            },
        )


def test_pagespeed_provider_parses_lighthouse_results():
    session = FakeSession()
    provider = GooglePerformanceProvider(
        api_key="test-key",
        session=session,
        timeout_seconds=3,
    )

    result = provider.run_pagespeed(
        "https://example.com/",
        "mobile",
    )

    assert result["status"] == "available"
    assert result["score"] == 0.82
    assert result["metrics"]["first_contentful_paint"] == {
        "numeric_value": 1200,
        "display_value": "1.2 s",
        "score": 0.9,
    }
    assert result["diagnostics"] == [
        {
            "id": "unused-javascript",
            "title": "Reduce unused JavaScript",
            "score": 0.5,
            "display_value": "120 KiB",
        }
    ]
    assert session.get_calls[0]["params"]["strategy"] == "mobile"
    assert session.get_calls[0]["params"]["key"] == "test-key"


def test_crux_provider_parses_field_metrics():
    session = FakeSession()
    provider = GooglePerformanceProvider(
        api_key="test-key",
        session=session,
        timeout_seconds=3,
    )

    result = provider.fetch_crux(
        "https://example.com/",
        "desktop",
    )

    assert result["status"] == "available"
    assert result["scope"] == "url"
    assert result["metrics"]["largest_contentful_paint"] == {
        "percentiles": {
            "p75": 2500,
        },
        "histogram": [
            {
                "start": 0,
                "end": 2500,
                "density": 0.75,
            }
        ],
    }
    assert session.post_calls[0]["json"]["formFactor"] == "DESKTOP"
    assert session.post_calls[0]["params"]["key"] == "test-key"


def test_crux_provider_is_unavailable_without_api_key():
    provider = GooglePerformanceProvider(
        api_key="",
        session=FakeSession(),
    )

    result = provider.fetch_crux(
        "https://example.com/",
        "mobile",
    )

    assert result == {
        "status": "unavailable",
        "scope": None,
        "metrics": {},
        "error": "UNAVAILABLE_DATA: Google API key not configured",
    }


if __name__ == "__main__":
    test_pagespeed_provider_parses_lighthouse_results()
    test_crux_provider_parses_field_metrics()
    test_crux_provider_is_unavailable_without_api_key()

    print(
        "google provider: OK"
    )
