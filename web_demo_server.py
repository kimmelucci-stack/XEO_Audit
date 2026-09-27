from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from audit_runner import run_audit


HOST = "127.0.0.1"
PORT = 8080
WEB_ROOT = Path(__file__).resolve().parent / "web"


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            directory=str(WEB_ROOT),
            **kwargs,
        )

    def do_POST(self) -> None:
        if self.path != "/api/audit":
            self.send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "Not found",
                },
            )
            return

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


def main() -> None:
    server = ThreadingHTTPServer(
        (
            HOST,
            PORT,
        ),
        DemoRequestHandler,
    )

    print(
        f"XEO Audit demo running at http://{HOST}:{PORT}"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
