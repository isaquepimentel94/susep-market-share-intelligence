"""Checks for the deployment HTTP boundary."""

import unittest
from unittest.mock import Mock

from werkzeug.test import Client

from server import create_app


class WebDeployment(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.service.catalog = {"entities": []}
        self.client = Client(create_app(self.service))

    def test_health_and_unconfigured_download(self):
        health = self.client.get("/healthz")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json, {"status": "ok"})
        self.assertEqual(health.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get("/api/catalog").json, self.service.catalog)
        self.service.analyze.assert_not_called()

        with self.assertRaisesRegex(ValueError, "SUSEP_PBIX_URL"):
            create_app(self.service, "file:///report.pbix")

    def test_web_root_exposes_only_frontend_assets(self):
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'id="pbix-download" rel="noreferrer" hidden', response.data)
        for path in ("/data/curated/fato_premios_uf.parquet", "/requirements.txt", "/%2e%2e/server.py"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post("/api/catalog").status_code, 405)
