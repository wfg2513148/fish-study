import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.source_ledger import load_sources, missing_matrix_entries


class SourceLedgerTests(unittest.TestCase):
    def test_load_sources_returns_source_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-ledger.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "source_id": "demo",
                            "subject": "数学",
                            "grade": "七年级",
                            "volume": "下册",
                            "version": "浙教版",
                            "source_type": "courseware",
                            "status": "available",
                            "local_path": "/tmp/demo.zip",
                            "sha256": "abc",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            sources = load_sources(path)

        self.assertEqual(sources[0].key, "七年级/下册/数学")

    def test_missing_matrix_entries_reports_uncovered_subjects(self):
        matrix = [
            {"grade": "七年级", "volume": "下册", "subject": "数学"},
            {"grade": "七年级", "volume": "下册", "subject": "语文"},
        ]
        covered = {"七年级/下册/数学"}

        self.assertEqual(
            missing_matrix_entries(matrix, covered),
            ["七年级/下册/语文"],
        )


if __name__ == "__main__":
    unittest.main()
