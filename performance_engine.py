from config import ALLOWED_DEVICES, PERFORMANCE_SAMPLE_SIZE
from models import PagePerformanceData, PerformanceData, SiteData
from providers.google import GooglePerformanceProvider


def select_performance_sample(
    site_data: SiteData,
    sample_size: int = PERFORMANCE_SAMPLE_SIZE,
) -> list[str]:
    selected_urls = []
    seen_urls = set()

    def add_url(url: str | None) -> None:
        if not url:
            return

        if url in seen_urls:
            return

        if len(selected_urls) >= sample_size:
            return

        seen_urls.add(url)
        selected_urls.append(url)

    homepage = None

    for page in site_data.pages:
        if page.page_type == "homepage":
            homepage = page
            break

    if homepage is None:
        for page in site_data.pages:
            if page.final_url == site_data.submitted_url:
                homepage = page
                break

    if homepage:
        add_url(homepage.final_url)

    desired_page_types = [
        "commercial",
        "editorial",
        "unclassified",
    ]

    for page_type in desired_page_types:
        for page in site_data.pages:
            if page.page_type != page_type:
                continue

            add_url(page.final_url)
            break

    for page in site_data.pages:
        add_url(page.final_url)

    return selected_urls


def analyze_web_performance(
    site_data: SiteData,
    device: str = "mobile",
    provider: GooglePerformanceProvider | None = None,
) -> PerformanceData:
    if device not in ALLOWED_DEVICES:
        raise ValueError(
            f"Unsupported device: {device}"
        )

    provider = provider or GooglePerformanceProvider()

    sampled_urls = select_performance_sample(
        site_data
    )

    performance_data = PerformanceData(
        device=device,
        sampled_urls=sampled_urls,
        provenance={
            "field_provider": "CrUX",
            "lab_provider": "PageSpeed Insights / Lighthouse",
        },
    )

    for url in sampled_urls:
        page_performance = PagePerformanceData(
            url=url,
            device=device,
        )

        crux_result = provider.fetch_crux(
            url,
            device,
        )

        page_performance.crux_status = str(
            crux_result.get(
                "status",
                "unavailable",
            )
        )
        page_performance.crux_scope = crux_result.get(
            "scope"
        )
        page_performance.crux_metrics = dict(
            crux_result.get(
                "metrics",
                {},
            )
        )

        crux_error = crux_result.get(
            "error"
        )

        if crux_error:
            page_performance.errors.append({
                "source": "crux",
                "error": str(crux_error),
            })

        pagespeed_result = provider.run_pagespeed(
            url,
            device,
        )

        page_performance.lighthouse_status = str(
            pagespeed_result.get(
                "status",
                "unavailable",
            )
        )
        page_performance.lighthouse_score = (
            pagespeed_result.get(
                "score"
            )
        )
        page_performance.lighthouse_metrics = dict(
            pagespeed_result.get(
                "metrics",
                {},
            )
        )
        page_performance.lighthouse_diagnostics = list(
            pagespeed_result.get(
                "diagnostics",
                [],
            )
        )

        pagespeed_error = pagespeed_result.get(
            "error"
        )

        if pagespeed_error:
            page_performance.errors.append({
                "source": "pagespeed",
                "error": str(pagespeed_error),
            })

        performance_data.pages.append(
            page_performance
        )

    performance_data.field_data_available = any(
        page.crux_status == "available"
        for page in performance_data.pages
    )

    performance_data.lab_data_available = any(
        page.lighthouse_status == "available"
        for page in performance_data.pages
    )

    if (
        performance_data.field_data_available
        and performance_data.lab_data_available
    ):
        performance_data.status = "complete"
    elif (
        performance_data.field_data_available
        or performance_data.lab_data_available
    ):
        performance_data.status = "partial"
    else:
        performance_data.status = "unavailable"

    return performance_data
