from audit_runner import run_audit, serialize_json_report
from models import PageData, PerformanceData, SiteData


class FakeProviderPerformance:
    pass


def test_run_audit_demo_mode_uses_limited_crawl(monkeypatch):
    calls = {}

    def fake_collect_site(
        url,
        hard_cap,
        min_desired,
    ):
        calls["collect_site"] = {
            "url": url,
            "hard_cap": hard_cap,
            "min_desired": min_desired,
        }

        return SiteData(
            submitted_url=url,
            normalized_host="example.com",
            pages=[
                PageData(
                    source_url=url,
                    final_url=url,
                    status_code=200,
                    page_type="homepage",
                    title=None,
                    meta_description="Example",
                    h1=[
                        "Example"
                    ],
                    canonical=url,
                )
            ],
            pages_discovered=1,
            pages_selected=1,
            pages_fetched=1,
            robots_txt_available=True,
        )

    def fake_analyze_web_performance(
        site_data,
        device,
    ):
        return PerformanceData(
            device=device,
            status="complete",
        )

    monkeypatch.setattr(
        "audit_runner.collect_site",
        fake_collect_site,
    )
    monkeypatch.setattr(
        "audit_runner.analyze_web_performance",
        fake_analyze_web_performance,
    )

    audit_run = run_audit(
        "example.com",
        device="desktop",
        demo_mode=True,
    )

    assert calls["collect_site"] == {
        "url": "https://example.com/",
        "hard_cap": 10,
        "min_desired": 5,
    }
    assert audit_run.context.device == "desktop"
    assert audit_run.audit_result.xeo_score is None
    assert audit_run.audit_result.xeo_status == "incomplete"
    assert audit_run.audit_result.pillar_scores[0].pillar_id == "search_readiness"
    assert audit_run.audit_result.pillar_scores[2].pillar_id == "web_performance"
    assert audit_run.audit_result.pillar_scores[2].score is None
    assert audit_run.report["mode"] == "demo"
    assert audit_run.report["demo_limits"]["crawl_hard_cap"] == 10
    assert audit_run.evaluation.score == 94
    assert audit_run.evaluation.category_scores["content_extractability"] == 95
    assert "Report tecnico di base" in audit_run.html_report
    assert '"mode": "demo"' in serialize_json_report(
        audit_run
    )
