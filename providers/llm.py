from __future__ import annotations

from config import OPENAI_API_KEY


class LLMProvider:
    """
    Provider boundary for semantic XEO analysis.

    The provider is fail-soft and currently intentionally does not call a
    remote model. Until prompts/model/versioning are approved, semantic output
    must remain unavailable instead of being fabricated.
    """

    def __init__(
        self,
        api_key: str | None = None,
    ) -> None:
        self.api_key = api_key or OPENAI_API_KEY

    def is_configured(self) -> bool:
        return bool(
            self.api_key
        )

    def infer_semantic_context(
        self,
        sanitized_summary: dict[str, object],
    ) -> dict[str, object]:
        if not self.is_configured():
            return {
                "status": "unavailable",
                "observed": {},
                "error": "UNAVAILABLE_DATA: LLM provider not configured",
            }

        return {
            "status": "unavailable",
            "observed": {},
            "error": "NOT_IMPLEMENTED: LLM prompt/version not approved",
        }
