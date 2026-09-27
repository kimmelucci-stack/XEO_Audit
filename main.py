from __future__ import annotations

import argparse
from collections.abc import Sequence

from audit_runner import run_audit, serialize_json_report
from collector import get_site_data_directory, normalize_url


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a XEO Audit for a public website."
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Public website URL to audit.",
    )

    parser.add_argument(
        "--device",
        choices=["mobile", "desktop"],
        default="mobile",
        help="Audit device context. Default: mobile.",
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Report output format. Default: markdown.",
    )

    parser.add_argument(
        "--output",
        help=(
            "Optional report output path. Defaults to the site's "
            "data directory."
        ),
    )

    parser.add_argument(
        "--recommendation-limit",
        type=int,
        default=None,
        help=(
            "Optional maximum number of action-plan recommendations "
            "to include."
        ),
    )

    return parser.parse_args(
        argv
    )


def main() -> None:
    args = parse_args()
    normalized_url = normalize_url(
        args.url
    )

    print("\nXEO Audit")
    print(f"URL: {normalized_url}")
    print(f"Device: {args.device}")
    print("Status: running audit")

    audit_run = run_audit(
        url=normalized_url,
        device=args.device,
        recommendation_limit=args.recommendation_limit,
    )

    if args.format == "json":
        report_content = serialize_json_report(
            audit_run
        )
        default_filename = "xeo_audit_report.json"

    else:
        report_content = audit_run.markdown_report
        default_filename = "xeo_audit_report.md"

    if args.output:
        output_path = args.output

    else:
        output_path = str(
            get_site_data_directory(
                normalized_url
            )
            / default_filename
        )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            report_content
        )

    print(
        "Search/Technical Readiness: "
        f"{audit_run.evaluation.score}/100 "
        f"({audit_run.evaluation.grade})"
    )
    print("XEO Score: non disponibile (moduli PRD mancanti)")
    print(f"Findings: {len(audit_run.evaluation.findings)}")
    print(f"Report: {output_path}\n")


if __name__ == "__main__":
    main()
