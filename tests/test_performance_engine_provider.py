from models import PageData, SiteData
from performance_engine import analyze_web_performance


class FakeGoogleProvider:
    def __init__(self):
        self.crux_calls = []
        self.pagespeed_calls = []

    def fetch_crux(
        self,
        url: str,
        device: str,
    ) -> dict[str, object]:
        self.crux_calls.append(
            (
                url,
                device,
            )
        )

        return {
            "status": "unavailable",
            "scope": None,
            "metrics": {},
            "error": "UNAVAILABLE_DATA: insufficient CrUX data",
        }

    def run_pagespeed(
        self,
        url: str,
        device: str,
    ) -> dict[str, object]:
        self.pagespeed_calls.append(
            (
                url,
                device,
            )
        )

        return {
            "status": "available",
            "score": 0.91,
            "metrics": {
                "first_contentful_paint": 1200,
            },
            "diagnostics": [
                {
                    "id": "unused-javascript",
                    "title": "Reduce unused JavaScript",
                }
            ],
        }


def test_performance_engine_uses_provider_and_preserves_device():
    provider = FakeGoogleProvider()

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            PageData(
                source_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                page_type="homepage",
            )
        ],
    )

    performance_data = analyze_web_performance(
        site_data,
        device="desktop",
        provider=provider,
    )

    assert provider.crux_calls == [
        (
            "https://example.com/",
            "desktop",
        )
    ]

    assert provider.pagespeed_calls == [
        (
            "https://example.com/",
            "desktop",
        )
    ]

    assert performance_data.device == "desktop"
    assert performance_data.sampled_urls == [
        "https://example.com/"
    ]
    assert performance_data.field_data_available is False
    assert performance_data.lab_data_available is True
    assert performance_data.status == "partial"

    page = performance_data.pages[0]

    assert page.crux_status == "unavailable"
    assert page.lighthouse_status == "available"
    assert page.lighthouse_score == 0.91
    assert page.lighthouse_metrics == {
        "first_contentful_paint": 1200,
    }
    assert page.errors == [
        {
            "source": "crux",
            "error": "UNAVAILABLE_DATA: insufficient CrUX data",
        }
    ]


if __name__ == "__main__":
    test_performance_engine_uses_provider_and_preserves_device()

    print(
        "performance provider orchestration: OK"
    )
