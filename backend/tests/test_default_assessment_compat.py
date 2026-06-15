from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.api.assessment import StartAssessmentRequest, _resolve_start_assessment
from app.api.candidate import _resolve_assessment_id, public_assessment
from app.core.config import Settings
from app.services.assessment_store import init_assessment_store


class DefaultAssessmentCompatibilityTests(unittest.TestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            local_db_path=str(root / "data" / "test.sqlite3"),
            local_submissions_dir=str(root / "submissions"),
            local_recordings_dir=str(root / "recordings"),
            local_assets_dir=str(root / "assets"),
        )

    def test_default_assessment_id_resolves_to_seeded_numeric_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)

            self.assertEqual(_resolve_assessment_id("default", settings), 1)
            self.assertEqual(_resolve_assessment_id("", settings), 1)
            self.assertEqual(_resolve_assessment_id(1, settings), 1)

    def test_public_default_assessment_returns_canonical_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)

            payload = public_assessment("default", settings)

            self.assertEqual(payload["id"], 1)
            self.assertEqual(payload["title"], "Backend API Work Simulation")

    def test_start_assessment_accepts_default_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)

            assessment = _resolve_start_assessment(
                StartAssessmentRequest(
                    name="Candidate",
                    email="candidate@example.com",
                    assessmentId="default",
                ),
                settings,
            )

            self.assertIsNotNone(assessment)
            self.assertEqual(assessment.id, 1)


if __name__ == "__main__":
    unittest.main()
