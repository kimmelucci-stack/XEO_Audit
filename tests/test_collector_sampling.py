from collector import select_representative_sample


def test_representative_sample_respects_cap_and_mix():
    homepage = [
        "https://example.com/"
    ]

    editorial = [
        f"https://example.com/blog/article-{i}"
        for i in range(40)
    ]

    commercial = [
        f"https://example.com/services/service-{i}"
        for i in range(40)
    ]

    candidates = (
        homepage
        + editorial
        + commercial
    )

    selected = select_representative_sample(
        candidates
    )

    assert len(selected) == 50

    assert "https://example.com/" in selected

    selected_editorial = [
        url
        for url in selected
        if "/blog/" in url
    ]

    selected_commercial = [
        url
        for url in selected
        if "/services/" in url
    ]

    assert selected_editorial
    assert selected_commercial


def test_representative_sample_uses_all_when_below_cap():
    candidates = [
        "https://example.com/"
    ] + [
        f"https://example.com/blog/article-{i}"
        for i in range(14)
    ] + [
        f"https://example.com/services/service-{i}"
        for i in range(15)
    ]

    selected = select_representative_sample(
        candidates
    )

    assert len(selected) == 30


def test_unclassified_pages_remain_eligible():
    candidates = [
        "https://example.com/"
    ] + [
        f"https://example.com/page-{i}/"
        for i in range(100)
    ]

    selected = select_representative_sample(
        candidates
    )

    assert len(selected) == 50

    assert "https://example.com/" in selected

    selected_unclassified = [
        url
        for url in selected
        if "/page-" in url
    ]

    assert len(selected_unclassified) == 49


def test_known_page_types_are_not_lost_when_unclassified_dominate():
    homepage = [
        "https://example.com/"
    ]

    editorial = [
        "https://example.com/blog/seo-guide",
        "https://example.com/blog/performance-guide",
    ]

    commercial = [
        "https://example.com/services/seo",
        "https://example.com/services/web",
    ]

    unclassified = [
        f"https://example.com/content-{i}/"
        for i in range(100)
    ]

    candidates = (
        homepage
        + unclassified
        + editorial
        + commercial
    )

    selected = select_representative_sample(
        candidates
    )

    assert len(selected) == 50

    assert "https://example.com/" in selected

    assert (
        "https://example.com/blog/seo-guide"
        in selected
    )

    assert (
        "https://example.com/blog/performance-guide"
        in selected
    )

    assert (
        "https://example.com/services/seo"
        in selected
    )

    assert (
        "https://example.com/services/web"
        in selected
    )


def test_sampling_is_deterministic():
    candidates = [
        "https://example.com/"
    ] + [
        f"https://example.com/content-{i}/"
        for i in range(100)
    ]

    first_sample = select_representative_sample(
        candidates
    )

    second_sample = select_representative_sample(
        candidates
    )

    assert first_sample == second_sample


if __name__ == "__main__":
    test_representative_sample_respects_cap_and_mix()
    test_representative_sample_uses_all_when_below_cap()
    test_unclassified_pages_remain_eligible()
    test_known_page_types_are_not_lost_when_unclassified_dominate()
    test_sampling_is_deterministic()

    print(
        "collector representative sampling: OK"
    )