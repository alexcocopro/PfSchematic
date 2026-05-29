from pathlib import Path
from io import BytesIO
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app


class SecurityTests(unittest.TestCase):
    def test_security_headers_are_sent(self):
        client = app.test_client()
        response = client.get("/api/health", headers={"Host": "localhost"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_untrusted_host_is_rejected(self):
        client = app.test_client()
        response = client.get("/api/health", headers={"Host": "evil.example"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("error", response.get_json())

    def test_large_upload_error_is_json(self):
        client = app.test_client()
        previous_limit = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 32
        try:
            response = client.post(
                "/api/upload",
                data={"xml": (BytesIO(b"<pfsense>" + (b"x" * 256) + b"</pfsense>"), "large.xml")},
                content_type="multipart/form-data",
                headers={"Host": "localhost"},
            )
        finally:
            app.config["MAX_CONTENT_LENGTH"] = previous_limit

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("limite", response.get_json()["error"])

    def test_unexpected_api_error_is_json(self):
        client = app.test_client()

        with patch("app._payload_from_path", side_effect=RuntimeError("boom")), self.assertLogs(app.logger.name, level="ERROR"):
            response = client.get("/api/sample", headers={"Host": "localhost"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("error", response.get_json())

    def test_library_route_is_allowlisted(self):
        client = app.test_client()
        response = client.get("/lib/tom-select/tom-select.css", headers={"Host": "localhost"})

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
