import hashlib
import json
import time
import uuid
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import (
    CRAWL_DELAY_SECONDS,
    CRAWL_HARD_CAP,
    CRAWL_MIN_DESIRED,
    DATA_ROOT,
    HTTP_TIMEOUT_SECONDS,
    USER_AGENT,
    HTTP_MAX_RETRIES,
)
from models import PageData, SiteData


def normalize_url(url: str) -> str:
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path or "/",
            "",
            parsed.query,
            "",
        )
    )


def get_normalized_host(url: str) -> str:
    normalized_url = normalize_url(url)
    parsed = urlparse(normalized_url)

    host = parsed.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    return host


def get_persistence_key(url: str) -> str:
    return get_normalized_host(url)


def get_site_data_directory(url: str) -> Path:
    persistence_key = get_persistence_key(url)
    site_directory = DATA_ROOT / persistence_key
    site_directory.mkdir(parents=True, exist_ok=True)

    return site_directory


def build_page_filename(url: str) -> str:
    normalized_url = normalize_url(url)
    parsed = urlparse(normalized_url)

    path = parsed.path.strip("/")

    if not path and not parsed.query:
        return "index.json"

    if path:
        readable_name = path.replace("/", "__")
    else:
        readable_name = "index"

    fingerprint_source = (
        f"{parsed.scheme}://{parsed.netloc.lower()}"
        f"{parsed.path}"
    )

    if parsed.query:
        fingerprint_source += f"?{parsed.query}"

    url_hash = hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()[:10]

    return f"{readable_name}__{url_hash}.json"


def persist_page(page: PageData) -> Path:
    site_directory = get_site_data_directory(page.final_url)
    filename = build_page_filename(page.final_url)

    output_file = site_directory / filename

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            asdict(page),
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_file

def persist_manifest(
    url: str,
    audit_id: str,
    page_files: dict[str, dict[str, str]],
    crawl_started_at: str,
    crawl_completed_at: str,
    pages_discovered: int,
    pages_selected: int,
    pages_fetched: int,
    robots_txt_url: str | None,
    robots_txt_available: bool,
    sitemap_files: list[str],
    sitemap_page_urls: list[str],
    persistence_complete: bool,
) -> Path:
    site_directory = get_site_data_directory(
        url
    )

    manifest_file = (
        site_directory
        / "_manifest.json"
    )

    manifest = {
        "audit_id": audit_id,
        "submitted_url": normalize_url(
            url
        ),
        "normalized_host": get_normalized_host(
            url
        ),
        "crawl_started_at": crawl_started_at,
        "crawl_completed_at": crawl_completed_at,
        "pages_discovered": pages_discovered,
        "pages_selected": pages_selected,
        "pages_fetched": pages_fetched,
        "robots_txt_url": robots_txt_url,
        "robots_txt_available": robots_txt_available,
        "sitemap_files": sitemap_files,
        "sitemap_page_urls": sitemap_page_urls,
        "persistence_complete": persistence_complete,
        "pages": page_files,
    }

    with manifest_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return manifest_file


def create_http_session() -> requests.Session:
    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
    })

    return session

class TargetBlockedError(
    requests.RequestException
):
    """Target site is actively rate-limiting or blocking the crawl."""


def get_with_retry(
    session: requests.Session,
    url: str,
) -> requests.Response:
    last_error = None

    for attempt in range(HTTP_MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                timeout=HTTP_TIMEOUT_SECONDS,
            )

        except requests.RequestException as exc:
            last_error = exc

            if attempt >= HTTP_MAX_RETRIES:
                raise

            time.sleep(2 ** attempt)
            continue

        if response.status_code == 429:
            if attempt >= HTTP_MAX_RETRIES:
                raise TargetBlockedError(
                    "TARGET_BLOCKED: repeated HTTP 429 "
                    f"for {url}"
                )

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait_seconds = float(retry_after)
            except (TypeError, ValueError):
                wait_seconds = 2 ** attempt

            time.sleep(wait_seconds)
            continue

        if response.status_code >= 500:
            if attempt >= HTTP_MAX_RETRIES:
                return response

            time.sleep(2 ** attempt)
            continue

        return response

    if last_error:
        raise last_error

    raise RuntimeError(
        f"Unable to fetch URL: {url}"
    )


def extract_sanitized_visible_text(html: str) -> str:
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "form",
            "template",
        ]
    ):
        element.decompose()

    visible_text = " ".join(
        soup.stripped_strings
    )

    visible_text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL_REDACTED]",
        visible_text,
    )

    visible_text = re.sub(
        r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
        "[PHONE_REDACTED]",
        visible_text,
    )

    return visible_text


def fetch_page(
    session: requests.Session,
    url: str,
) -> PageData:
    normalized_url = normalize_url(url)

    response = get_with_retry(
        session,
        normalized_url,
    )

    # Prevent redirects outside the audited host
    if (
        get_normalized_host(response.url)
        != get_normalized_host(normalized_url)
    ):
        raise ValueError(
            "Redirect outside normalized host: "
            f"{normalized_url} -> {response.url}"
        )

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if (
        "text/html" not in content_type
        and "application/xhtml+xml" not in content_type
    ):
        raise ValueError(
            f"Non-HTML content returned for {normalized_url}: "
            f"{content_type or 'unknown'}"
        )

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Title
    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else None
    )

    # Meta description
    meta_description_tag = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    meta_description = (
        meta_description_tag.get("content", "").strip()
        if meta_description_tag
        else None
    )

    # Headings
    h1 = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all("h1")
    ]

    h2 = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all("h2")
    ]

    h3 = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all("h3")
    ]

    # Canonical
    canonical_tag = soup.find(
        "link",
        attrs={"rel": "canonical"},
    )

    canonical = (
        urljoin(
            response.url,
            canonical_tag.get("href"),
        )
        if canonical_tag
        and canonical_tag.get("href")
        else None
    )

    # Meta robots
    robots_tag = soup.find(
        "meta",
        attrs={
            "name": lambda value:
            value and value.lower() == "robots"
        },
    )

    robots_content = (
        robots_tag.get("content", "").lower()
        if robots_tag
        else ""
    )

    robots_noindex = "noindex" in robots_content
    robots_nofollow = "nofollow" in robots_content

    # X-Robots-Tag HTTP header
    x_robots_tag = response.headers.get(
        "X-Robots-Tag"
    )

    # Internal links + anchor text
    current_host = get_normalized_host(
        response.url
    )

    internal_links = []
    internal_link_anchors = []

    for link in soup.find_all(
        "a",
        href=True,
    ):
        absolute_url = urljoin(
            response.url,
            link["href"],
        )

        parsed_link = urlparse(
            absolute_url
        )

        if parsed_link.scheme not in (
            "http",
            "https",
        ):
            continue

        if (
            get_normalized_host(absolute_url)
            != current_host
        ):
            continue

        normalized_internal_url = normalize_url(
            absolute_url
        )

        internal_links.append(
            normalized_internal_url
        )

        internal_link_anchors.append({
            "url": normalized_internal_url,
            "anchor_text": link.get_text(
                " ",
                strip=True,
            ),
        })

    internal_links = sorted(
        set(internal_links)
    )

    # Structured data
    structured_data_types = []

    for script in soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    ):
        if not script.string:
            continue

        try:
            json_data = json.loads(
                script.string
            )

            items = (
                json_data
                if isinstance(json_data, list)
                else [json_data]
            )

            for item in items:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                schema_type = item.get(
                    "@type"
                )

                if isinstance(
                    schema_type,
                    str,
                ):
                    structured_data_types.append(
                        schema_type
                    )

                elif isinstance(
                    schema_type,
                    list,
                ):
                    structured_data_types.extend(
                        schema_type
                    )

        except json.JSONDecodeError:
            continue

    structured_data_types = sorted(
        set(structured_data_types)
    )

    # Images
    images = soup.find_all("img")

    image_count = len(images)

    images_missing_alt = sum(
        1
        for image in images
        if not image.get("alt")
    )

    image_evidence = []

    for image in images:
        image_evidence.append({
            "src": image.get("src"),
            "alt": image.get("alt"),
            "width": image.get("width"),
            "height": image.get("height"),
            "loading": image.get("loading"),
        })

    # Sanitized visible text
    visible_text = extract_sanitized_visible_text(
        response.text
    )

    # Redirect history
    redirect_history = [
        item.url
        for item in response.history
    ]

    return PageData(
        source_url=normalized_url,
        final_url=response.url,
        status_code=response.status_code,
        redirect_history=redirect_history,
        crawl_timestamp=datetime.now(
            timezone.utc
        ).isoformat(),
        title=title,
        meta_description=meta_description,
        h1=h1,
        h2=h2,
        h3=h3,
        canonical=canonical,
        robots_noindex=robots_noindex,
        robots_nofollow=robots_nofollow,
        x_robots_tag=x_robots_tag,
        structured_data_types=structured_data_types,
        internal_links=internal_links,
        internal_link_anchors=internal_link_anchors,
        image_count=image_count,
        images_missing_alt=images_missing_alt,
        image_evidence=image_evidence,
        visible_text=visible_text,
    )


def get_robots_url(url: str) -> str:
    normalized_url = normalize_url(url)
    parsed = urlparse(normalized_url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}/robots.txt"
    )


def fetch_robots_parser(
    session: requests.Session,
    url: str,
) -> tuple[
    robotparser.RobotFileParser,
    bool,
]:
    robots_url = get_robots_url(url)

    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)

    try:
        response = get_with_retry(
            session,
            robots_url,
        )

    except requests.RequestException:
        parser.parse([])
        return parser, False

    if response.status_code == 200:
        parser.parse(
            response.text.splitlines()
        )
        return parser, True

    parser.parse([])
    return parser, False


def is_url_allowed(
    parser: robotparser.RobotFileParser,
    url: str,
) -> bool:
    return parser.can_fetch(
        USER_AGENT,
        normalize_url(url),
    )


def discover_internal_links(
    page: PageData,
) -> list[str]:
    normalized_links = []

    for url in page.internal_links:
        normalized_url = normalize_url(
            url
        )

        if (
            normalized_url
            not in normalized_links
        ):
            normalized_links.append(
                normalized_url
            )

    return normalized_links


def build_candidate_urls(
    homepage: PageData,
    robots_parser: robotparser.RobotFileParser,
) -> list[str]:
    candidates = [
        homepage.final_url
    ]

    for url in discover_internal_links(
        homepage
    ):
        if is_url_allowed(
            robots_parser,
            url,
        ):
            candidates.append(url)

    return sorted(
        set(candidates)
    )


def parse_sitemap_xml(
    xml_text: str,
) -> tuple[list[str], list[str]]:
    """
    Parse one sitemap XML document.

    Returns:
        sitemap_files:
            child sitemap XML URLs discovered from a sitemap index.

        page_urls:
            page URLs discovered from a URL sitemap.

    Image/video/news namespace <loc> elements are intentionally ignored.
    """
    try:
        root = ET.fromstring(
            xml_text
        )
    except ET.ParseError as exc:
        raise ValueError(
            f"Invalid sitemap XML: {exc}"
        ) from exc

    sitemap_files = []
    page_urls = []

    root_name = (
        root.tag
        .split("}")[-1]
        .lower()
    )

    if root_name == "sitemapindex":
        for sitemap_element in root:
            element_name = (
                sitemap_element.tag
                .split("}")[-1]
                .lower()
            )

            if element_name != "sitemap":
                continue

            for child in sitemap_element:
                child_name = (
                    child.tag
                    .split("}")[-1]
                    .lower()
                )

                if (
                    child_name == "loc"
                    and child.text
                ):
                    sitemap_files.append(
                        normalize_url(
                            child.text.strip()
                        )
                    )

                    break

    elif root_name == "urlset":
        for url_element in root:
            element_name = (
                url_element.tag
                .split("}")[-1]
                .lower()
            )

            if element_name != "url":
                continue

            for child in url_element:
                child_name = (
                    child.tag
                    .split("}")[-1]
                    .lower()
                )

                if (
                    child_name == "loc"
                    and child.text
                ):
                    page_urls.append(
                        normalize_url(
                            child.text.strip()
                        )
                    )

                    break

    else:
        raise ValueError(
            f"Unsupported sitemap root element: "
            f"{root_name}"
        )

    return (
        sorted(set(sitemap_files)),
        sorted(set(page_urls)),
    )

def get_sitemap_candidates(
    url: str,
    robots_parser: robotparser.RobotFileParser,
) -> list[str]:
    candidates = []

    robots_sitemaps = (
        robots_parser.site_maps()
    )

    if robots_sitemaps:
        candidates.extend(
            robots_sitemaps
        )

    default_sitemap = urljoin(
        normalize_url(url),
        "/sitemap.xml",
    )

    candidates.append(
        default_sitemap
    )

    return list(
        dict.fromkeys(candidates)
    )


def discover_sitemap_urls(
    session: requests.Session,
    url: str,
    robots_parser: robotparser.RobotFileParser,
    max_sitemaps: int = 20,
) -> tuple[list[str], list[str]]:
    """
    Discover sitemap files and page URLs for the audited host.

    Returns:
        sitemap_files:
            Successfully fetched and parsed sitemap XML files.

        sitemap_page_urls:
            Same-host page URLs discovered from those sitemap files.
    """
    audited_host = get_normalized_host(
        url
    )

    sitemap_queue = [
        normalize_url(sitemap_url)
        for sitemap_url in get_sitemap_candidates(
            url,
            robots_parser,
        )
    ]

    visited_sitemaps = set()
    sitemap_files = []
    discovered_pages = []

    while (
        sitemap_queue
        and len(visited_sitemaps) < max_sitemaps
    ):
        sitemap_url = sitemap_queue.pop(
            0
        )

        sitemap_url = normalize_url(
            sitemap_url
        )

        if sitemap_url in visited_sitemaps:
            continue

        visited_sitemaps.add(
            sitemap_url
        )

        # Do not make sitemap requests outside
        # the audited host.
        if (
            get_normalized_host(sitemap_url)
            != audited_host
        ):
            continue

        try:
            response = get_with_retry(
                session,
                sitemap_url,
            )

        except requests.RequestException:
            continue

        if response.status_code != 200:
            continue

        try:
            (
                child_sitemaps,
                page_urls,
            ) = parse_sitemap_xml(
                response.text
            )

        except ValueError:
            continue

        sitemap_files.append(
            sitemap_url
        )

        for page_url in page_urls:
            normalized_page_url = normalize_url(
                page_url
            )

            if (
                get_normalized_host(
                    normalized_page_url
                )
                != audited_host
            ):
                continue

            if not is_html_candidate_url(
                normalized_page_url
            ):
                continue

            discovered_pages.append(
                normalized_page_url
            )

        for child_sitemap in child_sitemaps:
            normalized_child_sitemap = normalize_url(
                child_sitemap
            )

            if (
                get_normalized_host(
                    normalized_child_sitemap
                )
                != audited_host
            ):
                continue

            if (
                normalized_child_sitemap
                in visited_sitemaps
            ):
                continue

            if (
                normalized_child_sitemap
                in sitemap_queue
            ):
                continue

            sitemap_queue.append(
                normalized_child_sitemap
            )

    return (
        list(
            dict.fromkeys(
                sitemap_files
            )
        ),
        list(
            dict.fromkeys(
                discovered_pages
            )
        ),
    )


EXCLUDED_PATH_TOKENS = (
    "/login",
    "/signin",
    "/account",
    "/my-account",
    "/cart",
    "/basket",
    "/checkout",
    "/payment",
    "/admin",
    "/wp-admin",
    "/search",
    "/api/",
)

NON_HTML_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".zip",
    ".rar",
    ".7z",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".xml",
    ".kml",
    ".json",
    ".txt",
    ".csv",
    ".css",
    ".js",
    ".map",
    ".ics",
    ".vcf",
)

def is_html_candidate_url(url: str) -> bool:
    parsed = urlparse(
        normalize_url(url)
    )

    path = parsed.path.lower()

    return not path.endswith(
        NON_HTML_EXTENSIONS
    )

def is_sensitive_or_operational_url(
    url: str,
) -> bool:
    parsed = urlparse(
        normalize_url(url)
    )

    path = parsed.path.lower()
    query = parsed.query.lower()

    if any(
        token in path
        for token in EXCLUDED_PATH_TOKENS
    ):
        return True

    sensitive_query_tokens = (
        "session=",
        "token=",
        "auth=",
    )

    if any(
        token in query
        for token in sensitive_query_tokens
    ):
        return True

    return False


def build_discovery_universe(
    homepage: PageData,
    sitemap_urls: list[str],
    robots_parser: robotparser.RobotFileParser,
) -> list[str]:
    candidates = [
        homepage.final_url
    ]

    candidates.extend(
        sitemap_urls
    )

    candidates.extend(
        discover_internal_links(
            homepage
        )
    )

    filtered_candidates = []

    for url in candidates:
        normalized_url = normalize_url(
            url
        )

        if (
            get_normalized_host(
                normalized_url
            )
            != get_normalized_host(
                homepage.final_url
            )
        ):
            continue

        if not is_url_allowed(
            robots_parser,
            normalized_url,
        ):
            continue

        if is_sensitive_or_operational_url(
            normalized_url
        ):
            continue

        if not is_html_candidate_url(
            normalized_url
        ):
            continue

        filtered_candidates.append(
            normalized_url
        )

    return list(
        dict.fromkeys(
            filtered_candidates
        )
    )


def classify_url(url: str) -> str:
    parsed = urlparse(
        normalize_url(url)
    )

    path = (
        parsed.path
        .lower()
        .strip("/")
    )

    if not path:
        return "homepage"

    editorial_tokens = (
        "blog",
        "news",
        "guide",
        "guides",
        "faq",
        "article",
        "articles",
        "insights",
        "resources",
    )

    commercial_tokens = (
        "product",
        "products",
        "category",
        "categories",
        "service",
        "services",
        "solutions",
        "landing",
        "shop",
    )

    path_segments = path.split("/")

    if any(
        token in path_segments
        for token in editorial_tokens
    ):
        return "editorial"

    if any(
        token in path_segments
        for token in commercial_tokens
    ):
        return "commercial"

    return "other"


def select_representative_sample(
    candidate_urls: list[str],
    hard_cap: int = CRAWL_HARD_CAP,
) -> list[str]:
    homepage_urls = []
    editorial_urls = []
    commercial_urls = []
    unclassified_urls = []

    seen_urls = set()

    for url in candidate_urls:
        if url in seen_urls:
            continue

        seen_urls.add(url)

        page_class = classify_url(
            url
        )

        if page_class == "homepage":
            homepage_urls.append(
                url
            )

        elif page_class == "editorial":
            editorial_urls.append(
                url
            )

        elif page_class == "commercial":
            commercial_urls.append(
                url
            )

        else:
            unclassified_urls.append(
                url
            )

    all_unique_urls = (
        homepage_urls
        + editorial_urls
        + commercial_urls
        + unclassified_urls
    )

    if len(all_unique_urls) <= hard_cap:
        return all_unique_urls

    selected_urls = []

    if homepage_urls:
        selected_urls.append(
            homepage_urls[0]
        )

    remaining_slots = (
        hard_cap
        - len(selected_urls)
    )

    if remaining_slots <= 0:
        return selected_urls

    groups = {
        "editorial": editorial_urls,
        "commercial": commercial_urls,
        "unclassified": unclassified_urls,
    }

    allocations = {
        group_name: 0
        for group_name in groups
    }

    remaining_groups = {
        group_name: urls
        for group_name, urls in groups.items()
        if urls
    }

    slots_left = remaining_slots

    # Preserve small groups completely when their
    # size fits comfortably within their fair share.
    while (
        remaining_groups
        and slots_left > 0
    ):
        fair_share = (
            slots_left
            / len(remaining_groups)
        )

        small_groups = [
            group_name
            for group_name, urls
            in remaining_groups.items()
            if len(urls) <= fair_share
        ]

        if not small_groups:
            break

        for group_name in small_groups:
            group_size = len(
                remaining_groups[
                    group_name
                ]
            )

            allocations[
                group_name
            ] = group_size

            slots_left -= group_size

            del remaining_groups[
                group_name
            ]

    # Distribute remaining capacity proportionally
    # across groups that are still larger than their
    # available share.
    if (
        remaining_groups
        and slots_left > 0
    ):
        total_capacity = sum(
            len(urls)
            for urls
            in remaining_groups.values()
        )

        fractional_remainders = []

        for (
            group_name,
            urls,
        ) in remaining_groups.items():
            exact_share = (
                slots_left
                * len(urls)
                / total_capacity
            )

            base_allocation = min(
                len(urls),
                int(exact_share),
            )

            allocations[
                group_name
            ] += base_allocation

            fractional_remainders.append(
                (
                    exact_share
                    - base_allocation,
                    group_name,
                )
            )

        allocated_now = sum(
            allocations[
                group_name
            ]
            for group_name
            in remaining_groups
        )

        still_available = (
            slots_left
            - allocated_now
        )

        fractional_remainders.sort(
            reverse=True
        )

        while still_available > 0:
            added = False

            for (
                _,
                group_name,
            ) in fractional_remainders:
                if (
                    allocations[group_name]
                    >= len(groups[group_name])
                ):
                    continue

                allocations[
                    group_name
                ] += 1

                still_available -= 1
                added = True

                if still_available <= 0:
                    break

            if not added:
                break

    # Deterministic distributed sampling inside
    # every group.
    for (
        group_name,
        urls,
    ) in groups.items():
        allocation = allocations[
            group_name
        ]

        if allocation <= 0:
            continue

        if len(urls) <= allocation:
            selected_urls.extend(
                urls
            )
            continue

        step = (
            len(urls)
            / allocation
        )

        sampled_urls = []

        for index in range(
            allocation
        ):
            selected_index = int(
                index * step
            )

            sampled_urls.append(
                urls[
                    selected_index
                ]
            )

        selected_urls.extend(
            sampled_urls
        )

    return selected_urls[
        :hard_cap
    ]


def collect_site(
    url: str,
    hard_cap: int = CRAWL_HARD_CAP,
    min_desired: int = CRAWL_MIN_DESIRED,
) -> SiteData:
    crawl_started_at = datetime.now(
        timezone.utc
    ).isoformat()

    audit_id = str(
        uuid.uuid4()
    )

    session = create_http_session()

    normalized_url = normalize_url(
        url
    )

    normalized_host = get_normalized_host(
        normalized_url
    )

    robots_url = get_robots_url(
        normalized_url
    )

    (
        robots_parser,
        robots_txt_available,
    ) = fetch_robots_parser(
        session,
        normalized_url,
    )

    if not is_url_allowed(
        robots_parser,
        normalized_url,
    ):
        raise PermissionError(
            "Homepage blocked by robots.txt "
            f"for {USER_AGENT}: {normalized_url}"
        )

    homepage = fetch_page(
        session,
        normalized_url,
    )

    homepage.page_type = "homepage"

    (
        sitemap_files,
        sitemap_page_urls,
    ) = discover_sitemap_urls(
        session,
        normalized_url,
        robots_parser,
    )

    discovery_universe = build_discovery_universe(
        homepage=homepage,
        sitemap_urls=sitemap_page_urls,
        robots_parser=robots_parser,
    )

    selected_urls = select_representative_sample(
        discovery_universe,
        hard_cap=hard_cap,
    )

    selected_url_set = set(
        selected_urls
    )

    reserve_urls = [
        candidate_url
        for candidate_url in discovery_universe
        if candidate_url not in selected_url_set
    ]

    crawl_queue = list(
        selected_urls
    )

    crawl_index = 0
    reserve_index = 0
    backfill_attempts = 0

    pages = []
    internal_link_graph = {}
    page_files = {}
    fetch_errors = []

    seen_final_urls = set()
    final_url_files = {}

    successful_fetches = 0

    persistence_complete = True

    consecutive_blocking_signals = 0

    while True:
        if crawl_index >= len(crawl_queue):
            if len(pages) >= min_desired:
                break

            if reserve_index >= len(reserve_urls):
                break

            if backfill_attempts >= min_desired:
                break

            reserve_url = reserve_urls[
                reserve_index
            ]

            reserve_index += 1
            backfill_attempts += 1

            crawl_queue.append(
                reserve_url
            )

        selected_url = crawl_queue[
            crawl_index
        ]

        crawl_index += 1
        try:
            if selected_url == homepage.final_url:
                page = homepage

            else:
                time.sleep(
                    CRAWL_DELAY_SECONDS
                )

                page = fetch_page(
                    session,
                    selected_url,
                )

                page.page_type = classify_url(
                    page.final_url
                )

            if not is_url_allowed(
                robots_parser,
                page.final_url,
            ):
                fetch_errors.append({
                    "url": selected_url,
                    "error": (
                        "Final URL blocked by robots.txt: "
                        f"{page.final_url}"
                    ),
                })
                continue

            if is_sensitive_or_operational_url(
                page.final_url
            ):
                fetch_errors.append({
                    "url": selected_url,
                    "error": (
                        "Final URL excluded by safety policy: "
                        f"{page.final_url}"
                    ),
                })
                continue

            is_blocking_status = (
                page.status_code == 403
                or page.status_code >= 500
            )

            if is_blocking_status:
                consecutive_blocking_signals += 1

                fetch_errors.append({
                    "url": selected_url,
                    "error": (
                        "Blocking signal: "
                        f"HTTP {page.status_code}"
                    ),
                })

                if consecutive_blocking_signals >= 2:
                    fetch_errors.append({
                        "url": selected_url,
                        "error": (
                            "TARGET_BLOCKED: repeated "
                            "403/5xx responses"
                        ),
                    })
                    break

                continue

            consecutive_blocking_signals = 0

            if 400 <= page.status_code < 500:
                fetch_errors.append({
                    "url": selected_url,
                    "error": (
                        f"HTTP {page.status_code}: "
                        "page excluded from eligible crawl sample"
                    ),
                })
                continue

            successful_fetches += 1

            normalized_final_url = normalize_url(
                page.final_url
            )

            is_duplicate_final = (
                normalized_final_url
                in seen_final_urls
            )

            existing_filename = final_url_files.get(
                normalized_final_url
            )

            if existing_filename is None:
                try:
                    saved_file = persist_page(
                        page
                    )

                except OSError as exc:
                    persistence_complete = False

                    fetch_errors.append({
                        "url": selected_url,
                        "error": (
                            "STORAGE_ERROR: "
                            f"{exc}"
                        ),
                    })

                    saved_filename = None

                else:
                    saved_filename = saved_file.name

                    final_url_files[
                        normalized_final_url
                    ] = saved_filename

            else:
                saved_filename = existing_filename

            if saved_filename is not None:
                page_files[
                    page.source_url
                ] = {
                    "source_url": page.source_url,
                    "final_url": page.final_url,
                    "filename": saved_filename,
                }

            if is_duplicate_final:
                continue

            seen_final_urls.add(
                normalized_final_url
            )

            pages.append(
                page
            )

            internal_link_graph[
                normalized_final_url
            ] = discover_internal_links(
                page
            )

            if len(selected_urls) < hard_cap:
                for discovered_url in discover_internal_links(
                    page
                ):
                    if len(selected_urls) >= hard_cap:
                        break

                    if discovered_url in selected_urls:
                        continue

                    if (
                        get_normalized_host(
                            discovered_url
                        )
                        != normalized_host
                    ):
                        continue

                    if not is_url_allowed(
                        robots_parser,
                        discovered_url,
                    ):
                        continue

                    if is_sensitive_or_operational_url(
                        discovered_url
                    ):
                        continue

                    if not is_html_candidate_url(
                        discovered_url
                    ):
                        continue

                    selected_urls.append(
                        discovered_url
                    )

                    crawl_queue.append(
                        discovered_url
                    )
        except TargetBlockedError as exc:
            fetch_errors.append({
                "url": selected_url,
                "error": str(exc),
            })

            break

        except OSError as exc:
            persistence_complete = False

            fetch_errors.append({
                "url": selected_url,
                "error": (
                    "STORAGE_ERROR: "
                    f"{exc}"
                ),
            })

            continue

        except (
            requests.RequestException,
            ValueError,
        ) as exc:
            fetch_errors.append({
                "url": selected_url,
                "error": str(exc),
            })

            continue

    crawl_completed_at = datetime.now(
        timezone.utc
    ).isoformat()

    try:
        persist_manifest(
            url=normalized_url,
            audit_id=audit_id,
            page_files=page_files,
            crawl_started_at=crawl_started_at,
            crawl_completed_at=crawl_completed_at,
            pages_discovered=len(
                discovery_universe
            ),
            pages_selected=len(
                selected_urls
            ),
            pages_fetched=successful_fetches,
            robots_txt_url=robots_url,
            robots_txt_available=robots_txt_available,
            sitemap_files=sitemap_files,
            sitemap_page_urls=sitemap_page_urls,
            persistence_complete=persistence_complete,
        )

    except OSError as exc:
        persistence_complete = False

        fetch_errors.append({
            "url": normalized_url,
            "error": (
                "STORAGE_ERROR: manifest write failed: "
                f"{exc}"
            ),
        })

    if persistence_complete:
        remove_stale_page_files(
            normalized_url,
            page_files,
        )

    return SiteData(
        submitted_url=normalized_url,
        normalized_host=normalized_host,
        pages=pages,
        robots_txt_url=robots_url,
        robots_txt_available=robots_txt_available,
        sitemap_files=sitemap_files,
        sitemap_page_urls=sitemap_page_urls,
        internal_link_graph=internal_link_graph,
        crawl_started_at=crawl_started_at,
        crawl_completed_at=crawl_completed_at,
        pages_discovered=len(
            discovery_universe
        ),
        pages_selected=len(
            selected_urls
        ),
        pages_fetched=successful_fetches,
        persistence_directory=str(
            get_site_data_directory(
                normalized_url
            )
        ),
        persistence_complete=persistence_complete,
        fetch_errors=fetch_errors,
    )

def remove_stale_page_files(
        url: str,
        current_page_files: dict[str, dict[str, str]],
) -> list[str]:
    site_directory = get_site_data_directory(
        url
    )

    current_filenames = {
        page_data["filename"]
        for page_data in current_page_files.values()
    }

    removed_files = []

    for path in site_directory.glob(
            "*.json"
    ):
        if path.name == "_manifest.json":
            continue

        if path.name in current_filenames:
            continue

        try:
            path.unlink()
        except OSError:
            continue

        removed_files.append(
            path.name
        )

    return removed_files
