from evaluation_engine import (
    build_audit_result,
    build_performance_pillar,
    evaluate_audit,
    grade_score,
)
from models import (
    AuditContext,
    PagePerformanceData,
    PerformanceData,
    SearchEvidence,
)


def test_grade_score_boundaries():
    assert grade_score(95) == "A"
    assert grade_score(80) == "B"
    assert grade_score(70) == "C"
    assert grade_score(60) == "D"
    assert grade_score(59) == "F"


def test_evaluate_audit_scores_search_evidence():
    evaluation = evaluate_audit([
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/"
            ],
            observed={
                "title": None,
            },
        ),
        SearchEvidence(
            evidence_id="sitemap_detected",
            category="technical",
            scope="site",
            source_urls=[
                "https://example.com/sitemap.xml"
            ],
        ),
    ])

    assert evaluation.score == 95
    assert evaluation.grade == "A"
    assert evaluation.category_scores == {
        "metadata": 90,
        "technical": 100,
    }

    finding = evaluation.findings[0]

    assert finding.finding_id == "title_missing"
    assert finding.severity == "high"
    assert finding.score_impact == 10
    assert finding.source_urls == [
        "https://example.com/"
    ]
    assert finding.observed == {
        "title": None,
    }


def test_evaluate_audit_includes_performance_findings():
    performance_data = PerformanceData(
        device="mobile",
        status="partial",
        pages=[
            PagePerformanceData(
                url="https://example.com/",
                device="mobile",
                lighthouse_status="available",
                lighthouse_score=0.49,
            )
        ],
    )

    evaluation = evaluate_audit(
        search_evidence=[],
        performance_data=performance_data,
    )

    assert evaluation.score == 90
    assert evaluation.grade == "A"
    assert evaluation.category_scores == {
        "performance": 90,
    }

    finding = evaluation.findings[0]

    assert finding.finding_id == "poor_lighthouse_score"
    assert finding.category == "performance"
    assert finding.severity == "high"
    assert finding.observed == {
        "lighthouse_score": 0.49,
        "device": "mobile",
    }


def test_evaluate_audit_scores_missing_canonical_explicitly():
    evaluation = evaluate_audit([
        SearchEvidence(
            evidence_id="canonical_missing",
            category="canonical",
            scope="page",
            source_urls=[
                "https://example.com/about/"
            ],
        )
    ])

    assert evaluation.score == 95
    assert evaluation.category_scores == {
        "canonical": 95,
    }

    finding = evaluation.findings[0]

    assert finding.severity == "medium"
    assert finding.score_impact == 5
    assert finding.message == "Manca l'URL canonical."


def test_build_performance_pillar_from_lighthouse_scores():
    performance_data = PerformanceData(
        device="mobile",
        status="partial",
        pages=[
            PagePerformanceData(
                url="https://example.com/",
                device="mobile",
                lighthouse_score=0.91,
            ),
            PagePerformanceData(
                url="https://example.com/about/",
                device="mobile",
                lighthouse_score=0.79,
            ),
        ],
    )

    pillar = build_performance_pillar(
        performance_data
    )

    assert pillar.pillar_id == "web_performance"
    assert pillar.status == "available"
    assert pillar.score == 85
    assert pillar.weight == 0.15


def test_build_audit_result_includes_performance_pillar_score():
    evaluation = evaluate_audit(
        search_evidence=[],
        performance_data=None,
    )

    performance_data = PerformanceData(
        device="desktop",
        status="partial",
        pages=[
            PagePerformanceData(
                url="https://example.com/",
                device="desktop",
                lighthouse_score=0.8,
            )
        ],
    )

    result = build_audit_result(
        context=AuditContext(
            submitted_url="https://example.com/"
        ),
        evaluation=evaluation,
        performance_data=performance_data,
    )

    performance_pillar = [
        pillar
        for pillar in result.pillar_scores
        if pillar.pillar_id == "web_performance"
    ][0]

    assert performance_pillar.score == 80
    assert result.xeo_score is None
    assert result.xeo_status == "incomplete"


if __name__ == "__main__":
    test_grade_score_boundaries()
    test_evaluate_audit_scores_search_evidence()
    test_evaluate_audit_includes_performance_findings()
    test_evaluate_audit_scores_missing_canonical_explicitly()
    test_build_performance_pillar_from_lighthouse_scores()
    test_build_audit_result_includes_performance_pillar_score()

    print(
        "evaluation engine: OK"
    )
