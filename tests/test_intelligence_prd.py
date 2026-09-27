from intelligence_engine import (
    analyze_intelligence,
    extract_candidate_phrases,
    generate_keyword_candidates,
)
from models import PageData, SiteData
from providers.dataforseo import DataForSEOProvider
from providers.llm import LLMProvider


def test_extract_candidate_phrases_filters_stopwords():
    phrases = extract_candidate_phrases(
        "Consulenza AI per aziende e automazione processi"
    )

    assert all(
        " per " not in f" {phrase} "
        for phrase in phrases
    )
    assert "automazione processi" in phrases


def test_generate_keyword_candidates_from_page_evidence():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            PageData(
                source_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                title="Consulenza AI per aziende",
                meta_description="Automazione processi con intelligenza artificiale",
                h1=[
                    "Consulenza AI"
                ],
            )
        ],
    )

    keywords = generate_keyword_candidates(
        site_data
    )

    assert keywords
    assert keywords[0].source == "deterministic_page_evidence"
    assert any(
        keyword.keyword == "automazione processi"
        for keyword in keywords
    )


def test_analyze_intelligence_is_fail_soft_without_providers():
    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            PageData(
                source_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                title="Consulenza AI per aziende",
            )
        ],
    )

    intelligence = analyze_intelligence(
        site_data,
        device="mobile",
        llm_provider=LLMProvider(
            api_key=""
        ),
        dataforseo_provider=DataForSEOProvider(
            login="",
            password="",
        ),
    )

    assert intelligence.status == "partial"
    assert intelligence.semantic_status == "unavailable"
    assert intelligence.keyword_status == "candidate_only"
    assert intelligence.serp_status == "unavailable"
    assert intelligence.keywords
    assert intelligence.serp_results
    assert intelligence.errors
