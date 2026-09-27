from collector import select_representative_sample


def test_unclassified_pages_are_not_starved_by_classified_pages():
    homepage = [
        "https://example.com/"
    ]

    editorial = [
        f"https://example.com/blog/article-{i}/"
        for i in range(40)
    ]

    commercial = [
        f"https://example.com/services/service-{i}/"
        for i in range(40)
    ]

    unclassified = [
        f"https://example.com/content-{i}/"
        for i in range(40)
    ]

    candidates = (
        homepage
        + editorial
        + commercial
        + unclassified
    )

    selected = select_representative_sample(
        candidates
    )

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

    selected_unclassified = [
        url
        for url in selected
        if "/content-" in url
    ]

    print(
        f"Selected total: "
        f"{len(selected)}"
    )

    print(
        f"Editorial: "
        f"{len(selected_editorial)}"
    )

    print(
        f"Commercial: "
        f"{len(selected_commercial)}"
    )

    print(
        f"Unclassified: "
        f"{len(selected_unclassified)}"
    )

    assert len(selected) == 50

    assert selected_editorial

    assert selected_commercial

    assert selected_unclassified


if __name__ == "__main__":
    test_unclassified_pages_are_not_starved_by_classified_pages()

    print(
        "collector sampling diversity: OK"
    )