from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from pydantic import ValidationError

from app.engine import TroubleshootingEngine
from app.models import HealthResponse, TroubleshootRequest


ROOT = Path(__file__).resolve().parents[1]
ENGINE = TroubleshootingEngine(ROOT / "data")
STATIC = ROOT / "static"


class GuideRailHandler(BaseHTTPRequestHandler):
    server_version = "GuideRail/1.0"
    max_request_bytes = 64 * 1024

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": "not_found"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/health":
            payload = HealthResponse(
                status="ok", catalog_entries=len(ENGINE.deeplinks), knowledge_records=len(ENGINE.records),
                cache_entries=len(ENGINE.cache), catalog_version=ENGINE.catalog_version,
                data_source=ENGINE.data_source, llm_available=ENGINE.llm.available,
                model_id=ENGINE.llm.model or None,
                checks={"schema": "ready", "catalog": "ready", "cache": "ready", "assets": "ready"},
            )
            self._send_json(payload.model_dump(mode="json"))
        elif route == "/metrics":
            self._send_json(ENGINE.stats())
        elif route in {"/", "/index.html"}:
            self._send_file(STATIC / "index.html", "text/html; charset=utf-8")
        elif route == "/app.css":
            self._send_file(STATIC / "app.css", "text/css; charset=utf-8")
        elif route == "/app.js":
            self._send_file(STATIC / "app.js", "text/javascript; charset=utf-8")
        else:
            self._send_json({"error": "not_found"}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/v1/troubleshoot":
            self._send_json({"error": "not_found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > self.max_request_bytes:
                self._send_json({"error": "invalid_request_size"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return
            payload = json.loads(self.rfile.read(length) or b"{}")
            request = TroubleshootRequest.model_validate(payload)
            result = ENGINE.troubleshoot(request)
            self._send_json(result.model_dump(mode="json"))
        except (json.JSONDecodeError, ValidationError) as exc:
            self._send_json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.UNPROCESSABLE_ENTITY)
        except Exception as exc:
            self._send_json({"error": "internal_error", "detail": type(exc).__name__}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:
        if os.getenv("QUIET") != "1":
            super().log_message(format, *args)


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"GuideRail listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), GuideRailHandler).serve_forever()


if __name__ == "__main__":
    main()
