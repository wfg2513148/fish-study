import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fish_study_wiki.models import SourceRecord
from fish_study_wiki.quality import (
    build_quality_report,
    render_quality_report,
    write_quality_reports,
)


def source_row(subject: str = "数学") -> dict[str, str]:
    return {
        "source_id": "demo",
        "subject": subject,
        "grade": "七年级",
        "volume": "下册",
        "version": "浙教版",
        "source_type": "courseware",
        "status": "available",
        "local_path": "/tmp/demo.zip",
        "sha256": "abc",
    }


class QualityTests(unittest.TestCase):
    def test_report_covers_every_matrix_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix_path = root / "matrix.json"
            ledger_path = root / "ledger.json"
            vault = root / "vault"
            matrix = [
                {"grade": "七年级", "volume": "下册", "subject": "数学"},
                {"grade": "七年级", "volume": "下册", "subject": "语文"},
            ]
            matrix_path.write_text(
                json.dumps(matrix, ensure_ascii=False), encoding="utf-8"
            )
            ledger_path.write_text(
                json.dumps([source_row()], ensure_ascii=False), encoding="utf-8"
            )
            subject_dir = vault / "10-教材Wiki" / "七年级" / "下册" / "数学"
            subject_dir.mkdir(parents=True)
            (subject_dir / "00-数学七年级下册索引.md").write_text(
                "index", encoding="utf-8"
            )
            (subject_dir / "专题1.md").write_text("note", encoding="utf-8")

            with patch("fish_study_wiki.quality.validate_available_source"):
                report = build_quality_report(matrix_path, ledger_path, vault)

        self.assertEqual(len(report.rows), 2)
        self.assertEqual(report.rows[0].status, "verified")
        self.assertEqual(report.rows[1].status, "missing_source")

    def test_render_quality_report_includes_coverage_table(self):
        source = SourceRecord(**source_row())

        with patch("fish_study_wiki.quality.validate_available_source"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                matrix_path = root / "matrix.json"
                ledger_path = root / "ledger.json"
                vault = root / "vault"
                matrix_path.write_text(
                    json.dumps(
                        [{"grade": "七年级", "volume": "下册", "subject": "数学"}],
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                ledger_path.write_text(
                    json.dumps([source.__dict__], ensure_ascii=False),
                    encoding="utf-8",
                )
                report = build_quality_report(matrix_path, ledger_path, vault)

        text = render_quality_report(report)

        self.assertIn(
            "| 七年级 | 下册 | 数学 | missing_vault_index | demo | 0 | no |",
            text,
        )

    def test_out_of_matrix_available_source_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix_path = root / "matrix.json"
            ledger_path = root / "ledger.json"
            vault = root / "vault"
            matrix_path.write_text(
                json.dumps(
                    [{"grade": "七年级", "volume": "下册", "subject": "数学"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            ledger_path.write_text(
                json.dumps([source_row(subject="物理")], ensure_ascii=False),
                encoding="utf-8",
            )

            with patch("fish_study_wiki.quality.validate_available_source"):
                report = build_quality_report(matrix_path, ledger_path, vault)

        self.assertFalse(report.passed)
        self.assertIn(
            "available source demo key 七年级/下册/物理 is not in subject matrix",
            report.errors,
        )

    def test_validation_failed_source_row_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix_path = root / "matrix.json"
            ledger_path = root / "ledger.json"
            vault = root / "vault"
            matrix_path.write_text(
                json.dumps(
                    [{"grade": "七年级", "volume": "下册", "subject": "数学"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            ledger_path.write_text(
                json.dumps([source_row()], ensure_ascii=False),
                encoding="utf-8",
            )
            subject_dir = vault / "10-教材Wiki" / "七年级" / "下册" / "数学"
            subject_dir.mkdir(parents=True)
            (subject_dir / "00-数学七年级下册索引.md").write_text(
                "index", encoding="utf-8"
            )
            (subject_dir / "专题1.md").write_text("note", encoding="utf-8")

            with patch(
                "fish_study_wiki.quality.validate_available_source",
                side_effect=ValueError("available source demo sha256 mismatch"),
            ):
                report = build_quality_report(matrix_path, ledger_path, vault)

        text = render_quality_report(report)

        self.assertFalse(report.passed)
        self.assertEqual(report.rows[0].status, "source_error")
        self.assertIn("- Verified rows: 0", text)
        self.assertIn("| 七年级 | 下册 | 数学 | source_error | demo | 1 | yes |", text)

    def test_write_quality_reports_writes_repo_and_vault_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix_path = root / "matrix.json"
            ledger_path = root / "ledger.json"
            vault = root / "vault"
            repo_report = root / "reports" / "wiki-quality.md"
            vault_report = vault / "00-入口" / "wiki-quality.md"
            matrix_path.write_text("[]", encoding="utf-8")
            ledger_path.write_text("[]", encoding="utf-8")
            report = build_quality_report(matrix_path, ledger_path, vault)

            write_quality_reports(report, repo_report, vault_report)

            self.assertTrue(repo_report.exists())
            self.assertEqual(
                repo_report.read_text(encoding="utf-8"),
                vault_report.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
