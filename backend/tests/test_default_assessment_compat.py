from __future__ import annotations

from io import BytesIO
import tempfile
import unittest
from pathlib import Path

from fastapi import BackgroundTasks, UploadFile

from app.api.assessment import StartAssessmentRequest, _resolve_start_assessment
from app.api.candidate import (
    _resolve_assessment_id,
    public_assessment,
    upload_assessment4,
    upload_zip,
)
from app.core.config import Settings
from app.services.assessment_store import (
    get_latest_candidate_by_assessment,
    get_report_by_candidate,
    init_assessment_store,
)


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


class DefaultAssessmentUploadTests(unittest.IsolatedAsyncioTestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            local_db_path=str(root / "data" / "test.sqlite3"),
            local_submissions_dir=str(root / "submissions"),
            local_recordings_dir=str(root / "recordings"),
            local_assets_dir=str(root / "assets"),
        )

    async def test_zip_upload_resolves_default_and_creates_pending_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)

            payload = await upload_zip(
                background_tasks=BackgroundTasks(),
                zipFile=UploadFile(filename="submission.zip", file=BytesIO(b"zip-data")),
                assessmentId="default",
                name="Candidate",
                email="candidate@example.com",
                settings=settings,
            )

            candidate = get_latest_candidate_by_assessment(settings, 1)
            self.assertIsNotNone(candidate)
            self.assertEqual(payload["assessmentId"], 1)
            self.assertEqual(payload["reportId"], candidate.id)
            self.assertIsNotNone(get_report_by_candidate(settings, candidate.id))

    async def test_assessment4_upload_resolves_default_and_creates_pending_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)

            payload = await upload_assessment4(
                background_tasks=BackgroundTasks(),
                submissionZip=UploadFile(filename="submission.zip", file=BytesIO(b"zip-data")),
                notebookFile=UploadFile(filename="notebook.ipynb", file=BytesIO(b"{}")),
                assessmentId="default",
                name="Candidate",
                email="candidate@example.com",
                settings=settings,
            )

            candidate = get_latest_candidate_by_assessment(settings, 1)
            self.assertIsNotNone(candidate)
            self.assertEqual(payload["assessmentId"], 1)
            self.assertEqual(payload["reportId"], candidate.id)
            self.assertIsNotNone(get_report_by_candidate(settings, candidate.id))


if __name__ == "__main__":
    unittest.main()
