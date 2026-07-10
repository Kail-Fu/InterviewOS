from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.core.config import Settings


class SettingsTests(unittest.TestCase):
    def test_development_allows_wildcard_cors(self):
        settings = Settings(app_env="dev", cors_origins=["*"])

        self.assertEqual(settings.cors_origins, ["*"])

    def test_production_rejects_wildcard_cors(self):
        with self.assertRaisesRegex(ValidationError, "CORS_ORIGINS cannot contain"):
            Settings(app_env="production", cors_origins=["*"])

    def test_production_accepts_explicit_cors_origins(self):
        settings = Settings(
            app_env="production",
            cors_origins=["https://interview.example.com"],
        )

        self.assertEqual(settings.cors_origins, ["https://interview.example.com"])


if __name__ == "__main__":
    unittest.main()
