from evaluation_engine import evaluate_audit
from intelligence_engine import build_recommendations
from models import AuditContext, PageData, SearchEvidence, SiteData
from report_builder import (
    build_audit_report,
    build_html_report,
    build_markdown_report,
    count_findings_by_severity,
)


def test_build_audit_report_serializes_core_sections():
    context = AuditContext(
        submitted_url="https://example.com/",
        device="mobile",
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages=[
            PageData(
                source_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
            )
        ],
        pages_discovered=1,
        pages_selected=1,
        pages_fetched=1,
    )

    evidence = [
        SearchEvidence(
            evidence_id="h1_missing",
            category="headings",
            scope="page",
        )
    ]

    evaluation = evaluate_audit(
        evidence
    )

    report = build_audit_report(
        context=context,
        site_data=site_data,
        search_evidence=evidence,
        evaluation=evaluation,
        recommendations=build_recommendations(
            evaluation
        ),
    )

    assert report["context"]["submitted_url"] == "https://example.com/"
    assert report["site"]["normalized_host"] == "example.com"
    assert report["search_evidence"][0]["evidence_id"] == "h1_missing"
    assert report["evaluation"]["score"] == 90
    assert report["performance"] is None
    assert report["severity_summary"] == {
        "high": 1
    }
    assert report["recommendations"][0]["recommendation_id"] == "h1_missing"
    assert report["recommendations"][0]["xeo_explanation"]
    assert report["audit_result"] is None


def test_build_markdown_report_includes_summary_and_findings():
    context = AuditContext(
        submitted_url="https://example.com/",
        device="desktop",
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages_discovered=3,
        pages_selected=3,
        pages_fetched=2,
        robots_txt_available=True,
        sitemap_files=[
            "https://example.com/sitemap.xml"
        ],
    )

    evidence = [
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/"
            ],
        )
    ]

    evaluation = evaluate_audit(
        evidence
    )

    markdown = build_markdown_report(
        context=context,
        site_data=site_data,
        search_evidence=evidence,
        evaluation=evaluation,
        recommendations=build_recommendations(
            evaluation
        ),
    )

    assert "# Report XEO Audit" in markdown
    assert "Dispositivo: desktop" in markdown
    assert "Search / Technical Readiness: 90/100 (A)" in markdown
    assert "XEO Score: non disponibile" in markdown
    assert "## Riepilogo severita" in markdown
    assert "- Alto: 1" in markdown
    assert "- Metadata: 90/100" in markdown
    assert "[Alto] Manca il tag title." in markdown
    assert "## Piano d'azione" in markdown
    assert "[P1] Manca il tag title." in markdown
    assert "Perche conta per AI/LLM" in markdown


def test_count_findings_by_severity_preserves_known_order():
    evaluation = evaluate_audit([
        SearchEvidence(
            evidence_id="meta_description_missing",
            category="metadata",
            scope="page",
        ),
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
        ),
        SearchEvidence(
            evidence_id="sitemap_detected",
            category="technical",
            scope="site",
        ),
    ])

    assert count_findings_by_severity(
        evaluation
    ) == {
        "high": 1,
        "medium": 1,
        "info": 1,
    }


def test_build_html_report_includes_pdf_action_without_lead_form():
    context = AuditContext(
        submitted_url="https://example.com/",
        device="mobile",
    )

    site_data = SiteData(
        submitted_url="https://example.com/",
        normalized_host="example.com",
        pages_discovered=1,
        pages_selected=1,
        pages_fetched=1,
    )

    evidence = [
        SearchEvidence(
            evidence_id="title_missing",
            category="metadata",
            scope="page",
            source_urls=[
                "https://example.com/"
            ],
        )
    ]

    evaluation = evaluate_audit(
        evidence
    )

    html = build_html_report(
        context=context,
        site_data=site_data,
        search_evidence=evidence,
        evaluation=evaluation,
        recommendations=build_recommendations(
            evaluation
        ),
        demo_mode=True,
    )

    assert "<!doctype html>" in html
    assert "Scarica PDF" in html
    assert "XEO Score non disponibile" in html
    assert "AIgen" in html
    assert "LM Readiness" in html
    assert "Cosa significa questo score" in html
    assert "Legenda scoring" in html
    assert "Come viene calcolato" in html
    assert "Principali motivi" in html
    assert "Ambito demo" in html
    assert "Limite della demo" in html
    assert "Request proposal" not in html
    assert "placeholder=\"Email\"" not in html
    assert "Audit demo" in html
    assert "Manca il tag title." in html
    assert "Perche conta per AI/LLM" in html


if __name__ == "__main__":
    test_build_audit_report_serializes_core_sections()
    test_build_markdown_report_includes_summary_and_findings()
    test_count_findings_by_severity_preserves_known_order()
    test_build_html_report_includes_pdf_action_without_lead_form()

    print(
        "report builder: OK"
    )
