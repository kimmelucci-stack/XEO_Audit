from __future__ import annotations

import requests

from config import GOOGLE_API_KEY, HTTP_TIMEOUT_SECONDS
from models import PagePerformanceData


CRUX_API_URL = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

DEVICE_TO_CRUX_FORM_FACTOR = {
    "mobile": "PHONE",
    "desktop": "DESKTOP",
}

DEVICE_TO_PAGESPEED_STRATEGY = {
    "mobile": "mobile",
    "desktop": "desktop",
}


class GooglePerformanceProvider:
    """
    Provider boundary for CrUX and PageSpeed Insights.

    The implementation is fail-soft: missing credentials, HTTP errors,
    malformed responses, and unavailable field data all return structured
    unavailable results instead of raising into the audit pipeline.
    """

    def __init__(
        self,
        api_key: str | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key or GOOGLE_API_KEY
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def fetch_crux(
        self,
        url: str,
        device: str,
    ) -> dict[str, object]:
        if not self.api_key:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": "UNAVAILABLE_DATA: Google API key not configured",
            }

        form_factor = DEVICE_TO_CRUX_FORM_FACTOR.get(
            device
        )

        if form_factor is None:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": f"UNSUPPORTED_DEVICE: {device}",
            }

        try:
            response = self.session.post(
                CRUX_API_URL,
                params={
                    "key": self.api_key,
                },
                json={
                    "url": url,
                    "formFactor": form_factor,
                },
                timeout=self.timeout_seconds,
            )

        except requests.RequestException as exc:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": f"REQUEST_ERROR: {exc}",
            }

        if response.status_code == 404:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": "UNAVAILABLE_DATA: insufficient CrUX data",
            }

        if response.status_code >= 400:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": (
                    "HTTP_ERROR: CrUX returned "
                    f"{response.status_code}"
                ),
            }

        try:
            payload = response.json()

        except ValueError as exc:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": f"PARSE_ERROR: {exc}",
            }

        record = payload.get(
            "record",
            {},
        )

        metrics = record.get(
            "metrics",
            {},
        )

        if not metrics:
            return {
                "status": "unavailable",
                "scope": None,
                "metrics": {},
                "error": "UNAVAILABLE_DATA: CrUX response had no metrics",
            }

        key = record.get(
            "key",
            {},
        )

        scope = (
            "url"
            if key.get("url")
            else "origin"
            if key.get("origin")
            else None
        )

        return {
            "status": "available",
            "scope": scope,
            "metrics": {
                metric_name: {
                    "percentiles": metric_data.get(
                        "percentiles",
                        {},
                    ),
                    "histogram": metric_data.get(
                        "histogram",
                        [],
                    ),
                }
                for metric_name, metric_data in metrics.items()
                if isinstance(
                    metric_data,
                    dict,
                )
            },
        }

    def run_pagespeed(
        self,
        url: str,
        device: str,
    ) -> dict[str, object]:
        strategy = DEVICE_TO_PAGESPEED_STRATEGY.get(
            device
        )

        if strategy is None:
            return {
                "status": "unavailable",
                "score": None,
                "metrics": {},
                "diagnostics": [],
                "error": f"UNSUPPORTED_DEVICE: {device}",
            }

        params = {
            "url": url,
            "strategy": strategy,
            "category": "performance",
        }

        if self.api_key:
            params["key"] = self.api_key

        try:
            response = self.session.get(
                PAGESPEED_API_URL,
                params=params,
                timeout=self.timeout_seconds,
            )

        except requests.RequestException as exc:
            return {
                "status": "unavailable",
                "score": None,
                "metrics": {},
                "diagnostics": [],
                "error": f"REQUEST_ERROR: {exc}",
            }

        if response.status_code >= 400:
            return {
                "status": "unavailable",
                "score": None,
                "metrics": {},
                "diagnostics": [],
                "error": (
                    "HTTP_ERROR: PageSpeed returned "
                    f"{response.status_code}"
                ),
            }

        try:
            payload = response.json()

        except ValueError as exc:
            return {
                "status": "unavailable",
                "score": None,
                "metrics": {},
                "diagnostics": [],
                "error": f"PARSE_ERROR: {exc}",
            }

        lighthouse_result = payload.get(
            "lighthouseResult",
            {},
        )

        categories = lighthouse_result.get(
            "categories",
            {},
        )

        performance_category = categories.get(
            "performance",
            {},
        )

        audits = lighthouse_result.get(
            "audits",
            {},
        )

        score = performance_category.get(
            "score"
        )

        metrics = extract_pagespeed_metrics(
            audits
        )

        if score is None and not metrics:
            return {
                "status": "unavailable",
                "score": None,
                "metrics": {},
                "diagnostics": [],
                "error": (
                    "UNAVAILABLE_DATA: PageSpeed response had no "
                    "performance results"
                ),
            }

        return {
            "status": "available",
            "score": score,
            "metrics": metrics,
            "diagnostics": extract_pagespeed_diagnostics(
                audits
            ),
        }


def extract_pagespeed_metrics(
    audits: dict[str, object],
) -> dict[str, object]:
    metric_ids = {
        "first-contentful-paint": "first_contentful_paint",
        "largest-contentful-paint": "largest_contentful_paint",
        "total-blocking-time": "total_blocking_time",
        "cumulative-layout-shift": "cumulative_layout_shift",
        "speed-index": "speed_index",
        "interactive": "time_to_interactive",
    }

    metrics = {}

    for audit_id, metric_name in metric_ids.items():
        audit = audits.get(
            audit_id,
            {},
        )

        if not isinstance(
            audit,
            dict,
        ):
            continue

        metrics[metric_name] = {
            "numeric_value": audit.get(
                "numericValue"
            ),
            "display_value": audit.get(
                "displayValue"
            ),
            "score": audit.get(
                "score"
            ),
        }

    return metrics


def extract_pagespeed_diagnostics(
    audits: dict[str, object],
    limit: int = 10,
) -> list[dict[str, object]]:
    diagnostics = []

    for audit_id, audit in audits.items():
        if not isinstance(
            audit,
            dict,
        ):
            continue

        details = audit.get(
            "details",
            {},
        )

        if not isinstance(
            details,
            dict,
        ):
            continue

        if details.get("type") != "opportunity":
            continue

        score = audit.get(
            "score"
        )

        if score is not None and score >= 0.9:
            continue

        diagnostics.append({
            "id": audit_id,
            "title": audit.get(
                "title"
            ),
            "score": score,
            "display_value": audit.get(
                "displayValue"
            ),
        })

        if len(diagnostics) >= limit:
            break

    return diagnostics


def build_unavailable_performance_page(
    url: str,
    device: str,
    reason: str,
) -> PagePerformanceData:
    return PagePerformanceData(
        url=url,
        device=device,
        errors=[
            {
                "source": "google",
                "error": reason,
            }
        ],
    )
