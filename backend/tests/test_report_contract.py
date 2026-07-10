from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from app.core.config import Settings
from app.services.assessment_store import (
    init_assessment_store,
    list_reflection_uploads_for_candidate,
    list_questions,
    question_to_payload,
    record_reflection_upload,
    upsert_report,
    get_report_by_candidate,
)
from app.services.report_engine import _detect_assessment_type, _reflection_payload


class ReportContractTests(unittest.TestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            local_db_path=str(root / "data" / "test.sqlite3"),
            local_submissions_dir=str(root / "submissions"),
            local_recordings_dir=str(root / "recordings"),
            local_assets_dir=str(root / "assets"),
        )

    def test_report_payload_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)
            report = upsert_report(
                settings,
                candidate_id=42,
                assessment_id=1,
                score=91,
                code_quality=83,
                results=[{"name": "check", "status": "pass"}],
                diffs=[{"path": "server.js"}],
                code_summary_bullets=["Executed grader."],
                report_ready=True,
                error=None,
                assessment_type="default",
                app_usage=[{"name": "Screen Recording", "duration": 12}],
                total_duration=12,
                submission_file="1-demo.zip",
                assessment_recording_key="recordings/demo.webm",
                reflection_recording_key=None,
                payload={"status": "ready", "questionData": {"title": "Users API"}},
            )
            fetched = get_report_by_candidate(settings, report.candidate_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.payload["status"], "ready")
            self.assertEqual(fetched.payload["questionData"]["title"], "Users API")

    def test_seeded_question_payloads_are_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)
            payloads = [question_to_payload(question) for question in list_questions(settings)]
            titles = {payload["title"] for payload in payloads if payload}
            self.assertIn("Users API", titles)
            self.assertIn("Supreme Court Q&A RAG System", titles)
            self.assertIn("Named Entity Recognition (NER) - Product Attributes", titles)
            self.assertIn("Insurance Document Processor - LlamaIndex API", titles)

    def test_assessment_type_detection_is_allowlisted(self):
        self.assertEqual(_detect_assessment_type("assessment3-rag"), "assessment3-rag")
        self.assertEqual(_detect_assessment_type("assessment4-ner"), "assessment4-ner")
        self.assertEqual(_detect_assessment_type("json-comparison"), "json-comparison")
        self.assertEqual(_detect_assessment_type("unexpected"), "default")

    def test_reflection_uploads_keep_latest_per_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            init_assessment_store(settings)
            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="demo_work",
                s3_key="reflection/1/old-demo.webm",
            )
            time.sleep(0.001)
            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="demo_work",
                s3_key="reflection/1/new-demo.webm",
            )
            time.sleep(0.001)
            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="struggles",
                s3_key="reflection/1/struggles.webm",
            )

            uploads = list_reflection_uploads_for_candidate(
                settings,
                assessment_id=1,
                email="candidate@example.com",
            )

            self.assertEqual([upload["s3Key"] for upload in uploads], [
                "reflection/1/new-demo.webm",
                "reflection/1/struggles.webm",
            ])

    def test_reflection_payload_ignores_empty_recordings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = self.make_settings(root)
            init_assessment_store(settings)
            recordings_root = root / "recordings"
            good = recordings_root / "reflection/1/demo_work-good.webm"
            empty = recordings_root / "reflection/1/struggles-empty.webm"
            good.parent.mkdir(parents=True, exist_ok=True)
            good.write_bytes(b"webm-data")
            empty.write_bytes(b"")

            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="demo_work",
                s3_key="reflection/1/demo_work-good.webm",
            )
            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="struggles",
                s3_key="reflection/1/struggles-empty.webm",
            )

            payload = _reflection_payload(settings, 1, "candidate@example.com")

            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["sectionId"], "demo_work")
            self.assertEqual(payload[0]["s3Key"], "reflection/1/demo_work-good.webm")

    def test_reflection_payload_rejects_paths_outside_recordings_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = self.make_settings(root)
            init_assessment_store(settings)
            outside = root / "outside.webm"
            outside.write_bytes(b"webm-data")

            record_reflection_upload(
                settings,
                assessment_id=1,
                email="candidate@example.com",
                section_id="demo_work",
                s3_key="../outside.webm",
            )

            payload = _reflection_payload(settings, 1, "candidate@example.com")

            self.assertEqual(payload, [])


if __name__ == "__main__":
    unittest.main()
