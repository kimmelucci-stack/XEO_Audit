from dataclasses import dataclass, field


@dataclass
class AuditContext:
    submitted_url: str
    device: str = "mobile"

    language: str | None = None
    location: str | None = None

    audit_id: str | None = None
    timestamp: str | None = None
    scoring_version: str | None = None

    persistence_key: str | None = None


@dataclass
class PageData:
    source_url: str
    final_url: str
    status_code: int

    redirect_history: list[str] = field(default_factory=list)
    crawl_timestamp: str | None = None

    page_type: str | None = None

    title: str | None = None
    meta_description: str | None = None

    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)

    canonical: str | None = None

    robots_noindex: bool | None = None
    robots_nofollow: bool | None = None
    x_robots_tag: str | None = None

    structured_data_types: list[str] = field(default_factory=list)

    internal_links: list[str] = field(default_factory=list)
    internal_link_anchors: list[dict[str, str]] = field(
        default_factory=list
    )

    image_count: int = 0
    images_missing_alt: int = 0
    image_evidence: list[dict[str, str | None]] = field(
        default_factory=list
    )

    visible_text: str = ""


@dataclass
class SiteData:
    submitted_url: str
    normalized_host: str

    pages: list[PageData] = field(default_factory=list)

    robots_txt_url: str | None = None
    robots_txt_available: bool | None = None

    sitemap_files: list[str] = field(default_factory=list)
    sitemap_page_urls: list[str] = field(default_factory=list)

    internal_link_graph: dict[str, list[str]] = field(default_factory=dict)

    crawl_started_at: str | None = None
    crawl_completed_at: str | None = None

    pages_discovered: int = 0
    pages_selected: int = 0
    pages_fetched: int = 0

    persistence_directory: str | None = None
    persistence_complete: bool = False

    fetch_errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PagePerformanceData:
    url: str
    device: str

    crux_status: str = "unavailable"
    crux_scope: str | None = None
    crux_metrics: dict[str, object] = field(default_factory=dict)

    lighthouse_status: str = "unavailable"
    lighthouse_score: float | None = None
    lighthouse_metrics: dict[str, object] = field(default_factory=dict)
    lighthouse_diagnostics: list[dict[str, object]] = field(
        default_factory=list
    )

    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PerformanceData:
    device: str
    sampled_urls: list[str] = field(default_factory=list)
    pages: list[PagePerformanceData] = field(default_factory=list)

    field_data_available: bool = False
    lab_data_available: bool = False

    status: str = "unavailable"
    provenance: dict[str, object] = field(default_factory=dict)


@dataclass
class SearchEvidence:
    evidence_id: str
    category: str
    scope: str

    source_urls: list[str] = field(
        default_factory=list
    )

    observed: dict[str, object] = field(
        default_factory=dict
    )

    method: str = "deterministic"


@dataclass
class EvaluationFinding:
    finding_id: str
    category: str
    severity: str
    score_impact: int

    source_urls: list[str] = field(
        default_factory=list
    )

    observed: dict[str, object] = field(
        default_factory=dict
    )

    message: str = ""


@dataclass
class PillarScore:
    pillar_id: str
    label: str
    status: str
    score: int | None = None
    weight: float | None = None
    summary: str = ""


@dataclass
class KeywordData:
    keyword: str
    intent: str | None = None
    cluster: str | None = None
    source: str = "unavailable"
    metrics: dict[str, object] = field(default_factory=dict)
    selected: bool = False


@dataclass
class SerpData:
    keyword: str
    device: str
    status: str = "unavailable"
    position: int | None = None
    ranking_url: str | None = None
    observed_at: str | None = None
    provider: str | None = None


@dataclass
class IntelligenceData:
    status: str = "unavailable"
    semantic_status: str = "unavailable"
    keyword_status: str = "unavailable"
    serp_status: str = "unavailable"

    semantic_summary: dict[str, object] = field(default_factory=dict)
    keywords: list[KeywordData] = field(default_factory=list)
    serp_results: list[SerpData] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class AuditEvaluation:
    score: int
    grade: str
    score_label: str = "Search / Technical Readiness"

    xeo_score: int | None = None
    xeo_status: str = "incomplete"

    findings: list[EvaluationFinding] = field(
        default_factory=list
    )

    category_scores: dict[str, int] = field(
        default_factory=dict
    )

    status: str = "complete"


@dataclass
class AuditResult:
    context: AuditContext
    technical_eligibility: str = "warning"
    xeo_score: int | None = None
    xeo_status: str = "incomplete"
    pillar_scores: list[PillarScore] = field(default_factory=list)
    findings: list[EvaluationFinding] = field(default_factory=list)
    recommendations: list["AuditRecommendation"] = field(default_factory=list)
    keywords: list[KeywordData] = field(default_factory=list)
    serp_results: list[SerpData] = field(default_factory=list)


@dataclass
class AuditRecommendation:
    recommendation_id: str
    priority: str
    category: str
    title: str
    rationale: str
    xeo_explanation: str = ""

    source_urls: list[str] = field(
        default_factory=list
    )

    actions: list[str] = field(
        default_factory=list
    )

    finding_ids: list[str] = field(
        default_factory=list
    )
