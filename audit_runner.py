from __future__ import annotations

import json
from dataclasses import dataclass

from collector import collect_site, normalize_url
from config import CRAWL_HARD_CAP, CRAWL_MIN_DESIRED
from evaluation_engine import build_audit_result, evaluate_audit
from intelligence_engine import analyze_intelligence, build_recommendations
from models import (
    AuditContext,
    AuditEvaluation,
    AuditRecommendation,
    AuditResult,
    IntelligenceData,
    PerformanceData,
    SearchEvidence,
    SiteData,
)
from performance_engine import analyze_web_performance
from report_builder import (
    build_audit_report,
    build_html_report,
    build_markdown_report,
)
from seo_engine import analyze_search_readiness


DEMO_CRAWL_HARD_CAP = 10
DEMO_CRAWL_MIN_DESIRED = 5
DEMO_RECOMMENDATION_LIMIT = 6


@dataclass
class AuditRun:
    context: AuditContext
    site_data: SiteData
    search_evidence: list[SearchEvidence]
    performance_data: PerformanceData
    intelligence_data: IntelligenceData
    evaluation: AuditEvaluation
    audit_result: AuditResult
    recommendations: list[AuditRecommendation]
    report: dict[str, object]
    markdown_report: str
    html_report: str


def run_audit(
    url: str,
    device: str = "mobile",
    recommendation_limit: int | None = None,
    demo_mode: bool = False,
) -> AuditRun:
    normalized_url = normalize_url(
        url
    )

    context = AuditContext(
        submitted_url=normalized_url,
        device=device,
    )

    hard_cap = (
        DEMO_CRAWL_HARD_CAP
        if demo_mode
        else None
    )

    min_desired = (
        DEMO_CRAWL_MIN_DESIRED
        if demo_mode
        else None
    )

    site_data = collect_site(
        normalized_url,
        hard_cap=hard_cap or CRAWL_HARD_CAP,
        min_desired=min_desired or CRAWL_MIN_DESIRED,
    )

    search_evidence = analyze_search_readiness(
        site_data
    )

    performance_data = analyze_web_performance(
        site_data,
        device=device,
    )

    intelligence_data = analyze_intelligence(
        site_data,
        device=device,
    )

    evaluation = evaluate_audit(
        search_evidence=search_evidence,
        performance_data=performance_data,
    )

    if recommendation_limit is None and demo_mode:
        recommendation_limit = DEMO_RECOMMENDATION_LIMIT

    recommendations = build_recommendations(
        evaluation,
        limit=recommendation_limit,
    )

    audit_result = build_audit_result(
        context=context,
        evaluation=evaluation,
        performance_data=performance_data,
        recommendations=recommendations,
    )
    audit_result.keywords = intelligence_data.keywords
    audit_result.serp_results = intelligence_data.serp_results

    report = build_audit_report(
        context=context,
        site_data=site_data,
        search_evidence=search_evidence,
        performance_data=performance_data,
        evaluation=evaluation,
        recommendations=recommendations,
        audit_result=audit_result,
    )
    report["intelligence"] = {
        "status": intelligence_data.status,
        "semantic_status": intelligence_data.semantic_status,
        "keyword_status": intelligence_data.keyword_status,
        "serp_status": intelligence_data.serp_status,
        "semantic_summary": intelligence_data.semantic_summary,
        "keywords": [
            keyword.__dict__
            for keyword in intelligence_data.keywords
        ],
        "serp_results": [
            serp.__dict__
            for serp in intelligence_data.serp_results
        ],
        "errors": intelligence_data.errors,
    }

    if demo_mode:
        report["mode"] = "demo"
        report["demo_limits"] = {
            "crawl_hard_cap": DEMO_CRAWL_HARD_CAP,
            "crawl_min_desired": DEMO_CRAWL_MIN_DESIRED,
            "recommendation_limit": recommendation_limit,
        }

    markdown_report = build_markdown_report(
        context=context,
        site_data=site_data,
        search_evidence=search_evidence,
        performance_data=performance_data,
        evaluation=evaluation,
        recommendations=recommendations,
    )

    html_report = build_html_report(
        context=context,
        site_data=site_data,
        search_evidence=search_evidence,
        performance_data=performance_data,
        intelligence_data=intelligence_data,
        evaluation=evaluation,
        recommendations=recommendations,
        audit_result=audit_result,
        demo_mode=demo_mode,
    )

    return AuditRun(
        context=context,
        site_data=site_data,
        search_evidence=search_evidence,
        performance_data=performance_data,
        intelligence_data=intelligence_data,
        evaluation=evaluation,
        audit_result=audit_result,
        recommendations=recommendations,
        report=report,
        markdown_report=markdown_report,
        html_report=html_report,
    )


def serialize_json_report(
    audit_run: AuditRun,
) -> str:
    return json.dumps(
        audit_run.report,
        ensure_ascii=False,
        indent=2,
    )
