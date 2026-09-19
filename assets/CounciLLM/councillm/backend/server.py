"""Minimal offline AI Council development server.

This foundation intentionally does not start an inference engine or alter the
frontend.  It serves static files and defines the small API boundary that the
frontend will use as the council features are introduced.
"""

from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "council.json"


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open(encoding="utf-8") as file:
        return json.load(file)


def resolve_path(value: str, config_path: Path) -> Path:
    candidate = Path(os.path.expandvars(value))
    return candidate if candidate.is_absolute() else (config_path.parent / candidate).resolve()


class CouncilHandler(SimpleHTTPRequestHandler):
    """Static-file handler with a deliberately small, versionable JSON API."""

    server_version = "AICouncil/0.1"

    @property
    def council_config(self) -> dict[str, Any]:
        return self.server.council_config  # type: ignore[attr-defined]

    @property
    def config_path(self) -> Path:
        return self.server.config_path  # type: ignore[attr-defined]

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by http.server
        request_path = urlparse(self.path).path
        if request_path == "/api/health":
            self.send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "mode": "offline-development",
                    "inference": "not-started",
                    "message": "Backend skeleton is running; no model runtime is started yet.",
                },
            )
            return

        if request_path == "/api/models":
            models = []
            for item in self.council_config.get("models", []):
                model_path = resolve_path(item["path"], self.config_path)
                models.append(
                    {
                        "id": item["id"],
                        "role": item["role"],
                        "path": str(model_path),
                        "available": model_path.is_file(),
                        "notes": item.get("notes", ""),
                    }
                )
            self.send_json(HTTPStatus.OK, {"models": models, "runtime": "not-configured"})
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - required by http.server
        request_path = urlparse(self.path).path
        if request_path.startswith("/api/"):
            self.send_json(
                HTTPStatus.NOT_IMPLEMENTED,
                {
                    "error": "The local inference pipeline has not been implemented yet.",
                    "requested_endpoint": request_path,
                },
            )
            return
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline AI Council foundation server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), type=Path)
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = load_config(config_path)
    frontend_dir = resolve_path(config["frontend_dir"], config_path)
    if not frontend_dir.is_dir():
        raise SystemExit(
            f"Frontend directory is missing: {frontend_dir}\n"
            "Copy the existing HTML project there or update config/council.json."
        )

    handler = lambda *handler_args, **handler_kwargs: CouncilHandler(  # noqa: E731
        *handler_args, directory=str(frontend_dir), **handler_kwargs
    )
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    httpd.council_config = config  # type: ignore[attr-defined]
    httpd.config_path = config_path  # type: ignore[attr-defined]
    print(f"AI Council foundation: http://{args.host}:{args.port}")
    print(f"Serving frontend: {frontend_dir}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
