from __future__ import annotations

from collections import defaultdict

from models import (
    AuditEvaluation,
    AuditResult,
    AuditContext,
    EvaluationFinding,
    PillarScore,
    PerformanceData,
    SearchEvidence,
)


SEVERITY_IMPACTS = {
    "critical": 15,
    "high": 10,
    "medium": 5,
    "low": 2,
    "info": 0,
}


SEVERITY_GROUP_CAPS = {
    "critical": 30,
    "high": 20,
    "medium": 15,
    "low": 6,
    "info": 0,
}


EVIDENCE_SEVERITY = {
    "http_status_non_200": "critical",
    "noindex_detected": "critical",
    "canonical_external": "high",
    "canonical_mismatch": "high",
    "canonical_missing": "medium",
    "title_missing": "high",
    "h1_missing": "high",
    "robots_txt_unavailable": "medium",
    "sitemap_unavailable": "medium",
    "meta_description_missing": "medium",
    "h1_multiple": "medium",
    "nofollow_detected": "medium",
    "x_robots_tag_detected": "medium",
    "images_missing_alt": "medium",
    "internal_links_missing_anchor_text": "medium",
    "no_internal_links": "medium",
    "no_observed_inbound_links": "low",
    "redirect_detected": "low",
    "duplicate_title": "low",
    "duplicate_meta_description": "low",
    "content_extractability_low": "medium",
    "entity_context_weak": "low",
    "answerability_structure_weak": "low",
    "structured_facts_missing": "low",
    "sitemap_detected": "info",
    "structured_data_detected": "info",
}


FINDING_MESSAGES = {
    "http_status_non_200": "La pagina restituisce uno status HTTP non 200.",
    "noindex_detected": "La pagina è marcata noindex.",
    "canonical_external": "Il canonical punta a un dominio esterno.",
    "canonical_mismatch": "Il canonical non coincide con l'URL finale.",
    "canonical_missing": "Manca l'URL canonical.",
    "title_missing": "Manca il tag title.",
    "h1_missing": "Manca un H1 principale.",
    "robots_txt_unavailable": "Il file robots.txt non è disponibile.",
    "sitemap_unavailable": "Non è stata rilevata una sitemap.",
    "meta_description_missing": "Manca la meta description.",
    "h1_multiple": "La pagina ha piu H1.",
    "nofollow_detected": "La pagina è marcata nofollow.",
    "x_robots_tag_detected": "È stato rilevato un header X-Robots-Tag.",
    "images_missing_alt": "Una o piu immagini non hanno testo alt.",
    "internal_links_missing_anchor_text": (
        "Uno o piu link interni non hanno anchor text."
    ),
    "no_internal_links": "La pagina non ha link interni.",
    "no_observed_inbound_links": (
        "Non sono stati osservati link interni in ingresso per questa pagina."
    ),
    "redirect_detected": "La pagina passa da un redirect prima dell'URL finale.",
    "duplicate_title": "Title duplicato su piu pagine.",
    "duplicate_meta_description": (
        "Meta description duplicata su piu pagine."
    ),
    "content_extractability_low": (
        "La pagina contiene poco testo visibile estraibile."
    ),
    "entity_context_weak": (
        "Title e H1 non condividono termini descrittivi chiari."
    ),
    "answerability_structure_weak": (
        "Il contenuto lungo non usa heading di supporto."
    ),
    "structured_facts_missing": (
        "Mancano dati strutturati per una pagina informativa o commerciale."
    ),
    "sitemap_detected": "Sitemap rilevata.",
    "structured_data_detected": "Dati strutturati rilevati.",
}


def grade_score(score: int) -> str:
    if score >= 90:
        return "A"

    if score >= 80:
        return "B"

    if score >= 70:
        return "C"

    if score >= 60:
        return "D"

    return "F"


def build_finding_from_evidence(
    evidence: SearchEvidence,
) -> EvaluationFinding:
    severity = EVIDENCE_SEVERITY.get(
        evidence.evidence_id,
        "low",
    )

    return EvaluationFinding(
        finding_id=evidence.evidence_id,
        category=evidence.category,
        severity=severity,
        score_impact=SEVERITY_IMPACTS[severity],
        source_urls=list(
            evidence.source_urls
        ),
        observed=dict(
            evidence.observed
        ),
        message=FINDING_MESSAGES.get(
            evidence.evidence_id,
            evidence.evidence_id.replace(
                "_",
                " ",
            ).capitalize(),
        ),
    )


def build_performance_findings(
    performance_data: PerformanceData | None,
) -> list[EvaluationFinding]:
    if performance_data is None:
        return []

    findings = []

    if performance_data.status == "unavailable":
        findings.append(
            EvaluationFinding(
                finding_id="performance_data_unavailable",
                category="performance",
                severity="medium",
                score_impact=SEVERITY_IMPACTS["medium"],
                message="I dati performance non sono disponibili.",
            )
        )

    for page in performance_data.pages:
        if (
            page.lighthouse_score is not None
            and page.lighthouse_score < 0.5
        ):
            findings.append(
                EvaluationFinding(
                    finding_id="poor_lighthouse_score",
                    category="performance",
                    severity="high",
                    score_impact=SEVERITY_IMPACTS["high"],
                    source_urls=[
                        page.url
                    ],
                    observed={
                        "lighthouse_score": page.lighthouse_score,
                        "device": page.device,
                    },
                    message="Il punteggio Lighthouse performance è basso.",
                )
            )

        elif (
            page.lighthouse_score is not None
            and page.lighthouse_score < 0.75
        ):
            findings.append(
                EvaluationFinding(
                    finding_id="needs_improvement_lighthouse_score",
                    category="performance",
                    severity="medium",
                    score_impact=SEVERITY_IMPACTS["medium"],
                    source_urls=[
                        page.url
                    ],
                    observed={
                        "lighthouse_score": page.lighthouse_score,
                        "device": page.device,
                    },
                    message=(
                        "Il punteggio Lighthouse performance va migliorato."
                    ),
                )
            )

    return findings


def evaluate_audit(
    search_evidence: list[SearchEvidence],
    performance_data: PerformanceData | None = None,
) -> AuditEvaluation:
    findings = [
        build_finding_from_evidence(
            evidence
        )
        for evidence in search_evidence
    ]

    findings.extend(
        build_performance_findings(
            performance_data
        )
    )

    category_groups = defaultdict(list)

    for finding in findings:
        category_groups[
            finding.category
        ].append(
            finding
        )

    category_scores = {
        category: max(
            0,
            100 - calculate_capped_impact(
                category_findings
            ),
        )
        for category, category_findings in sorted(
            category_groups.items()
        )
    }

    score = calculate_overall_score(
        category_scores
    )

    return AuditEvaluation(
        score=score,
        grade=grade_score(
            score
        ),
        score_label="Search / Technical Readiness",
        xeo_score=None,
        xeo_status="incomplete",
        findings=findings,
        category_scores=category_scores,
    )


def calculate_capped_impact(
    findings: list[EvaluationFinding],
) -> int:
    grouped_impacts = defaultdict(int)
    group_severities = {}

    for finding in findings:
        grouped_impacts[
            finding.finding_id
        ] += finding.score_impact
        group_severities[
            finding.finding_id
        ] = finding.severity

    total = 0

    for finding_id, impact in grouped_impacts.items():
        severity = group_severities.get(
            finding_id,
            "low",
        )
        cap = SEVERITY_GROUP_CAPS.get(
            severity,
            6,
        )
        total += min(
            impact,
            cap,
        )

    return total


def calculate_overall_score(
    category_scores: dict[str, int],
) -> int:
    if not category_scores:
        return 100

    return round(
        sum(
            category_scores.values()
        )
        / len(
            category_scores
        )
    )


def build_audit_result(
    context: AuditContext,
    evaluation: AuditEvaluation,
    performance_data: PerformanceData | None = None,
    recommendations: list[object] | None = None,
) -> AuditResult:
    performance_pillar = build_performance_pillar(
        performance_data
    )

    pillar_scores = [
        PillarScore(
            pillar_id="search_readiness",
            label="Search Readiness",
            status="available",
            score=evaluation.score,
            weight=0.40,
            summary=(
                "Disponibile: basato su crawl tecnico, metadata, "
                "canonical, sitemap, link interni, immagini e structured data."
            ),
        ),
        PillarScore(
            pillar_id="aigen_lm_readiness",
            label="AIgen & LM Readiness",
            status="not_implemented",
            score=None,
            weight=0.25,
            summary=(
                "Non ancora implementato: analisi semantica LLM, "
                "answerability, entity clarity e citation readiness."
            ),
        ),
        performance_pillar,
        PillarScore(
            pillar_id="keyword_position_performance",
            label="Keyword Position Performance",
            status="not_implemented",
            score=None,
            weight=0.20,
            summary=(
                "Non ancora implementato: keyword universe, DataForSEO "
                "e posizionamenti Google organici osservati."
            ),
        ),
    ]

    return AuditResult(
        context=context,
        technical_eligibility="warning",
        xeo_score=None,
        xeo_status="incomplete",
        pillar_scores=pillar_scores,
        findings=evaluation.findings,
        recommendations=list(
            recommendations or []
        ),
    )


def build_performance_pillar(
    performance_data: PerformanceData | None,
) -> PillarScore:
    if performance_data is None:
        return PillarScore(
            pillar_id="web_performance",
            label="Web Performance",
            status="unavailable",
            score=None,
            weight=0.15,
            summary="Performance non eseguita.",
        )

    lighthouse_scores = [
        page.lighthouse_score
        for page in performance_data.pages
        if page.lighthouse_score is not None
    ]

    if not lighthouse_scores:
        return PillarScore(
            pillar_id="web_performance",
            label="Web Performance",
            status=performance_data.status,
            score=None,
            weight=0.15,
            summary=(
                "Nessun punteggio Lighthouse disponibile; il pillar resta "
                "non calcolabile."
            ),
        )

    score = round(
        sum(
            lighthouse_scores
        )
        / len(
            lighthouse_scores
        )
        * 100
    )

    status = (
        "available"
        if performance_data.status in (
            "complete",
            "partial",
        )
        else performance_data.status
    )

    return PillarScore(
        pillar_id="web_performance",
        label="Web Performance",
        status=status,
        score=score,
        weight=0.15,
        summary=(
            "Punteggio derivato dalla media dei Lighthouse performance score "
            "disponibili nel campione. CrUX resta separato come field data."
        ),
    )
