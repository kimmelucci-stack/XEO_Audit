from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from audit_runner import run_audit


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            payload = json.loads(
                self.rfile.read(
                    content_length
                )
            )

            url = str(
                payload.get(
                    "url",
                    "",
                )
            ).strip()

            device = str(
                payload.get(
                    "device",
                    "mobile",
                )
            ).strip()

            if not url:
                raise ValueError(
                    "Website URL is required."
                )

            if device not in (
                "mobile",
                "desktop",
            ):
                raise ValueError(
                    f"Unsupported device: {device}"
                )

            audit_run = run_audit(
                url=url,
                device=device,
                demo_mode=True,
            )

            self.send_json(
                HTTPStatus.OK,
                {
                    "score": audit_run.evaluation.score,
                    "grade": audit_run.evaluation.grade,
                    "html_report": audit_run.html_report,
                },
            )

        except Exception as exc:
            self.send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": str(
                        exc
                    ),
                },
            )

    def do_OPTIONS(self) -> None:
        self.send_response(
            HTTPStatus.NO_CONTENT
        )
        self.send_cors_headers()
        self.end_headers()

    def send_json(
        self,
        status: HTTPStatus,
        payload: dict[str, object],
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )

        self.send_response(
            status
        )
        self.send_cors_headers()
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(
                len(body)
            ),
        )
        self.end_headers()
        self.wfile.write(
            body
        )

    def send_cors_headers(self) -> None:
        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )
