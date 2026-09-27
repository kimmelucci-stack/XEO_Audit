import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from collector import (
    persist_manifest,
    remove_stale_page_files,
)


def test_stale_page_files_are_removed():
    with TemporaryDirectory() as temp_dir:
        site_directory = Path(temp_dir)

        current_file = (
            site_directory
            / "current-page.json"
        )

        stale_file = (
            site_directory
            / "old-page.json"
        )

        current_file.write_text(
            "{}",
            encoding="utf-8",
        )

        stale_file.write_text(
            "{}",
            encoding="utf-8",
        )

        page_files = {
            "https://example.com/current-page": {
                "source_url":
                    "https://example.com/current-page",
                "final_url":
                    "https://example.com/current-page",
                "filename":
                    "current-page.json",
            }
        }

        with patch(
            "collector.get_site_data_directory",
            return_value=site_directory,
        ):
            manifest_path = persist_manifest(
                url="https://example.com/",
                audit_id="test-audit",
                page_files=page_files,
                crawl_started_at="start",
                crawl_completed_at="end",
                pages_discovered=2,
                pages_selected=1,
                pages_fetched=1,
                robots_txt_url=(
                    "https://example.com/robots.txt"
                ),
                robots_txt_available=True,
                sitemap_files=[],
                sitemap_page_urls=[],
                persistence_complete=True,
            )

            removed_files = remove_stale_page_files(
                "https://example.com/",
                page_files,
            )

        with manifest_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            manifest = json.load(
                file
            )

        current_manifest_files = {
            page_data["filename"]
            for page_data
            in manifest["pages"].values()
        }

        assert current_manifest_files == {
            "current-page.json"
        }

        assert current_file.exists()
        assert not stale_file.exists()

        assert removed_files == [
            "old-page.json"
        ]


if __name__ == "__main__":
    test_stale_page_files_are_removed()

    print(
        "collector stale persistence cleanup: OK"
    )