import re
from urllib.parse import urljoin, urlparse

from models import SearchEvidence, SiteData


MIN_EXTRACTABLE_WORDS = 80
MIN_STRUCTURED_FACT_WORDS = 40
MIN_ANSWERABLE_WORDS = 120

SEMANTIC_STOPWORDS = {
    "and",
    "are",
    "con",
    "dei",
    "del",
    "della",
    "for",
    "gli",
    "il",
    "in",
    "la",
    "le",
    "per",
    "the",
    "una",
    "uno",
    "with",
}


def analyze_search_readiness(
    site_data: SiteData,
) -> list[SearchEvidence]:
    evidence = []

    # ---------------------------------------------------------
    # SITE-LEVEL TECHNICAL EVIDENCE
    # ---------------------------------------------------------

    if site_data.robots_txt_available is False:
        source_urls = []

        if site_data.robots_txt_url:
            source_urls.append(
                site_data.robots_txt_url
            )

        evidence.append(
            SearchEvidence(
                evidence_id="robots_txt_unavailable",
                category="technical",
                scope="site",
                source_urls=source_urls,
                observed={
                    "robots_txt_url": site_data.robots_txt_url,
                    "robots_txt_available": False,
                },
                method="deterministic",
            )
        )

    if site_data.sitemap_files:
        evidence.append(
            SearchEvidence(
                evidence_id="sitemap_detected",
                category="technical",
                scope="site",
                source_urls=site_data.sitemap_files,
                observed={
                    "sitemap_files": site_data.sitemap_files,
                    "sitemap_file_count": len(
                        site_data.sitemap_files
                    ),
                    "sitemap_page_url_count": len(
                        site_data.sitemap_page_urls
                    ),
                },
                method="deterministic",
            )
        )
    else:
        evidence.append(
            SearchEvidence(
                evidence_id="sitemap_unavailable",
                category="technical",
                scope="site",
                source_urls=[],
                observed={
                    "sitemap_files": [],
                    "sitemap_page_url_count": len(
                        site_data.sitemap_page_urls
                    ),
                },
                method="deterministic",
            )
        )

    # ---------------------------------------------------------
    # PAGE-LEVEL DETERMINISTIC EVIDENCE
    # ---------------------------------------------------------

    for page in site_data.pages:
        if page.status_code != 200:
            evidence.append(
                SearchEvidence(
                    evidence_id="http_status_non_200",
                    category="technical",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "source_url": page.source_url,
                        "final_url": page.final_url,
                        "status_code": page.status_code,
                    },
                    method="deterministic",
                )
            )

        if page.redirect_history:
            evidence.append(
                SearchEvidence(
                    evidence_id="redirect_detected",
                    category="technical",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "source_url": page.source_url,
                        "final_url": page.final_url,
                        "redirect_history": (
                            page.redirect_history
                        ),
                        "redirect_count": len(
                            page.redirect_history
                        ),
                    },
                    method="deterministic",
                )
            )

        if not page.title:
            evidence.append(
                SearchEvidence(
                    evidence_id="title_missing",
                    category="metadata",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "title": page.title,
                    },
                    method="deterministic",
                )
            )

        if not page.meta_description:
            evidence.append(
                SearchEvidence(
                    evidence_id="meta_description_missing",
                    category="metadata",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "meta_description": page.meta_description,
                    },
                    method="deterministic",
                )
            )

        if not page.h1:
            evidence.append(
                SearchEvidence(
                    evidence_id="h1_missing",
                    category="headings",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "h1": page.h1,
                    },
                    method="deterministic",
                )
            )

        if len(page.h1) > 1:
            evidence.append(
                SearchEvidence(
                    evidence_id="h1_multiple",
                    category="headings",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "h1": page.h1,
                        "count": len(
                            page.h1
                        ),
                    },
                    method="deterministic",
                )
            )

        # -----------------------------------------------------
        # CANONICAL
        # -----------------------------------------------------

        if not page.canonical:
            evidence.append(
                SearchEvidence(
                    evidence_id="canonical_missing",
                    category="canonical",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "canonical": page.canonical,
                    },
                    method="deterministic",
                )
            )

        else:
            resolved_canonical = urljoin(
                page.final_url,
                page.canonical,
            )

            if resolved_canonical != page.final_url:
                evidence.append(
                    SearchEvidence(
                        evidence_id="canonical_mismatch",
                        category="canonical",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "final_url": page.final_url,
                            "canonical": page.canonical,
                        },
                        method="deterministic",
                    )
                )

            canonical_host = urlparse(
                resolved_canonical
            ).hostname

            final_host = urlparse(
                page.final_url
            ).hostname

            if (
                canonical_host
                and final_host
                and canonical_host.lower()
                != final_host.lower()
            ):
                evidence.append(
                    SearchEvidence(
                        evidence_id="canonical_external",
                        category="canonical",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "final_url": page.final_url,
                            "canonical": page.canonical,
                        },
                        method="deterministic",
                    )
                )

        # -----------------------------------------------------
        # INDEXABILITY
        # -----------------------------------------------------

        if page.robots_noindex:
            evidence.append(
                SearchEvidence(
                    evidence_id="noindex_detected",
                    category="indexability",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "robots_noindex": True,
                    },
                    method="deterministic",
                )
            )

        if page.robots_nofollow:
            evidence.append(
                SearchEvidence(
                    evidence_id="nofollow_detected",
                    category="indexability",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "robots_nofollow": True,
                    },
                    method="deterministic",
                )
            )

        if page.x_robots_tag:
            evidence.append(
                SearchEvidence(
                    evidence_id="x_robots_tag_detected",
                    category="indexability",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "x_robots_tag": page.x_robots_tag,
                    },
                    method="deterministic",
                )
            )

        # -----------------------------------------------------
        # IMAGE HYGIENE
        # -----------------------------------------------------

        if page.images_missing_alt > 0:
            evidence.append(
                SearchEvidence(
                    evidence_id="images_missing_alt",
                    category="images",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "image_count": page.image_count,
                        "images_missing_alt": (
                            page.images_missing_alt
                        ),
                    },
                    method="deterministic",
                )
            )

        # -----------------------------------------------------
        # INTERNAL LINKS
        # -----------------------------------------------------

        if not page.internal_links:
            evidence.append(
                SearchEvidence(
                    evidence_id="no_internal_links",
                    category="internal_links",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "internal_link_count": 0,
                    },
                    method="deterministic",
                )
            )

        links_missing_anchor_text = []

        for link in page.internal_link_anchors:
            anchor_text = link.get(
                "anchor_text"
            )

            if anchor_text and anchor_text.strip():
                continue

            links_missing_anchor_text.append(
                link
            )

        if links_missing_anchor_text:
            evidence.append(
                SearchEvidence(
                    evidence_id=(
                        "internal_links_missing_anchor_text"
                    ),
                    category="internal_links",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "count": len(
                            links_missing_anchor_text
                        ),
                        "links": links_missing_anchor_text,
                    },
                    method="deterministic",
                )
            )

        # -----------------------------------------------------
        # STRUCTURED DATA
        # -----------------------------------------------------

        if page.structured_data_types:
            evidence.append(
                SearchEvidence(
                    evidence_id="structured_data_detected",
                    category="structured_data",
                    scope="page",
                    source_urls=[
                        page.final_url
                    ],
                    observed={
                        "structured_data_types": (
                            page.structured_data_types
                        ),
                        "count": len(
                            page.structured_data_types
                        ),
                    },
                    method="deterministic",
                )
            )

        # -----------------------------------------------------
        # XEO / AI READINESS HEURISTICS
        # -----------------------------------------------------

        if is_page_candidate_for_xeo_checks(page):
            words = extract_words(
                page.visible_text
            )

            if len(words) < MIN_EXTRACTABLE_WORDS:
                evidence.append(
                    SearchEvidence(
                        evidence_id="content_extractability_low",
                        category="content_extractability",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "visible_word_count": len(
                                words
                            ),
                            "minimum_expected_word_count": (
                                MIN_EXTRACTABLE_WORDS
                            ),
                        },
                        method="heuristic",
                    )
                )

            title_terms = extract_significant_terms(
                page.title or ""
            )
            h1_terms = extract_significant_terms(
                " ".join(
                    page.h1
                )
            )

            if (
                title_terms
                and h1_terms
                and title_terms.isdisjoint(
                    h1_terms
                )
            ):
                evidence.append(
                    SearchEvidence(
                        evidence_id="entity_context_weak",
                        category="semantic_clarity",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "title": page.title,
                            "h1": page.h1,
                            "title_terms": sorted(
                                title_terms
                            ),
                            "h1_terms": sorted(
                                h1_terms
                            ),
                        },
                        method="heuristic",
                    )
                )

            if (
                len(words) >= MIN_ANSWERABLE_WORDS
                and not page.h2
                and not page.h3
            ):
                evidence.append(
                    SearchEvidence(
                        evidence_id="answerability_structure_weak",
                        category="answerability",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "visible_word_count": len(
                                words
                            ),
                            "h2_count": len(
                                page.h2
                            ),
                            "h3_count": len(
                                page.h3
                            ),
                        },
                        method="heuristic",
                    )
                )

            if (
                not page.structured_data_types
                and page.page_type
                in (
                    "commercial",
                    "editorial",
                )
                and len(words) >= MIN_STRUCTURED_FACT_WORDS
            ):
                evidence.append(
                    SearchEvidence(
                        evidence_id="structured_facts_missing",
                        category="structured_data",
                        scope="page",
                        source_urls=[
                            page.final_url
                        ],
                        observed={
                            "page_type": page.page_type,
                            "structured_data_types": [],
                            "visible_word_count": len(
                                words
                            ),
                        },
                        method="heuristic",
                    )
                )

    # ---------------------------------------------------------
    # SITE-LEVEL DUPLICATE TITLES
    # ---------------------------------------------------------

    titles_to_urls = {}

    for page in site_data.pages:
        if not page.title:
            continue

        titles_to_urls.setdefault(
            page.title,
            [],
        ).append(
            page.final_url
        )

    for (
        title,
        urls,
    ) in titles_to_urls.items():
        if len(urls) <= 1:
            continue

        evidence.append(
            SearchEvidence(
                evidence_id="duplicate_title",
                category="metadata",
                scope="site",
                source_urls=urls,
                observed={
                    "title": title,
                    "count": len(
                        urls
                    ),
                },
                method="deterministic",
            )
        )

    # ---------------------------------------------------------
    # SITE-LEVEL DUPLICATE META DESCRIPTIONS
    # ---------------------------------------------------------

    descriptions_to_urls = {}

    for page in site_data.pages:
        if not page.meta_description:
            continue

        descriptions_to_urls.setdefault(
            page.meta_description,
            [],
        ).append(
            page.final_url
        )

    for (
        meta_description,
        urls,
    ) in descriptions_to_urls.items():
        if len(urls) <= 1:
            continue

        evidence.append(
            SearchEvidence(
                evidence_id=(
                    "duplicate_meta_description"
                ),
                category="metadata",
                scope="site",
                source_urls=urls,
                observed={
                    "meta_description": (
                        meta_description
                    ),
                    "count": len(
                        urls
                    ),
                },
                method="deterministic",
            )
        )

    # ---------------------------------------------------------
    # OBSERVED INBOUND LINKS
    #
    # Heuristic because the crawl is representative,
    # not exhaustive.
    # ---------------------------------------------------------

    observed_inbound_counts = {
        page.final_url: 0
        for page in site_data.pages
    }

    for (
        source_url,
        linked_urls,
    ) in site_data.internal_link_graph.items():
        for linked_url in linked_urls:
            if (
                linked_url
                in observed_inbound_counts
            ):
                observed_inbound_counts[
                    linked_url
                ] += 1

    homepage_url = (
        site_data.submitted_url
    )

    for (
        page_url,
        inbound_count,
    ) in observed_inbound_counts.items():
        if page_url == homepage_url:
            continue

        if inbound_count > 0:
            continue

        evidence.append(
            SearchEvidence(
                evidence_id=(
                    "no_observed_inbound_links"
                ),
                category="internal_links",
                scope="page",
                source_urls=[
                    page_url
                ],
                observed={
                    "observed_inbound_link_count": 0,
                },
                method="heuristic",
            )
        )

    return evidence


def is_page_candidate_for_xeo_checks(
    page: object,
) -> bool:
    return (
        getattr(
            page,
            "status_code",
            None,
        )
        == 200
        and not getattr(
            page,
            "robots_noindex",
            False,
        )
    )


def extract_words(
    text: str,
) -> list[str]:
    return re.findall(
        r"[^\W_]+",
        text.lower(),
    )


def extract_significant_terms(
    text: str,
) -> set[str]:
    return {
        word
        for word in extract_words(
            text
        )
        if len(
            word
        )
        >= 3
        and word not in SEMANTIC_STOPWORDS
    }
