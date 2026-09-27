import json
from pathlib import Path

from collector import (
    collect_site,
    is_html_candidate_url,
)


TEST_URL = "https://www.python.org/"


def test_real_site_collector():
    site_data = collect_site(
        TEST_URL
    )

    print()
    print("REAL SITE COLLECTOR RESULT")
    print("--------------------------")

    print(
        f"Submitted URL: "
        f"{site_data.submitted_url}"
    )

    print(
        f"Normalized host: "
        f"{site_data.normalized_host}"
    )

    print()
    print("DISCOVERY PREFLIGHT")
    print("-------------------")

    print(
        f"Robots.txt URL: "
        f"{site_data.robots_txt_url}"
    )

    print(
        f"Robots.txt available: "
        f"{site_data.robots_txt_available}"
    )

    print(
        f"Sitemap files inspected: "
        f"{len(site_data.sitemap_files)}"
    )

    if site_data.sitemap_files:
        print(
            "Sitemap file examples:"
        )

        for url in site_data.sitemap_files[:5]:
            print(
                f"  - {url}"
            )

    print(
        f"HTML page URLs discovered via sitemap: "
        f"{len(site_data.sitemap_page_urls)}"
    )

    if site_data.sitemap_page_urls:
        print(
            "Sitemap page URL examples:"
        )

        for url in site_data.sitemap_page_urls[:5]:
            print(
                f"  - {url}"
            )

    print()
    print("CRAWL COVERAGE")
    print("--------------")

    print(
        f"Pages discovered: "
        f"{site_data.pages_discovered}"
    )

    print(
        f"Pages selected: "
        f"{site_data.pages_selected}"
    )

    print(
        f"Pages fetched: "
        f"{site_data.pages_fetched}"
    )

    print(
        f"Persistence complete: "
        f"{site_data.persistence_complete}"
    )

    print(
        f"Persistence directory: "
        f"{site_data.persistence_directory}"
    )

    print(
        f"Fetch errors: "
        f"{len(site_data.fetch_errors)}"
    )

    # V1 hard cap
    assert site_data.pages_selected <= 50
    assert site_data.pages_fetched <= 50

    # Desired minimum when enough candidates exist
    if site_data.pages_discovered >= 25:
        assert site_data.pages_selected >= 25

    assert site_data.pages_fetched > 0

    # robots.txt evidence
    assert site_data.robots_txt_url

    assert isinstance(
        site_data.robots_txt_available,
        bool,
    )

    # Sitemap evidence
    assert isinstance(
        site_data.sitemap_files,
        list,
    )

    assert isinstance(
        site_data.sitemap_page_urls,
        list,
    )

    # Sitemap page URLs must be HTML candidates
    for url in site_data.sitemap_page_urls:
        assert is_html_candidate_url(
            url
        )

    persistence_dir = Path(
        site_data.persistence_directory
    )

    assert persistence_dir.exists()

    manifest_path = (
        persistence_dir
        / "_manifest.json"
    )

    assert manifest_path.exists()

    with manifest_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        manifest = json.load(
            file
        )

    page_json_files = [
        path
        for path in persistence_dir.glob(
            "*.json"
        )
        if path.name != "_manifest.json"
    ]

    print(
        f"Persisted page JSON files: "
        f"{len(page_json_files)}"
    )

    manifest_pages = manifest.get(
        "pages",
        {}
    )

    manifest_filenames = [
        page_data["filename"]
        for page_data in manifest_pages.values()
    ]

    unique_manifest_filenames = set(
        manifest_filenames
    )

    physical_filenames = {
        path.name
        for path in page_json_files
    }

    print(
        f"Manifest page mappings: "
        f"{len(manifest_pages)}"
    )

    print(
        f"Unique persisted pages: "
        f"{len(unique_manifest_filenames)}"
    )

    # Every fetched source URL must remain traceable
    # in the manifest.
    assert (
        len(manifest_pages)
        == site_data.pages_fetched
    )

    # Physical JSON files represent unique normalized
    # final pages. Multiple source URLs may legitimately
    # converge on the same final URL / filename.
    assert (
        physical_filenames
        == unique_manifest_filenames
    )

    # At least one persisted normalized page
    # must exist.
    assert len(
        unique_manifest_filenames
    ) >= 1

    # PRD desired minimum must also hold against
    # unique persisted pages when enough candidates exist.
    if site_data.pages_discovered >= 25:
        assert (
            len(unique_manifest_filenames)
            >= 25
        )

    assert manifest.get(
        "sitemap_files",
        []
    ) == site_data.sitemap_files

    assert manifest.get(
        "sitemap_page_urls",
        []
    ) == site_data.sitemap_page_urls

    duplicate_filenames = sorted({
        filename
        for filename in manifest_filenames
        if manifest_filenames.count(
            filename
        ) > 1
    })

    if duplicate_filenames:
        print()
        print("SOURCE URL ALIASES / REDIRECTS")
        print("------------------------------")

        for filename in duplicate_filenames:
            print(
                f"  Persisted file: "
                f"{filename}"
            )

            for (
                source_url,
                page_data,
            ) in manifest_pages.items():
                if (
                    page_data["filename"]
                    == filename
                ):
                    print(
                        f"      source: "
                        f"{source_url}"
                    )

                    print(
                        f"      final:  "
                        f"{page_data['final_url']}"
                    )

    if site_data.fetch_errors:
        print()
        print("FETCH ERRORS")
        print("------------")

        for error in site_data.fetch_errors:
            print(
                error
            )

    print()
    print(
        "collector real-site acceptance: OK"
    )


if __name__ == "__main__":
    test_real_site_collector()