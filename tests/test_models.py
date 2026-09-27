from models import (
    AuditContext,
    AuditRecommendation,
    AuditResult,
    KeywordData,
    PageData,
    PillarScore,
    SerpData,
)


def test_audit_context_defaults():
    context = AuditContext(
        submitted_url="https://example.com",
    )

    assert context.submitted_url == "https://example.com"
    assert context.device == "mobile"
    assert context.language is None
    assert context.location is None
    assert context.audit_id is None
    assert context.timestamp is None
    assert context.scoring_version is None
    assert context.persistence_key is None


def test_page_data_defaults_are_isolated():
    first_page = PageData(
        source_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
    )

    second_page = PageData(
        source_url="https://example.com/about/",
        final_url="https://example.com/about/",
        status_code=200,
    )

    first_page.h1.append(
        "Home"
    )

    assert first_page.h1 == [
        "Home"
    ]
    assert second_page.h1 == []
    assert first_page.internal_links == []
    assert first_page.image_count == 0
    assert first_page.visible_text == ""


def test_audit_recommendation_defaults():
    recommendation = AuditRecommendation(
        recommendation_id="title_missing",
        priority="P1",
        category="metadata",
        title="Page is missing a title tag.",
        rationale="1 occurrence detected.",
    )

    assert recommendation.source_urls == []
    assert recommendation.actions == []
    assert recommendation.finding_ids == []
    assert recommendation.xeo_explanation == ""


def test_prd_result_models_defaults():
    keyword = KeywordData(
        keyword="consulenza ai"
    )

    serp = SerpData(
        keyword="consulenza ai",
        device="mobile",
    )

    pillar = PillarScore(
        pillar_id="search_readiness",
        label="Search Readiness",
        status="available",
        score=90,
        weight=0.4,
    )

    result = AuditResult(
        context=AuditContext(
            submitted_url="https://example.com/"
        ),
        pillar_scores=[
            pillar
        ],
        keywords=[
            keyword
        ],
        serp_results=[
            serp
        ],
    )

    assert keyword.source == "unavailable"
    assert serp.status == "unavailable"
    assert result.xeo_score is None
    assert result.xeo_status == "incomplete"
    assert result.pillar_scores[0].score == 90
