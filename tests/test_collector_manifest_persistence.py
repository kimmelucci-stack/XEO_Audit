import json
from tempfile import TemporaryDirectory
from unittest.mock import patch

from collector import persist_manifest


def test_manifest_persists_mapping():
    page_files = {
        "https://example.com/page": {
            "source_url": "https://example.com/page",
            "final_url": "https://example.com/final-page",
            "filename": "page.json",
        }
    }

    with TemporaryDirectory() as temp_dir:
        with patch(
            "collector.get_site_data_directory",
            return_value=__import__("pathlib").Path(temp_dir),
        ):
            manifest_path = persist_manifest(
                url="https://example.com/",
                audit_id="test-audit",
                page_files=page_files,
                crawl_started_at="start",
                crawl_completed_at="end",
                pages_discovered=1,
                pages_selected=1,
                pages_fetched=1,
                robots_txt_url="https://example.com/robots.txt",
                robots_txt_available=True,
                sitemap_files=[],
                sitemap_page_urls=[],
                persistence_complete=True,
            )

        with manifest_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            manifest = json.load(file)

    assert manifest["pages"] == page_files


if __name__ == "__main__":
    test_manifest_persists_mapping()

    print("collector manifest persistence: OK")