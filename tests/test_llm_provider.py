from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from app.llm import OpenAICompatibleProvider


class StubHandler(BaseHTTPRequestHandler):
    authorization = None

    def do_POST(self):
        type(self).authorization = self.headers.get("Authorization")
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        content = json.dumps({"echo_model": request["model"], "ok": True})
        payload = json.dumps({
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return


class ProviderTransportTests(unittest.TestCase):
    def test_openai_compatible_transport_parses_json_and_usage(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {
                "OPENAI_COMPAT_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_ID": "stub-model",
                "API_KEY": "test-key",
                "MODEL_INPUT_USD_PER_MILLION": "1",
                "MODEL_OUTPUT_USD_PER_MILLION": "2",
            }, clear=False):
                provider = OpenAICompatibleProvider()
                result = provider.complete_json("Return JSON", "test")
            self.assertEqual(result.data, {"echo_model": "stub-model", "ok": True})
            self.assertEqual(result.total_tokens, 18)
            self.assertEqual(StubHandler.authorization, "Bearer test-key")
            self.assertGreater(provider.estimated_cost(11, 7), 0)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
