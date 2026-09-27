import json

from collector import (
    normalize_url,
    get_normalized_host,
    get_persistence_key,
    get_site_data_directory,
    build_page_filename,
    persist_page,
    persist_manifest,
    create_http_session,
    fetch_page,
    get_robots_url,
    fetch_robots_parser,
    is_url_allowed,
    discover_internal_links,
    build_candidate_urls,
    parse_sitemap_xml,
    get_sitemap_candidates,
    discover_sitemap_urls,
    build_discovery_universe,
    classify_url,
    select_representative_sample,
    collect_site,
    is_html_candidate_url,
)

from models import PageData


def test_collector_helpers():
    assert normalize_url("www.example.com") == "https://www.example.com/"
    assert normalize_url("https://example.com") == "https://example.com/"

    assert get_normalized_host("https://www.example.com/test") == "example.com"
    assert get_normalized_host("https://example.com/test") == "example.com"

    assert get_persistence_key("https://www.example.com/test") == "example.com"

    site_directory = get_site_data_directory("https://www.example.com/test")
    assert site_directory.name == "example.com"
    assert site_directory.exists()

    assert build_page_filename("https://example.com/") == "index.json"
    seo_filename = build_page_filename(
        "https://example.com/services/seo"
    )

    assert seo_filename.startswith(
        "services__seo__"
    )
    assert seo_filename.endswith(".json")

    page = PageData(
        source_url="https://www.example.com/services/seo",
        final_url="https://www.example.com/services/seo",
        status_code=200,
        title="SEO Services",
    )

    saved_file = persist_page(page)

    assert saved_file.exists()
    assert saved_file.name.startswith(
        "services__seo__"
    )
    assert saved_file.name.endswith(".json")

    manifest_file = persist_manifest(
        url="https://www.example.com",
        audit_id="test-audit-001",
        page_files={
            "https://www.example.com/services/seo": {
                "source_url": "https://www.example.com/services/seo",
                "final_url": "https://www.example.com/services/seo",
                "filename": saved_file.name,
            }
        },
        crawl_started_at="2026-08-20T10:00:00+00:00",
        crawl_completed_at="2026-08-20T10:01:00+00:00",
        pages_discovered=10,
        pages_selected=5,
        pages_fetched=5,
        robots_txt_url="https://www.example.com/robots.txt",
        robots_txt_available=True,
        sitemap_files=[
            "https://www.example.com/sitemap.xml"
        ],
        sitemap_page_urls=[],
        persistence_complete=True,
    )

    assert manifest_file.exists()
    assert manifest_file.name == "_manifest.json"

    with manifest_file.open(
            "r",
            encoding="utf-8",
    ) as file:
        manifest_data = json.load(file)

    assert manifest_data["audit_id"] == "test-audit-001"
    assert manifest_data["pages_discovered"] == 10
    assert manifest_data["pages_selected"] == 5
    assert manifest_data["pages_fetched"] == 5
    assert manifest_data["robots_txt_available"] is True
    assert manifest_data["sitemap_files"] == [
        "https://www.example.com/sitemap.xml"
    ]
    assert manifest_data["sitemap_page_urls"] == []
    assert manifest_data["persistence_complete"] is True

    session = create_http_session()

    fetched_page = fetch_page(
        session,
        "https://example.com",
    )

    fetched_page_file = persist_page(fetched_page)

    assert fetched_page_file.exists()
    assert fetched_page_file.name == "index.json"
    assert fetched_page.status_code == 200
    assert fetched_page.final_url.startswith("https://example.com")
    assert fetched_page.title is not None

    discovered_links = discover_internal_links(fetched_page)

    assert isinstance(discovered_links, list)

    assert (
        get_robots_url("https://www.example.com/test")
        == "https://www.example.com/robots.txt"
    )

    robots_parser, robots_txt_available = fetch_robots_parser(
        session,
        "https://example.com"
    )
    assert isinstance(robots_txt_available, bool)

    assert isinstance(
        is_url_allowed(
            robots_parser,
            "https://example.com",
        ),
        bool,
    )

    candidate_urls = build_candidate_urls(
        fetched_page,
        robots_parser,
    )

    assert isinstance(candidate_urls, list)
    assert fetched_page.final_url in candidate_urls

    sitemap_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
        </url>
        <url>
            <loc>https://example.com/services/</loc>
        </url>
    </urlset>
    """

    sitemap_files, page_urls = parse_sitemap_xml(
        sitemap_xml
    )

    assert sitemap_files == []
    assert page_urls == [
        "https://example.com/",
        "https://example.com/services/",
    ]

    sitemap_with_image_xml = """
    <urlset
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
    >
        <url>
            <loc>https://example.com/product/</loc>
            <image:image>
                <image:loc>https://example.com/media/product.jpg</image:loc>
            </image:image>
        </url>
    </urlset>
    """

    sitemap_files, page_urls = parse_sitemap_xml(
        sitemap_with_image_xml
    )

    assert sitemap_files == []
    assert page_urls == [
        "https://example.com/product/",
    ]

    sitemap_index_xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://example.com/sitemap-pages.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://example.com/sitemap-posts.xml</loc>
        </sitemap>
    </sitemapindex>
    """

    sitemap_files, page_urls = parse_sitemap_xml(
        sitemap_index_xml
    )

    assert sitemap_files == [
        "https://example.com/sitemap-pages.xml",
        "https://example.com/sitemap-posts.xml",
    ]
    assert page_urls == []

    discovery_universe = build_discovery_universe(
        homepage=fetched_page,
        sitemap_urls=[
            "https://example.com/",
            "https://example.com/services/",
            "https://example.com/blog/",
        ],
        robots_parser=robots_parser,
    )

    assert isinstance(discovery_universe, list)
    assert "https://example.com/" in discovery_universe

    assert classify_url("https://example.com/") == "homepage"

    assert classify_url(
        "https://example.com/blog/seo-guide"
    ) == "editorial"

    assert classify_url(
        "https://example.com/services/seo"
    ) == "commercial"

    assert classify_url(
        "https://example.com/about-us"
    ) == "other"

    sample_candidates = [
        "https://example.com/",
        "https://example.com/services/seo",
        "https://example.com/services/web",
        "https://example.com/products/tool",
        "https://example.com/blog/seo-guide",
        "https://example.com/blog/performance-guide",
        "https://example.com/about-us",
    ]

    selected_sample = select_representative_sample(
        sample_candidates,
        hard_cap=5,
    )

    assert len(selected_sample) == 5
    assert "https://example.com/" in selected_sample
    assert "https://example.com/about-us" in selected_sample

    unclassified_candidates = [
        "https://example.com/",
        "https://example.com/about-us",
        "https://example.com/company",
        "https://example.com/contact",
    ]

    unclassified_sample = select_representative_sample(
        unclassified_candidates,
        hard_cap=4,
    )

    assert len(unclassified_sample) == 4
    assert "https://example.com/about-us" in unclassified_sample
    assert "https://example.com/company" in unclassified_sample
    assert "https://example.com/contact" in unclassified_sample

    site_data = collect_site(
        "https://example.com"
    )

    assert site_data.normalized_host == "example.com"
    assert site_data.pages_fetched >= 1
    assert len(site_data.pages) >= 1
    assert site_data.persistence_directory is not None
    assert isinstance(
        site_data.robots_txt_available,
        bool,
    )

    assert isinstance(
        site_data.sitemap_files,
        list,
    )
    assert isinstance(
        site_data.sitemap_page_urls,
        list,
    )

    assert build_page_filename(
        "https://example.com/"
    ) == "index.json"

    seo_filename = build_page_filename(
        "https://example.com/services/seo"
    )

    assert seo_filename.startswith(
        "services__seo__"
    )
    assert seo_filename.endswith(".json")

    filename_a = build_page_filename(
        "https://example.com/products/shoes?size=42"
    )

    filename_b = build_page_filename(
        "https://example.com/products/shoes?size=43"
    )

    assert filename_a != filename_b

    assert is_html_candidate_url(
        "https://example.com/services/seo"
    )

    assert is_html_candidate_url(
        "https://example.com/blog/article"
    )

    assert not is_html_candidate_url(
        "https://example.com/catalog.pdf"
    )

    assert not is_html_candidate_url(
        "https://example.com/images/product.jpg"
    )

    assert not is_html_candidate_url(
        "https://example.com/download/file.zip"
    )
    assert not is_html_candidate_url(
        "https://example.com/locations.kml"
    )

    assert not is_html_candidate_url(
        "https://example.com/sitemap.xml"
    )

    assert not is_html_candidate_url(
        "https://example.com/data.json"
    )

    assert not is_html_candidate_url(
        "https://example.com/feed.csv"
    )

    assert not is_html_candidate_url(
        "https://example.com/app.js"
    )

if __name__ == "__main__":
    test_collector_helpers()
    print("collector persistence: OK")
