import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fish_study_wiki import cli


class CliTests(unittest.TestCase):
    def test_inventory_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_inventory", return_value=0) as run:
            self.assertEqual(cli.main(["inventory"]), 0)

        run.assert_called_once_with()

    def test_build_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_build", return_value=0) as run:
            self.assertEqual(cli.main(["build"]), 0)

        run.assert_called_once_with()

    def test_verify_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_verify", return_value=0) as run:
            self.assertEqual(cli.main(["verify"]), 0)

        run.assert_called_once_with()

    def test_study_context_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_study_context", return_value=0) as run:
            self.assertEqual(cli.main(["study-context"]), 0)

        run.assert_called_once_with()

    def test_study_context_lists_available_sources_and_note_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix_path = root / "matrix.json"
            ledger_path = root / "ledger.json"
            vault = root / "vault"
            subject_dir = vault / "10-教材Wiki" / "七年级" / "下册" / "数学"
            subject_dir.mkdir(parents=True)
            (subject_dir / "00-数学七年级下册索引.md").write_text(
                "# index\n",
                encoding="utf-8",
            )
            (subject_dir / "第1章 1.1 直线的相交.md").write_text(
                "# topic\n",
                encoding="utf-8",
            )
            matrix_path.write_text(
                json.dumps(
                    [
                        {
                            "grade": "七年级",
                            "volume": "下册",
                            "subject": "数学",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            ledger_path.write_text(
                json.dumps(
                    [
                        {
                            "source_id": "demo-math",
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

            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                status = cli.run_study_context(matrix_path, ledger_path, vault)

            self.assertEqual(status, 0)
            text = stdout.getvalue()
            self.assertIn("当前可用资料：1 套", text)
            self.assertIn("七年级下册数学：浙教版，demo-math，知识点笔记 1 篇", text)
            self.assertIn("note: 待定位", text)

    def test_unknown_command_prints_usage(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit):
                cli.main(["unknown"])

        self.assertIn("invalid choice", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
