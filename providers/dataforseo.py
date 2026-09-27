from __future__ import annotations

import requests

from config import DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD, HTTP_TIMEOUT_SECONDS


class DataForSEOProvider:
    """
    Provider boundary for keyword metrics and Google SERP LIVE.

    V1 must not invent keyword volume or ranking positions. Missing
    credentials, request errors and unsupported calls return structured
    unavailable states.
    """

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        self.login = login or DATAFORSEO_LOGIN
        self.password = password or DATAFORSEO_PASSWORD
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return bool(
            self.login
            and self.password
        )

    def validate_keyword_metrics(
        self,
        keywords: list[str],
        location_code: int | None = None,
        language_code: str | None = None,
    ) -> dict[str, object]:
        if not self.is_configured():
            return unavailable_result(
                "UNAVAILABLE_DATA: DataForSEO credentials not configured"
            )

        return unavailable_result(
            "NOT_IMPLEMENTED: keyword metrics API call not wired yet"
        )

    def fetch_google_serp_live(
        self,
        keywords: list[str],
        domain: str,
        device: str,
        location_code: int | None = None,
        language_code: str | None = None,
    ) -> dict[str, object]:
        if not self.is_configured():
            return unavailable_result(
                "UNAVAILABLE_DATA: DataForSEO credentials not configured"
            )

        return unavailable_result(
            "NOT_IMPLEMENTED: Google SERP LIVE API call not wired yet"
        )


def unavailable_result(
    reason: str,
) -> dict[str, object]:
    return {
        "status": "unavailable",
        "items": [],
        "error": reason,
    }
