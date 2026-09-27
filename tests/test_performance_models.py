from models import PagePerformanceData, PerformanceData


def test_performance_data_defaults():
    page = PagePerformanceData(
        url="https://example.com/",
        device="mobile",
    )

    assert page.url == "https://example.com/"
    assert page.device == "mobile"
    assert page.crux_status == "unavailable"
    assert page.crux_metrics == {}
    assert page.lighthouse_status == "unavailable"
    assert page.lighthouse_score is None
    assert page.errors == []

    performance_data = PerformanceData(
        device="mobile"
    )

    assert performance_data.device == "mobile"
    assert performance_data.sampled_urls == []
    assert performance_data.pages == []
    assert performance_data.field_data_available is False
    assert performance_data.lab_data_available is False
    assert performance_data.status == "unavailable"


if __name__ == "__main__":
    test_performance_data_defaults()

    print(
        "performance models: OK"
    )
