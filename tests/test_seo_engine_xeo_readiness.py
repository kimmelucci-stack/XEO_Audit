from models import PageData, SiteData
from seo_engine import analyze_search_readiness


def test_low_extractable_content_generates_xeo_evidence():
    page = PageData(
        source_url="https://example.com/service/",
        final_url="https://example.com/service/",
        status_code=200,
        title="AI consulting",
        h1=[
            "AI consulting"
        ],
        canonical="https://example.com/service/",
        internal_links=[
            "https://example.com/"
        ],
        visible_text="AI consulting for teams.",
    )

    evidence = analyze_search_readiness(
        SiteData(
            submitted_url="https://example.com/",
            normalized_host="example.com",
            pages=[
                page
            ],
            sitemap_files=[
                "https://example.com/sitemap.xml"
            ],
        )
    )

    extractability_evidence = [
        item
        for item in evidence
        if item.evidence_id == "content_extractability_low"
    ]

    assert len(
        extractability_evidence
    ) == 1
    assert extractability_evidence[0].category == "content_extractability"
    assert extractability_evidence[0].method == "heuristic"
    assert extractability_evidence[0].observed["visible_word_count"] == 4


def test_misaligned_title_and_h1_generates_entity_context_evidence():
    page = PageData(
        source_url="https://example.com/service/",
        final_url="https://example.com/service/",
        status_code=200,
        title="AI consulting for manufacturers",
        h1=[
            "Cloud migration roadmap"
        ],
        canonical="https://example.com/service/",
        internal_links=[
            "https://example.com/"
        ],
        visible_text=" ".join(
            [
                "Detailed consulting content"
                for _ in range(
                    90
                )
            ]
        ),
    )

    evidence = analyze_search_readiness(
        SiteData(
            submitted_url="https://example.com/",
            normalized_host="example.com",
            pages=[
                page
            ],
            sitemap_files=[
                "https://example.com/sitemap.xml"
            ],
        )
    )

    entity_evidence = [
        item
        for item in evidence
        if item.evidence_id == "entity_context_weak"
    ]

    assert len(
        entity_evidence
    ) == 1
    assert entity_evidence[0].category == "semantic_clarity"
    assert entity_evidence[0].observed["title"] == (
        "AI consulting for manufacturers"
    )


def test_long_unsectioned_content_generates_answerability_evidence():
    page = PageData(
        source_url="https://example.com/guide/",
        final_url="https://example.com/guide/",
        status_code=200,
        title="AI readiness guide",
        h1=[
            "AI readiness guide"
        ],
        canonical="https://example.com/guide/",
        internal_links=[
            "https://example.com/"
        ],
        visible_text=" ".join(
            [
                "answerable content"
                for _ in range(
                    70
                )
            ]
        ),
    )

    evidence = analyze_search_readiness(
        SiteData(
            submitted_url="https://example.com/",
            normalized_host="example.com",
            pages=[
                page
            ],
            sitemap_files=[
                "https://example.com/sitemap.xml"
            ],
        )
    )

    answerability_evidence = [
        item
        for item in evidence
        if item.evidence_id == "answerability_structure_weak"
    ]

    assert len(
        answerability_evidence
    ) == 1
    assert answerability_evidence[0].category == "answerability"
    assert answerability_evidence[0].observed["h2_count"] == 0


def test_commercial_page_without_schema_generates_structured_facts_evidence():
    page = PageData(
        source_url="https://example.com/product/",
        final_url="https://example.com/product/",
        status_code=200,
        page_type="commercial",
        title="AI audit platform",
        h1=[
            "AI audit platform"
        ],
        h2=[
            "Features"
        ],
        canonical="https://example.com/product/",
        internal_links=[
            "https://example.com/"
        ],
        visible_text=" ".join(
            [
                "platform feature"
                for _ in range(
                    30
                )
            ]
        ),
    )

    evidence = analyze_search_readiness(
        SiteData(
            submitted_url="https://example.com/",
            normalized_host="example.com",
            pages=[
                page
            ],
            sitemap_files=[
                "https://example.com/sitemap.xml"
            ],
        )
    )

    structured_facts_evidence = [
        item
        for item in evidence
        if item.evidence_id == "structured_facts_missing"
    ]

    assert len(
        structured_facts_evidence
    ) == 1
    assert structured_facts_evidence[0].category == "structured_data"
    assert structured_facts_evidence[0].observed["page_type"] == "commercial"


if __name__ == "__main__":
    test_low_extractable_content_generates_xeo_evidence()
    test_misaligned_title_and_h1_generates_entity_context_evidence()
    test_long_unsectioned_content_generates_answerability_evidence()
    test_commercial_page_without_schema_generates_structured_facts_evidence()

    print(
        "seo engine xeo readiness: OK"
    )
