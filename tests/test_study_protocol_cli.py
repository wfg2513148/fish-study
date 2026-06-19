import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki import cli
from fish_study_wiki import study_protocol_cli


class StudyProtocolCliTests(unittest.TestCase):
    def test_protocol_subcommands_write_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_root = root / "outputs"
            vault_root = root / "vault"

            cases = (
                (
                    "homework",
                    "samples/homework-plan.json",
                    (
                        output_root / "2026-06-19" / "today-study-plan.html",
                        output_root / "2026-06-19" / "today-study-plan-parent.md",
                        vault_root / "30-每日学习计划" / "2026-06-19.md",
                    ),
                ),
                (
                    "wrong",
                    "samples/wrong-question-review.json",
                    (
                        output_root / "2026-06-19" / "wrong-question-review.html",
                        output_root / "2026-06-19" / "wrong-question-review-parent.md",
                        vault_root / "20-错题归因" / "2026-06-19.md",
                    ),
                ),
                (
                    "review-plan",
                    "samples/review-plan-source.json",
                    (
                        output_root / "2026-06-19" / "review-plan.md",
                        vault_root / "40-复习计划" / "2026-06-19.md",
                    ),
                ),
            )

            for command, sample, expected_paths in cases:
                with self.subTest(command=command):
                    stdout, stderr, status = self._run_protocol(
                        command,
                        sample,
                        "--output-root",
                        str(output_root),
                        "--vault-root",
                        str(vault_root),
                    )

                    self.assertEqual(status, 0, stderr)
                    self.assertEqual(stderr, "")
                    for path in expected_paths:
                        self.assertTrue(path.exists(), path)
                        self.assertIn(str(path), stdout)

    def test_main_cli_study_aliases_delegate_to_protocol_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_root = root / "outputs"
            vault_root = root / "vault"

            cases = (
                (
                    "study-homework",
                    "samples/homework-plan.json",
                    output_root / "2026-06-19" / "today-study-plan.html",
                ),
                (
                    "study-wrong",
                    "samples/wrong-question-review.json",
                    output_root / "2026-06-19" / "wrong-question-review.html",
                ),
                (
                    "study-review-plan",
                    "samples/review-plan-source.json",
                    output_root / "2026-06-19" / "review-plan.md",
                ),
            )

            for command, sample, expected_path in cases:
                with self.subTest(command=command):
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        status = cli.main(
                            [
                                command,
                                sample,
                                "--output-root",
                                str(output_root),
                                "--vault-root",
                                str(vault_root),
                            ]
                        )

                    self.assertEqual(status, 0)
                    self.assertTrue(expected_path.exists())
                    self.assertIn(str(expected_path), stdout.getvalue())

    def test_quality_check_failure_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_input = root / "bad-homework.json"
            bad_input.write_text(
                json.dumps(
                    {
                        "task_type": "homework_plan",
                        "date": "2026-06-19",
                        "items": [
                            {
                                "subject": "数学",
                                "raw_text": "完成第1题",
                                "book_or_source": "作业本",
                                "page": "12",
                                "question_range": "1",
                                "deadline": "今晚",
                                "matched_knowledge": [],
                                "status": "matched",
                            }
                        ],
                        "uncertain_items": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            stdout, stderr, status = self._run_protocol(
                "homework",
                str(bad_input),
                "--output-root",
                str(root / "outputs"),
                "--vault-root",
                str(root / "vault"),
            )

            self.assertEqual(status, 1)
            self.assertEqual(stdout, "")
            self.assertIn("ERROR:", stderr)
            self.assertIn("knowledge_link_or_pending", stderr)
            self.assertFalse((root / "outputs" / "2026-06-19").exists())

    def _run_protocol(self, *args: str) -> tuple[str, str, int]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = study_protocol_cli.main(list(args))
        return stdout.getvalue(), stderr.getvalue(), status


if __name__ == "__main__":
    unittest.main()
