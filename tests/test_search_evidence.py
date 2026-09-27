from models import SearchEvidence


def test_search_evidence_defaults():
    evidence = SearchEvidence(
        evidence_id="title_missing",
        category="metadata",
        scope="page",
    )

    assert evidence.evidence_id == "title_missing"
    assert evidence.category == "metadata"
    assert evidence.scope == "page"

    assert evidence.source_urls == []
    assert evidence.observed == {}
    assert evidence.method == "deterministic"


def test_search_evidence_observed_data():
    evidence = SearchEvidence(
        evidence_id="title_missing",
        category="metadata",
        scope="page",
        source_urls=[
            "https://example.com/about/"
        ],
        observed={
            "title": None,
        },
    )

    assert evidence.source_urls == [
        "https://example.com/about/"
    ]

    assert evidence.observed == {
        "title": None,
    }

    assert evidence.method == "deterministic"


if __name__ == "__main__":
    test_search_evidence_defaults()
    test_search_evidence_observed_data()

    print(
        "search evidence model: OK"
    )