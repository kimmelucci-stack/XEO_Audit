from evaluation_engine import evaluate_audit
from intelligence_engine import build_recommendations
from models import SearchEvidence


def test_build_recommendations_groups_findings_by_issue():
    evaluation = evaluate_audit([
        SearchEvidence(
            evidence_id="meta_description_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/about/"
            ],
        ),
        SearchEvidence(
            evidence_id="meta_description_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/services/"
            ],
        ),
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/"
            ],
        ),
        SearchEvidence(
            evidence_id="sitemap_detected",
            category="technical",
            scope="site",
        ),
    ])

    recommendations = build_recommendations(
        evaluation
    )

    assert [
        recommendation.recommendation_id
        for recommendation in recommendations
    ] == [
        "title_missing",
        "meta_description_missing",
    ]

    description_recommendation = recommendations[1]

    assert description_recommendation.priority == "P2"
    assert description_recommendation.rationale == (
        "2 occorrenze rilevate, con impatto stimato di 10 punti sullo score."
    )
    assert (
        "sistemi AI"
        in description_recommendation.xeo_explanation
    )
    assert description_recommendation.source_urls == [
        "https://example.com/about/",
        "https://example.com/services/",
    ]
    assert description_recommendation.actions


def test_build_recommendations_respects_limit():
    evaluation = evaluate_audit([
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
        ),
        SearchEvidence(
            evidence_id="h1_missing",
            category="headings",
            scope="page",
        ),
    ])

    recommendations = build_recommendations(
        evaluation,
        limit=1,
    )

    assert len(
        recommendations
    ) == 1
