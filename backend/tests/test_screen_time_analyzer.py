from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.screen_time_analyzer import _probe_duration_seconds, analyze_screen_time


class ScreenTimeAnalyzerTests(unittest.TestCase):
    def test_missing_recording_returns_empty_usage(self):
        usage, total_duration = analyze_screen_time("missing.webm")

        self.assertEqual(usage, [])
        self.assertEqual(total_duration, 0)

    def test_probe_timeout_returns_zero_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            recording = Path(tmp) / "recording.webm"
            recording.write_bytes(b"webm-data")

            with patch("app.services.screen_time_analyzer.subprocess.run") as run:
                run.side_effect = subprocess.TimeoutExpired(["ffprobe"], timeout=30)

                self.assertEqual(_probe_duration_seconds(recording), 0)
                self.assertEqual(analyze_screen_time(recording), ([], 0))
                self.assertEqual(run.call_args.kwargs["timeout"], 30)

    def test_valid_duration_returns_single_usage_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            recording = Path(tmp) / "recording.webm"
            recording.write_bytes(b"webm-data")

            with patch("app.services.screen_time_analyzer.subprocess.run") as run:
                run.return_value.stdout = "12.4\n"

                usage, total_duration = analyze_screen_time(recording)

        self.assertEqual(total_duration, 12)
        self.assertEqual(usage, [{"name": "Screen Recording", "duration": 12}])


if __name__ == "__main__":
    unittest.main()
