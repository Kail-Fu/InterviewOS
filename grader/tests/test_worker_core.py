from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from app.main import safe_extract, structural_similarity


class WorkerCoreTests(unittest.TestCase):
    def test_safe_extract_blocks_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zipf:
                zipf.writestr("../escape.txt", "bad")
            with self.assertRaises(ValueError):
                safe_extract(archive, root / "out")

    def test_safe_extract_blocks_sibling_prefix_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad-prefix.zip"
            with zipfile.ZipFile(archive, "w") as zipf:
                zipf.writestr("../out-evil/escape.txt", "bad")
            with self.assertRaises(ValueError):
                safe_extract(archive, root / "out")

    def test_structural_similarity_scores_nested_json(self):
        expected = {"name": "Alice", "items": [{"price": 10}, {"price": 20}]}
        actual = {"name": "Alice", "items": [{"price": 10}, {"price": 25}]}
        self.assertGreaterEqual(structural_similarity(expected, actual), 80)
        self.assertEqual(structural_similarity(expected, expected), 100)


if __name__ == "__main__":
    unittest.main()
