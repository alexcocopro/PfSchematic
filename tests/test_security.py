from pathlib import Path
import sys
import unittest

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

    def test_library_route_is_allowlisted(self):
        client = app.test_client()
        response = client.get("/lib/tom-select/tom-select.css", headers={"Host": "localhost"})

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
