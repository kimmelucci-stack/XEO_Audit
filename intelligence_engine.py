from __future__ import annotations

from collections.abc import Iterable
from collections import defaultdict
import re

from models import (
    AuditEvaluation,
    AuditRecommendation,
    EvaluationFinding,
    IntelligenceData,
    KeywordData,
    SerpData,
    SiteData,
)
from providers.dataforseo import DataForSEOProvider
from providers.llm import LLMProvider


PRIORITY_BY_SEVERITY = {
    "critical": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
    "info": "P4",
}


PRIORITY_RANK = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}


STOPWORDS = {
    "alla", "alle", "allo", "anche", "come", "con", "dei", "del",
    "della", "delle", "gli", "il", "in", "la", "le", "nel", "nella",
    "per", "piu", "sul", "sulla", "the", "and", "for", "with", "from",
    "this", "that", "your", "you", "are", "was", "were", "about",
}


def analyze_intelligence(
    site_data: SiteData,
    device: str,
    llm_provider: LLMProvider | None = None,
    dataforseo_provider: DataForSEOProvider | None = None,
) -> IntelligenceData:
    semantic_summary = build_semantic_summary(
        site_data
    )

    llm_provider = llm_provider or LLMProvider()
    dataforseo_provider = dataforseo_provider or DataForSEOProvider()

    llm_result = llm_provider.infer_semantic_context(
        semantic_summary
    )

    keywords = generate_keyword_candidates(
        site_data
    )

    keyword_result = dataforseo_provider.validate_keyword_metrics(
        [
            keyword.keyword
            for keyword in keywords
        ]
    )

    serp_result = dataforseo_provider.fetch_google_serp_live(
        [
            keyword.keyword
            for keyword in keywords[:10]
        ],
        domain=site_data.normalized_host,
        device=device,
    )

    serp_results = [
        SerpData(
            keyword=keyword.keyword,
            device=device,
            status=str(
                serp_result.get(
                    "status",
                    "unavailable",
                )
            ),
            provider="dataforseo",
        )
        for keyword in keywords[:10]
    ]

    errors = []

    for source, result in (
        (
            "llm",
            llm_result,
        ),
        (
            "keyword_metrics",
            keyword_result,
        ),
        (
            "serp_live",
            serp_result,
        ),
    ):
        error = result.get(
            "error"
        )

        if error:
            errors.append({
                "source": source,
                "error": str(
                    error
                ),
            })

    keyword_status = (
        "candidate_only"
        if keywords
        else "unavailable"
    )

    return IntelligenceData(
        status="partial" if keywords else "unavailable",
        semantic_status=str(
            llm_result.get(
                "status",
                "unavailable",
            )
        ),
        keyword_status=keyword_status,
        serp_status=str(
            serp_result.get(
                "status",
                "unavailable",
            )
        ),
        semantic_summary=semantic_summary,
        keywords=keywords,
        serp_results=serp_results,
        errors=errors,
    )


def build_semantic_summary(
    site_data: SiteData,
) -> dict[str, object]:
    pages = []

    for page in site_data.pages[:12]:
        pages.append({
            "url": page.final_url,
            "page_type": page.page_type,
            "title": page.title,
            "meta_description": page.meta_description,
            "h1": page.h1[:3],
            "structured_data_types": page.structured_data_types,
            "visible_text_excerpt": page.visible_text[:700],
        })

    return {
        "host": site_data.normalized_host,
        "pages_sampled": len(
            pages
        ),
        "pages": pages,
    }


def generate_keyword_candidates(
    site_data: SiteData,
    limit: int = 50,
) -> list[KeywordData]:
    phrase_counts = defaultdict(int)

    for page in site_data.pages:
        text_sources = [
            page.title or "",
            page.meta_description or "",
            " ".join(
                page.h1
            ),
            " ".join(
                page.h2[:4]
            ),
        ]

        for text in text_sources:
            for phrase in extract_candidate_phrases(
                text
            ):
                phrase_counts[
                    phrase
                ] += 1

    ranked_phrases = sorted(
        phrase_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    return [
        KeywordData(
            keyword=phrase,
            source="deterministic_page_evidence",
            selected=index < 10,
        )
        for index, (
            phrase,
            _count,
        ) in enumerate(
            ranked_phrases[:limit]
        )
    ]


def extract_candidate_phrases(
    text: str,
) -> list[str]:
    tokens = [
        token
        for token in re.findall(
            r"[a-zA-ZÀ-ÿ0-9]+",
            text.lower(),
        )
        if len(token) >= 3
        and token not in STOPWORDS
    ]

    phrases = []

    for size in (
        2,
        3,
    ):
        for index in range(
            0,
            max(
                0,
                len(tokens) - size + 1,
            ),
        ):
            phrase = " ".join(
                tokens[
                    index:index + size
                ]
            )
            phrases.append(
                phrase
            )

    return phrases


RECOMMENDED_ACTIONS = {
    "http_status_non_200": [
        "Restore a 200 response for the affected URL or redirect it to the correct live page.",
        "Update internal links, canonicals, and sitemap entries that still reference unavailable URLs.",
    ],
    "noindex_detected": [
        "Remove noindex from pages that should appear in search results.",
        "Keep noindex only on pages intentionally excluded from organic discovery.",
    ],
    "canonical_external": [
        "Point the canonical URL to the preferred page on the same site unless cross-domain canonicalization is intentional.",
        "Confirm that the canonical target is indexable and returns a 200 status.",
    ],
    "canonical_mismatch": [
        "Set the canonical URL to the final preferred URL for the page.",
        "Use absolute canonical URLs consistently after redirects are resolved.",
    ],
    "canonical_missing": [
        "Add a canonical link element that points to the preferred final URL.",
        "Keep canonical values consistent with redirects and sitemap URLs.",
    ],
    "title_missing": [
        "Add a unique, descriptive title tag to each affected page.",
        "Prioritize titles that describe the page purpose and primary query intent.",
    ],
    "meta_description_missing": [
        "Add a unique meta description to each affected page.",
        "Use concise copy that reflects the page content and supports search-result snippets.",
    ],
    "h1_missing": [
        "Add one clear H1 that describes the main content of the page.",
        "Align the H1 with the page title without duplicating it mechanically.",
    ],
    "h1_multiple": [
        "Keep one primary H1 per page.",
        "Convert secondary top-level headings to H2 or H3 where appropriate.",
    ],
    "nofollow_detected": [
        "Remove page-level nofollow when internal links should pass discovery signals.",
        "Keep nofollow only where link following is intentionally restricted.",
    ],
    "x_robots_tag_detected": [
        "Review X-Robots-Tag headers for directives that block indexing or following.",
        "Update server rules so indexable pages do not receive restrictive robot headers.",
    ],
    "robots_txt_unavailable": [
        "Publish a reachable robots.txt file at the site root.",
        "Include sitemap references and verify that important sections are not blocked accidentally.",
    ],
    "sitemap_unavailable": [
        "Publish an XML sitemap and expose it from robots.txt.",
        "Include canonical, indexable URLs that return 200 responses.",
    ],
    "images_missing_alt": [
        "Add descriptive alt text to meaningful images.",
        "Use empty alt attributes only for decorative images.",
    ],
    "internal_links_missing_anchor_text": [
        "Add visible, descriptive anchor text to affected internal links.",
        "Avoid empty anchors and image-only links without accessible labels.",
    ],
    "no_internal_links": [
        "Add relevant internal links from the page to related site sections.",
        "Use descriptive anchor text that clarifies the destination.",
    ],
    "no_observed_inbound_links": [
        "Link to the page from relevant crawlable pages.",
        "Prioritize links from navigation, hub pages, or closely related content.",
    ],
    "redirect_detected": [
        "Update internal references to point directly to the final URL.",
        "Keep redirects only where they are needed for legacy or external traffic.",
    ],
    "duplicate_title": [
        "Rewrite duplicate title tags so each indexed page has a distinct purpose.",
        "Keep shared brand suffixes, but make the page-specific part unique.",
    ],
    "duplicate_meta_description": [
        "Rewrite duplicate meta descriptions to reflect each page's unique content.",
        "Avoid boilerplate descriptions across indexable pages.",
    ],
    "performance_data_unavailable": [
        "Configure Google API access if field and lab performance data is required.",
        "Retry the audit after confirming the tested URL is publicly reachable.",
    ],
    "poor_lighthouse_score": [
        "Address the largest Lighthouse performance opportunities first.",
        "Focus on render-blocking work, large assets, JavaScript execution, and layout stability.",
    ],
    "needs_improvement_lighthouse_score": [
        "Review Lighthouse diagnostics and fix the highest-impact opportunities.",
        "Retest the same device profile after each performance change.",
    ],
}

ITALIAN_ACTIONS = {
    "title_missing": [
        "Aggiungi un title unico e descrittivo per ogni pagina coinvolta.",
        "Chiarisci nel title il tema principale e l'intento della pagina.",
    ],
    "meta_description_missing": [
        "Aggiungi una meta description unica e leggibile.",
        "Riassumi il contenuto in modo utile per snippet e sistemi AI.",
    ],
    "h1_missing": [
        "Aggiungi un H1 principale che descriva il contenuto della pagina.",
        "Allinea H1 e title senza duplicarli meccanicamente.",
    ],
    "canonical_missing": [
        "Aggiungi un canonical verso l'URL finale preferito.",
        "Mantieni canonical, redirect e sitemap coerenti.",
    ],
    "sitemap_unavailable": [
        "Pubblica una sitemap XML raggiungibile.",
        "Includi URL canonici, indicizzabili e con status 200.",
    ],
    "robots_txt_unavailable": [
        "Pubblica un file robots.txt alla root del sito.",
        "Verifica che non blocchi sezioni importanti per crawler e AI.",
    ],
    "no_internal_links": [
        "Aggiungi link interni rilevanti verso pagine correlate.",
        "Usa anchor text descrittivi e comprensibili.",
    ],
    "no_observed_inbound_links": [
        "Collega la pagina da altre pagine crawlable del sito.",
        "Dai priorita a navigazione, hub tematici e contenuti correlati.",
    ],
    "internal_links_missing_anchor_text": [
        "Aggiungi anchor text visibile e descrittivo ai link interni.",
        "Evita link vuoti o solo visuali senza label accessibile.",
    ],
    "images_missing_alt": [
        "Aggiungi alt text descrittivo alle immagini informative.",
        "Usa alt vuoto solo per immagini decorative.",
    ],
    "performance_data_unavailable": [
        "Configura l'accesso alle API Google se vuoi includere dati performance.",
        "Verifica che l'URL sia pubblico e raggiungibile.",
    ],
}


XEO_EXPLANATIONS = {
    "http_status_non_200": (
        "Crawler, motori di ricerca e sistemi AI non possono usare una pagina "
        "che non risponde correttamente: l'evidenza riduce crawlability e "
        "affidabilita della fonte."
    ),
    "noindex_detected": (
        "Una pagina noindex puo essere esclusa dagli indici e quindi anche "
        "dai sistemi che recuperano contenuti indicizzati per risposte e "
        "citazioni."
    ),
    "canonical_external": (
        "Un canonical esterno trasferisce il segnale di preferenza fuori dal "
        "dominio: puo rendere meno chiaro quale contenuto del sito debba "
        "essere citato."
    ),
    "canonical_mismatch": (
        "Canonical, redirect e URL finale incoerenti rendono piu difficile "
        "stabilire la pagina autorevole da indicizzare, sintetizzare e citare."
    ),
    "canonical_missing": (
        "Il canonical aiuta a identificare la versione preferita di un "
        "contenuto. Senza questo segnale, duplicati e varianti URL possono "
        "diluire l'interpretazione della pagina."
    ),
    "title_missing": (
        "Il title e uno dei segnali piu forti per capire il tema della pagina. "
        "Se manca, crawler e sistemi AI hanno meno contesto per classificare "
        "e riassumere il contenuto."
    ),
    "meta_description_missing": (
        "La meta description non determina da sola il ranking, ma fornisce un "
        "riassunto controllato che aiuta snippet, preview e sistemi AI a "
        "capire il valore della pagina."
    ),
    "h1_missing": (
        "Un H1 chiaro rende esplicito il tema principale della pagina. Senza "
        "una gerarchia semantica stabile, l'estrazione del contenuto diventa "
        "meno affidabile."
    ),
    "h1_multiple": (
        "Troppi H1 possono rendere ambiguo il tema primario della pagina. Una "
        "gerarchia heading pulita aiuta crawler e modelli a distinguere titolo "
        "principale e sezioni."
    ),
    "nofollow_detected": (
        "Il nofollow a livello pagina puo limitare la scoperta delle relazioni "
        "interne. Questo indebolisce il contesto che crawler e sistemi AI usano "
        "per comprendere il sito."
    ),
    "x_robots_tag_detected": (
        "Gli header X-Robots-Tag possono bloccare indexing, following o snippet. "
        "Vanno verificati per evitare restrizioni invisibili nel markup HTML."
    ),
    "robots_txt_unavailable": (
        "robots.txt e un punto di controllo standard per crawler. Se manca o "
        "non e raggiungibile, il sito fornisce meno indicazioni operative su "
        "cosa puo essere esplorato."
    ),
    "sitemap_unavailable": (
        "La sitemap facilita scoperta, priorita e aggiornamento delle pagine. "
        "Senza sitemap, crawler e pipeline AI hanno meno percorsi espliciti "
        "verso i contenuti canonici."
    ),
    "images_missing_alt": (
        "L'alt text trasforma immagini informative in segnali testuali. Questo "
        "migliora accessibilita, comprensione visuale indiretta e contesto per "
        "sistemi che estraggono informazioni dalla pagina."
    ),
    "internal_links_missing_anchor_text": (
        "Anchor text vuoti o generici riducono il contesto sui collegamenti. "
        "Link descrittivi aiutano crawler e modelli a capire relazioni e "
        "destinazioni."
    ),
    "no_internal_links": (
        "Una pagina senza link interni offre pochi percorsi di scoperta e poco "
        "contesto relazionale. Questo limita la comprensione della sua posizione "
        "nel sito."
    ),
    "no_observed_inbound_links": (
        "Se una pagina non riceve link interni osservati, puo apparire isolata. "
        "Le pagine isolate sono piu deboli per scoperta, priorita e citazione."
    ),
    "redirect_detected": (
        "Redirect interni evitabili consumano budget di crawl e possono confondere "
        "la catena di segnali tra URL richiesto, URL finale e canonical."
    ),
    "duplicate_title": (
        "Title duplicati rendono meno distinguibili pagine diverse. Per sistemi "
        "AI e motori di ricerca, questo riduce chiarezza di intent e selezione "
        "della pagina piu pertinente."
    ),
    "duplicate_meta_description": (
        "Descrizioni duplicate indeboliscono il riassunto specifico di ogni "
        "pagina. Ogni URL importante dovrebbe comunicare il proprio ruolo in "
        "modo distinto."
    ),
    "performance_data_unavailable": (
        "Senza dati performance non e possibile valutare stabilita e usabilita "
        "del contenuto nel campione. Il pillar Web Performance resta quindi "
        "non calcolabile."
    ),
    "poor_lighthouse_score": (
        "Performance molto basse possono impedire agli utenti di fruire il "
        "contenuto e rendere piu costoso il rendering per crawler e sistemi "
        "di analisi."
    ),
    "needs_improvement_lighthouse_score": (
        "Performance migliorabili possono ridurre accessibilita pratica del "
        "contenuto. Tempi e stabilita incidono sulla capacita di usare e "
        "valutare la pagina."
    ),
}


DEFAULT_XEO_EXPLANATION = (
    "Questa evidenza incide sulla capacita del sito di essere scoperto, "
    "interpretato e citato da motori di ricerca e sistemi AI."
)


def build_recommendations(
    evaluation: AuditEvaluation,
    limit: int | None = None,
) -> list[AuditRecommendation]:
    grouped_findings: dict[str, list[EvaluationFinding]] = defaultdict(list)

    for finding in evaluation.findings:
        if finding.score_impact <= 0:
            continue

        grouped_findings[
            finding.finding_id
        ].append(
            finding
        )

    recommendations = [
        build_recommendation(
            finding_id,
            findings,
        )
        for finding_id, findings in grouped_findings.items()
    ]

    recommendations.sort(
        key=lambda recommendation: (
            PRIORITY_RANK.get(
                recommendation.priority,
                99,
            ),
            -sum(
                finding.score_impact
                for finding in grouped_findings[
                    recommendation.recommendation_id
                ]
            ),
            recommendation.category,
            recommendation.title,
        )
    )

    if limit is None:
        return recommendations

    return recommendations[
        :limit
    ]


def build_recommendation(
    finding_id: str,
    findings: list[EvaluationFinding],
) -> AuditRecommendation:
    primary_finding = findings[0]
    total_impact = sum(
        finding.score_impact
        for finding in findings
    )

    source_urls = unique_values(
        url
        for finding in findings
        for url in finding.source_urls
    )

    priority = PRIORITY_BY_SEVERITY.get(
        primary_finding.severity,
        "P3",
    )

    occurrence_label = (
        "1 occorrenza"
        if len(findings) == 1
        else f"{len(findings)} occorrenze"
    )

    return AuditRecommendation(
        recommendation_id=finding_id,
        priority=priority,
        category=primary_finding.category,
        title=primary_finding.message,
        rationale=(
            f"{occurrence_label} rilevate, con impatto stimato "
            f"di {total_impact} punti sullo score."
        ),
        xeo_explanation=XEO_EXPLANATIONS.get(
            finding_id,
            DEFAULT_XEO_EXPLANATION,
        ),
        source_urls=source_urls,
        actions=ITALIAN_ACTIONS.get(
            finding_id,
            [
                "Analizza l'evidenza rilevata e aggiorna la pagina.",
                "Ripeti l'audit dopo la pubblicazione della correzione.",
            ],
        ),
        finding_ids=[
            finding.finding_id
            for finding in findings
        ],
    )


def unique_values(
    values: Iterable[str],
) -> list[str]:
    unique = []
    seen = set()

    for value in values:
        if value in seen:
            continue

        seen.add(
            value
        )
        unique.append(
            value
        )

    return unique
