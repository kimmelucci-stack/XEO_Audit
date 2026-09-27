from __future__ import annotations

from dataclasses import asdict
from html import escape

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


def count_findings_by_severity(
    evaluation: AuditEvaluation,
) -> dict[str, int]:
    severity_order = [
        "critical",
        "high",
        "medium",
        "low",
        "info",
    ]

    counts = {
        severity: 0
        for severity in severity_order
    }

    for finding in evaluation.findings:
        counts.setdefault(
            finding.severity,
            0,
        )
        counts[
            finding.severity
        ] += 1

    return {
        severity: count
        for severity, count in counts.items()
        if count > 0
    }


def build_audit_report(
    context: AuditContext,
    site_data: SiteData,
    search_evidence: list[SearchEvidence],
    evaluation: AuditEvaluation,
    performance_data: PerformanceData | None = None,
    intelligence_data: IntelligenceData | None = None,
    recommendations: list[AuditRecommendation] | None = None,
    audit_result: AuditResult | None = None,
) -> dict[str, object]:
    return {
        "context": asdict(
            context
        ),
        "site": asdict(
            site_data
        ),
        "search_evidence": [
            asdict(
                evidence
            )
            for evidence in search_evidence
        ],
        "performance": (
            asdict(
                performance_data
            )
            if performance_data
            else None
        ),
        "evaluation": asdict(
            evaluation
        ),
        "severity_summary": count_findings_by_severity(
            evaluation
        ),
        "recommendations": [
            asdict(
                recommendation
            )
            for recommendation in recommendations or []
        ],
        "audit_result": (
            asdict(
                audit_result
            )
            if audit_result
            else None
        ),
    }


def build_markdown_report(
    context: AuditContext,
    site_data: SiteData,
    search_evidence: list[SearchEvidence],
    evaluation: AuditEvaluation,
    performance_data: PerformanceData | None = None,
    intelligence_data: IntelligenceData | None = None,
    recommendations: list[AuditRecommendation] | None = None,
    audit_result: AuditResult | None = None,
) -> str:
    lines = [
        "# Report XEO Audit",
        "",
        f"URL: {context.submitted_url}",
        f"Dispositivo: {context.device}",
        (
            "Search / Technical Readiness: "
            f"{evaluation.score}/100 ({evaluation.grade})"
        ),
        "XEO Score: non disponibile (moduli AIgen/LM e keyword/SERP mancanti)",
        "",
        "## Riepilogo severita",
        "",
    ]

    severity_summary = count_findings_by_severity(
        evaluation
    )

    if severity_summary:
        for severity, count in severity_summary.items():
            lines.append(
                f"- {translate_label(severity)}: {count}"
            )
    else:
        lines.append(
            "- Nessun finding rilevato."
        )

    lines.extend([
        "",
        "## Riepilogo crawl",
        "",
        f"- Pagine scoperte: {site_data.pages_discovered}",
        f"- Pagine selezionate: {site_data.pages_selected}",
        f"- Pagine analizzate: {site_data.pages_fetched}",
        f"- robots.txt available: {site_data.robots_txt_available}",
        f"- Sitemap rilevate: {len(site_data.sitemap_files)}",
        "",
        "## Score per categoria",
        "",
    ])

    if evaluation.category_scores:
        for category, score in evaluation.category_scores.items():
            lines.append(
                f"- {translate_label(category)}: {score}/100"
            )
    else:
        lines.append(
            "- Nessun impatto categoria rilevato."
        )

    lines.extend([
        "",
        "## Finding",
        "",
    ])

    actionable_findings = [
        finding
        for finding in evaluation.findings
        if finding.score_impact > 0
    ]

    if actionable_findings:
        for finding in actionable_findings:
            source_urls = ", ".join(
                finding.source_urls
            )

            suffix = (
                f" ({source_urls})"
                if source_urls
                else ""
            )

            lines.append(
                "- "
                f"[{translate_label(finding.severity)}] "
                f"{finding.message}"
                f"{suffix}"
            )

    else:
        lines.append(
            "- Nessun finding operativo rilevato."
        )

    lines.extend([
        "",
        "## Conteggio evidenze",
        "",
        f"- Evidenze XEO: {len(search_evidence)}",
    ])

    if performance_data:
        lines.extend([
            f"- Stato performance: {translate_label(performance_data.status)}",
            (
                "- URL performance analizzati: "
                f"{len(performance_data.sampled_urls)}"
            ),
        ])

    if recommendations:
        lines.extend([
            "",
            "## Piano d'azione",
            "",
        ])

        for recommendation in recommendations:
            lines.append(
                "- "
                f"[{recommendation.priority}] "
                f"{recommendation.title}"
            )

            lines.append(
                f"  Rationale: {recommendation.rationale}"
            )

            if recommendation.xeo_explanation:
                lines.append(
                    "  Perche conta per AI/LLM: "
                    f"{recommendation.xeo_explanation}"
                )

            if recommendation.source_urls:
                lines.append(
                    "  URLs: "
                    + ", ".join(
                        recommendation.source_urls
                    )
                )

            if recommendation.actions:
                lines.append(
                    "  Azioni: "
                    + " ".join(
                        recommendation.actions
                    )
                )

    return "\n".join(
        lines
    ).strip() + "\n"


def build_html_report(
    context: AuditContext,
    site_data: SiteData,
    search_evidence: list[SearchEvidence],
    evaluation: AuditEvaluation,
    performance_data: PerformanceData | None = None,
    intelligence_data: IntelligenceData | None = None,
    recommendations: list[AuditRecommendation] | None = None,
    audit_result: AuditResult | None = None,
    demo_mode: bool = False,
) -> str:
    severity_summary = count_findings_by_severity(
        evaluation
    )

    actionable_findings = [
        finding
        for finding in evaluation.findings
        if finding.score_impact > 0
    ]

    category_score_cards = "".join(
        build_metric_card(
            label=translate_label(
                category
            ),
            value=f"{score}/100",
        )
        for category, score in evaluation.category_scores.items()
    )

    if not category_score_cards:
        category_score_cards = build_metric_card(
            label="Category Impact",
            value="None",
        )

    severity_cards = "".join(
        build_metric_card(
            label=translate_label(
                severity
            ),
            value=str(count),
        )
        for severity, count in severity_summary.items()
    )

    if not severity_cards:
        severity_cards = build_metric_card(
            label="Findings",
            value="0",
        )

    recommendation_items = "".join(
        build_recommendation_item(
            recommendation
        )
        for recommendation in recommendations or []
    )

    if not recommendation_items:
        recommendation_items = (
            "<p class=\"muted\">Nessuna raccomandazione generata.</p>"
        )

    finding_items = "".join(
        build_finding_item(
            finding
        )
        for finding in actionable_findings[:12]
    )

    if not finding_items:
        finding_items = (
            "<p class=\"muted\">Nessun problema operativo rilevato.</p>"
        )

    performance_status = (
        translate_label(
            performance_data.status
        )
        if performance_data
        else translate_label(
            "not run"
        )
    )

    sampled_urls = (
        len(performance_data.sampled_urls)
        if performance_data
        else 0
    )

    demo_badge = (
        "<span class=\"badge\">Audit demo</span>"
        if demo_mode
        else ""
    )

    score_explanation = build_score_explanation(
        evaluation
    )

    top_deductions = build_top_deductions(
        actionable_findings
    )

    demo_notice = (
        """
        <div class="notice">
          <strong>Ambito demo:</strong> questo è un campione compatto, non una
          scansione completa del sito. Lo score segnala rischi tecnici e
          semantici che possono limitare crawler, motori di ricerca e sistemi AI.
        </div>
        """
        if demo_mode
        else ""
    )

    pillar_status_cards = build_pillar_status_cards(
        audit_result
    )
    intelligence_section = build_intelligence_section(
        intelligence_data
    )

    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Report XEO Audit</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #141414;
      --muted: #666a73;
      --line: #e7e3dc;
      --paper: #fbfaf7;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-dark: #134e4a;
      --warm: #f3eee5;
      --danger: #b42318;
      --shadow: 0 24px 80px rgba(20, 20, 20, 0.10);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}

    .page {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 24px 72px;
    }}

    .hero {{
      padding: 56px;
      background: var(--ink);
      color: #fff;
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}

    .eyebrow {{
      display: flex;
      gap: 12px;
      align-items: center;
      color: #cbd5d1;
      font-size: 13px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}

    .badge {{
      display: inline-flex;
      padding: 4px 9px;
      border: 1px solid rgba(255,255,255,.28);
      border-radius: 999px;
      color: #ffffff;
      text-transform: none;
    }}

    h1 {{
      margin: 18px 0 12px;
      max-width: 780px;
      font-size: 56px;
      line-height: 1.02;
      letter-spacing: 0;
    }}

    .url {{
      color: #d7ddd9;
      overflow-wrap: anywhere;
      font-size: 18px;
    }}

    .plain-explanation {{
      margin-top: 22px;
      max-width: 760px;
      color: #e8efec;
      font-size: 17px;
    }}

    .score-row {{
      display: grid;
      grid-template-columns: 220px 1fr;
      gap: 28px;
      margin-top: 36px;
      align-items: end;
    }}

    .score {{
      font-size: 84px;
      line-height: .9;
      font-weight: 800;
      letter-spacing: 0;
    }}

    .grade {{
      font-size: 28px;
      color: #9ee6dc;
      font-weight: 700;
    }}

    .score-denominator {{
      font-size: 26px;
      color: #cbd5d1;
      margin-left: 4px;
    }}

    .score-help {{
      display: inline-grid;
      place-items: center;
      width: 24px;
      height: 24px;
      margin-left: 8px;
      border: 1px solid rgba(255,255,255,.38);
      border-radius: 50%;
      color: #fff;
      font-size: 14px;
      cursor: help;
      position: relative;
    }}

    .score-help:hover::after,
    .score-help:focus::after {{
      content: attr(data-tooltip);
      position: absolute;
      z-index: 4;
      left: 0;
      top: 34px;
      width: min(360px, 80vw);
      padding: 14px;
      background: #fff;
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      font-size: 13px;
      line-height: 1.45;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}

    .metric {{
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}

    .metric-label {{
      color: var(--muted);
      font-size: 13px;
    }}

    .metric-value {{
      margin-top: 8px;
      font-size: 24px;
      font-weight: 760;
      color: var(--ink);
    }}

    .notice {{
      margin-top: 18px;
      padding: 16px 18px;
      background: #fff8ea;
      border: 1px solid #ecd7a7;
      border-radius: 8px;
      color: #5d4212;
    }}

    .score-legend {{
      margin-top: 18px;
      display: grid;
      gap: 8px;
      padding: 18px;
      background: #eefaf8;
      border: 1px solid #b8e4de;
      border-radius: 8px;
      color: #123c39;
    }}

    .score-legend-title {{
      font-weight: 800;
    }}

    .score-legend-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
      font-size: 13px;
    }}

    .score-legend-grid span {{
      padding: 8px;
      border-radius: 6px;
      background: #fff;
      border: 1px solid #d4efeb;
    }}

    .keyword-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }}

    .keyword-list span {{
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--ink);
      font-size: 13px;
    }}

    .explain {{
      display: grid;
      gap: 12px;
    }}

    .definition {{
      display: grid;
      gap: 6px;
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}

    .definition strong {{
      font-size: 17px;
    }}

    section {{
      margin-top: 38px;
    }}

    h2 {{
      font-size: 26px;
      margin: 0 0 16px;
      letter-spacing: 0;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}

    .list {{
      display: grid;
      gap: 12px;
    }}

    .item {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
    }}

    .item-head {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      justify-content: space-between;
    }}

    .priority {{
      color: var(--accent-dark);
      background: #dff7f3;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 12px;
      font-weight: 750;
    }}

    .severity {{
      color: var(--danger);
      font-size: 13px;
      font-weight: 760;
      text-transform: uppercase;
    }}

    .item-title {{
      margin: 8px 0;
      font-weight: 760;
      font-size: 18px;
    }}

    .muted {{
      color: var(--muted);
    }}

    .actions {{
      margin: 12px 0 0;
      padding-left: 20px;
    }}

    .actions li {{
      margin: 5px 0;
    }}

    button, .button {{
      border: 0;
      border-radius: 8px;
      padding: 13px 16px;
      background: var(--accent);
      color: #fff;
      font-weight: 760;
      cursor: pointer;
      text-align: center;
      text-decoration: none;
    }}

    .print-bar {{
      display: flex;
      justify-content: flex-end;
      margin: 18px 0 0;
    }}

    @media (max-width: 820px) {{
      .page {{
        padding: 18px 14px 42px;
      }}

      .hero {{
        padding: 32px 24px;
      }}

      h1 {{
        font-size: 40px;
      }}

      .score-row,
      .summary,
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}

    @media print {{
      body {{
        background: #fff;
      }}

      .page {{
        max-width: none;
        padding: 0;
      }}

      .hero,
      .item,
      .metric,
      .cta {{
        box-shadow: none;
      }}

      .print-bar,
      .proposal-note {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div class="eyebrow">XEO Audit {demo_badge}</div>
      <h1>Report tecnico di base per XEO Audit</h1>
      <div class="url">{escape(context.submitted_url)}</div>
      <p class="plain-explanation">
        Questo report mostra lo stato tecnico/Search Readiness disponibile
        oggi. Lo XEO Score completo richiede anche moduli AIgen/LM, keyword
        intelligence e posizionamenti SERP, non ancora implementati.
      </p>
      <div class="score-row">
        <div>
          <div class="score">
            {evaluation.score}<span class="score-denominator">/100</span>
            <span class="score-help" tabindex="0" data-tooltip="Lo score parte da 100. Ogni problema tecnico sottrae punti in base alla severita: critico -15, alto -10, medio -5, basso -2. I problemi ripetuti sono raggruppati e limitati, per evitare che molte pagine con lo stesso difetto azzerino il punteggio in modo artificiale.">?</span>
          </div>
          <div class="grade">Search/Technical {escape(evaluation.grade)}</div>
        </div>
        <div class="summary">
          {build_metric_card("Dispositivo", context.device)}
          {build_metric_card("Pagine analizzate", str(site_data.pages_fetched))}
          {build_metric_card("Problemi", str(len(actionable_findings)))}
          {build_metric_card("Performance", performance_status)}
        </div>
      </div>
      <div class="print-bar">
        <button onclick="window.print()">Scarica PDF</button>
      </div>
    </header>

    {demo_notice}

    <section>
      <h2>Stato XEO Score</h2>
      <div class="notice">
        <strong>XEO Score non disponibile:</strong> secondo il PRD v1.3 il
        punteggio XEO richiede quattro pillar: Search Readiness, AIgen & LM
        Readiness, Web Performance e Keyword Position Performance. In questa
        versione sono disponibili solo i fondamenti tecnici/Search Readiness e
        parte della performance.
      </div>
      <div class="grid">{pillar_status_cards}</div>
    </section>

    {intelligence_section}

    <section>
      <h2>Cosa significa questo score</h2>
      <div class="explain">
        <div class="score-legend">
          <div class="score-legend-title">Legenda scoring</div>
          <div>
            Lo score tecnico parte da 100 per ogni categoria disponibile. Le penalita vengono applicate per
            gravita, raggruppando i problemi ripetuti. Lo score finale è la
            media delle categorie Search/Technical disponibili, non lo XEO Score completo.
          </div>
          <div class="score-legend-grid">
            <span>Critico: -15</span>
            <span>Alto: -10</span>
            <span>Medio: -5</span>
            <span>Basso: -2</span>
            <span>Info: 0</span>
          </div>
        </div>
        <div class="definition">
          <strong>{escape(score_explanation["headline"])}</strong>
          <span class="muted">{escape(score_explanation["body"])}</span>
        </div>
        <div class="definition">
          <strong>Come viene calcolato</strong>
          <span class="muted">
            L'audit parte da 100. I problemi critici sottraggono 15 punti, gli
            alti 10, i medi 5, i bassi 2. I problemi ripetuti dello stesso tipo
            vengono raggruppati, per non trasformare un difetto ricorrente in
            uno zero automatico.
          </span>
        </div>
        <div class="definition">
          <strong>Principali motivi della perdita di punti</strong>
          <span class="muted">{top_deductions}</span>
        </div>
      </div>
    </section>

    <section>
      <h2>Riepilogo severita</h2>
      <div class="grid">{severity_cards}</div>
    </section>

    <section>
      <h2>Score per categoria</h2>
      <div class="grid">{category_score_cards}</div>
    </section>

    <section>
      <h2>Piano d'azione</h2>
      <div class="list">{recommendation_items}</div>
    </section>

    <section>
      <h2>Problemi principali rilevati</h2>
      <div class="list">{finding_items}</div>
    </section>

    <section>
      <h2>Campione analizzato</h2>
      <div class="grid">
        {build_metric_card("Pagine scoperte", str(site_data.pages_discovered))}
        {build_metric_card("Pagine selezionate", str(site_data.pages_selected))}
        {build_metric_card("Sitemaps", str(len(site_data.sitemap_files)))}
        {build_metric_card("Robots.txt", str(site_data.robots_txt_available))}
        {build_metric_card("Evidenze XEO", str(len(search_evidence)))}
        {build_metric_card("URL performance", str(sampled_urls))}
      </div>
    </section>

    <section class="proposal-note">
      <h2>Limite della demo</h2>
      <p class="muted">
        Questa demo usa un campione compatto. Un audit completo dovrebbe
        ampliare la copertura, validare le correzioni e includere segnali
        semantici piu profondi per motori generativi e modelli linguistici.
      </p>
    </section>
  </main>
</body>
</html>
"""


def build_metric_card(
    label: str,
    value: str,
) -> str:
    return (
        "<div class=\"metric\">"
        f"<div class=\"metric-label\">{escape(label)}</div>"
        f"<div class=\"metric-value\">{escape(value)}</div>"
        "</div>"
    )


def build_pillar_status_cards(
    audit_result: AuditResult | None,
) -> str:
    if audit_result is None:
        fallback_pillars = [
            ("Search Readiness", "Disponibile"),
            ("AIgen & LM Readiness", "Non implementato"),
            ("Web Performance", "Parziale"),
            ("Keyword Position Performance", "Non implementato"),
        ]

        return "".join(
            build_metric_card(
                label,
                value,
            )
            for label, value in fallback_pillars
        )

    return "".join(
        build_metric_card(
            pillar.label,
            (
                f"{pillar.score}/100"
                if pillar.score is not None
                else translate_label(
                    pillar.status
                )
            ),
        )
        for pillar in audit_result.pillar_scores
    )


def build_intelligence_section(
    intelligence_data: IntelligenceData | None,
) -> str:
    if intelligence_data is None:
        return """
    <section>
      <h2>Keyword, SERP e LLM</h2>
      <div class="notice">
        Modulo non ancora eseguito in questo report.
      </div>
    </section>
"""

    keyword_items = "".join(
        f"<span>{escape(keyword.keyword)}</span>"
        for keyword in intelligence_data.keywords[:12]
    )

    if not keyword_items:
        keyword_items = "<span>Nessun candidato disponibile</span>"

    return f"""
    <section>
      <h2>Keyword, SERP e LLM</h2>
      <div class="notice">
        <strong>Stato moduli intelligence:</strong> keyword candidate
        {escape(translate_label(intelligence_data.keyword_status))};
        SERP {escape(translate_label(intelligence_data.serp_status))};
        LLM {escape(translate_label(intelligence_data.semantic_status))}.
        Le keyword sotto sono candidate derivate dalle pagine, non ancora
        validate da DataForSEO e non ancora usate per calcolare XEO Score.
      </div>
      <div class="keyword-list">
        {keyword_items}
      </div>
    </section>
"""


def build_recommendation_item(
    recommendation: AuditRecommendation,
) -> str:
    actions = "".join(
        f"<li>{escape(action)}</li>"
        for action in recommendation.actions
    )

    urls = (
        "<p class=\"muted\">"
        + escape(
            ", ".join(
                recommendation.source_urls[:4]
            )
        )
        + "</p>"
        if recommendation.source_urls
        else ""
    )

    return (
        "<article class=\"item\">"
        "<div class=\"item-head\">"
        f"<span class=\"priority\">{escape(recommendation.priority)}</span>"
        f"<span class=\"muted\">{escape(translate_label(recommendation.category))}</span>"
        "</div>"
        f"<div class=\"item-title\">{escape(recommendation.title)}</div>"
        f"<p class=\"muted\">{escape(recommendation.rationale)}</p>"
        f"{build_xeo_explanation(recommendation.xeo_explanation)}"
        f"{urls}"
        f"<ul class=\"actions\">{actions}</ul>"
        "</article>"
    )


def build_xeo_explanation(
    explanation: str,
) -> str:
    if not explanation:
        return ""

    return (
        "<p class=\"muted\"><strong>Perche conta per AI/LLM:</strong> "
        f"{escape(explanation)}</p>"
    )


def build_finding_item(
    finding: object,
) -> str:
    source_urls = getattr(
        finding,
        "source_urls",
        [],
    )

    urls = (
        "<p class=\"muted\">"
        + escape(
            ", ".join(
                source_urls[:3]
            )
        )
        + "</p>"
        if source_urls
        else ""
    )

    return (
        "<article class=\"item\">"
        "<div class=\"item-head\">"
        f"<span class=\"severity\">{escape(translate_label(finding.severity))}</span>"
        f"<span class=\"muted\">-{finding.score_impact} pt</span>"
        "</div>"
        f"<div class=\"item-title\">{escape(finding.message)}</div>"
        f"{urls}"
        "</article>"
    )


def build_score_explanation(
    evaluation: AuditEvaluation,
) -> dict[str, str]:
    if evaluation.score >= 90:
        return {
            "headline": "Base tecnica solida",
            "body": (
                "Il campione mostra pochi rischi tecnici. Il lavoro successivo "
                "riguarda profondita dei contenuti, autorita e conversione."
            ),
        }

    if evaluation.score >= 70:
        return {
            "headline": "Buona base, ma ci sono problemi da correggere",
            "body": (
                "Il sito è migliorabile da una base utilizzabile, ma alcune "
                "evidenze possono ridurre crawlability, indexability o chiarezza "
                "per motori e modelli AI."
            ),
        }

    if evaluation.score >= 40:
        return {
            "headline": "Serve una pulizia tecnica significativa",
            "body": (
                "Il campione contiene problemi con impatto rilevante. Prima "
                "vanno corretti i blocchi tecnici, poi ha senso lavorare sulla "
                "crescita organica."
            ),
        }

    return {
        "headline": "Stato tecnico ad alto rischio",
        "body": (
            "Il campione ha generato molte deduzioni. Non significa che il "
            "business valga zero: significa che, in questa scansione, emergono "
            "problemi tecnici o semantici da sistemare prima di valutare altro."
        ),
    }


def build_top_deductions(
    findings: list[object],
    limit: int = 4,
) -> str:
    scored_findings = sorted(
        findings,
        key=lambda finding: finding.score_impact,
        reverse=True,
    )

    if not scored_findings:
        return "Nessun finding con impatto sul punteggio nel campione."

    labels = [
        (
            f"{finding.message} "
            f"(-{finding.score_impact} punti, {translate_label(finding.severity)})"
        )
        for finding in scored_findings[:limit]
    ]

    return "; ".join(
        labels
    ) + "."


def translate_label(
    value: str,
) -> str:
    labels = {
        "critical": "Critico",
        "high": "Alto",
        "medium": "Medio",
        "low": "Basso",
        "info": "Info",
        "technical": "Tecnica",
        "metadata": "Metadata",
        "headings": "Heading",
        "canonical": "Canonical",
        "indexability": "Indicizzabilita",
        "images": "Immagini",
        "internal_links": "Link interni",
        "structured_data": "Dati strutturati",
        "content_extractability": "Estraibilita contenuto",
        "semantic_clarity": "Chiarezza semantica",
        "answerability": "Answerability",
        "performance": "Performance",
        "mobile": "Mobile",
        "desktop": "Desktop",
        "complete": "Completa",
        "partial": "Parziale",
        "unavailable": "Non disponibile",
        "not run": "Non eseguita",
        "available": "Disponibile",
        "partial": "Parziale",
        "not_implemented": "Non implementato",
        "incomplete": "Incompleto",
        "candidate_only": "solo candidate",
    }

    return labels.get(
        value,
        value,
    )
