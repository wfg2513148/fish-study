import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki import cli
from fish_study_wiki import study_protocol_cli


class StudyProtocolCliTests(unittest.TestCase):
    def test_wrong_command_writes_student_answer_and_obsidian_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stdout, stderr, status = self._run_protocol(
                "wrong",
                "samples/wrong-question-training.json",
                "--output-root",
                str(root / "outputs"),
                "--vault-root",
                str(root / "vault"),
            )

            expected = (
                root / "outputs" / "2026-06-19" / "wrong-question-training.html",
                root / "outputs" / "2026-06-19" / "wrong-question-training-answers.html",
                root / "outputs" / "2026-06-19" / "science-training.html",
                root / "outputs" / "2026-06-19" / "science-training-answers.html",
                root / "outputs" / "2026-06-19" / "science-knowledge.md",
                root / "outputs" / "2026-06-19" / "math-training.html",
                root / "outputs" / "2026-06-19" / "math-training-answers.html",
                root / "outputs" / "2026-06-19" / "math-knowledge.md",
                root / "vault" / "20-错题归因" / "2026-06-19.md",
            )
            self.assertEqual(status, 0, stderr)
            self.assertEqual(stderr, "")
            for path in expected:
                self.assertTrue(path.exists(), path)
                self.assertIn(str(path), stdout)

    def test_weekly_review_command_writes_report_student_answer_and_obsidian_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stdout, stderr, status = self._run_protocol(
                "weekly-review",
                "samples/weekly-review-source.json",
                "--output-root",
                str(root / "outputs"),
                "--vault-root",
                str(root / "vault"),
            )

            expected = (
                root / "outputs" / "2026-06-21" / "weekly-review.md",
                root / "outputs" / "2026-06-21" / "weekly-review.html",
                root / "outputs" / "2026-06-21" / "weekly-review-answers.html",
                root / "vault" / "40-复习计划" / "2026-06-21.md",
            )
            self.assertEqual(status, 0, stderr)
            self.assertEqual(stderr, "")
            for path in expected:
                self.assertTrue(path.exists(), path)
                self.assertIn(str(path), stdout)

    def test_main_cli_study_aliases_delegate_to_protocol_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_root = root / "outputs"
            vault_root = root / "vault"

            cases = (
                (
                    "study-wrong",
                    "samples/wrong-question-training.json",
                    output_root / "2026-06-19" / "wrong-question-training.html",
                ),
                (
                    "study-weekly-review",
                    "samples/weekly-review-source.json",
                    output_root / "2026-06-21" / "weekly-review.md",
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

    def test_removed_protocol_commands_return_argparse_error(self):
        for command in ("home" + "work", "review" + "-plan"):
            with self.subTest(command=command):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        study_protocol_cli.main([command, "unused.json"])

                self.assertIn("invalid choice", stderr.getvalue())

    def test_removed_main_aliases_return_argparse_error(self):
        for command in ("study-" + "home" + "work", "study-" + "review" + "-plan"):
            with self.subTest(command=command):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        cli.main([command, "unused.json"])

                self.assertIn("invalid choice", stderr.getvalue())

    def test_quality_check_failure_returns_nonzero_without_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_input = root / "bad-training.json"
            data = json.loads(
                Path("samples/wrong-question-training.json").read_text(encoding="utf-8")
            )
            data["clusters"][0]["training_questions"] = []
            bad_input.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            stdout, stderr, status = self._run_protocol(
                "wrong",
                str(bad_input),
                "--output-root",
                str(root / "outputs"),
                "--vault-root",
                str(root / "vault"),
            )

            self.assertEqual(status, 1)
            self.assertEqual(stdout, "")
            self.assertIn("ERROR:", stderr)
            self.assertIn("training_questions_present", stderr)
            self.assertFalse((root / "outputs" / "2026-06-19").exists())

    def test_invalid_date_cannot_escape_output_or_vault_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_input = root / "bad-weekly.json"
            data = json.loads(
                Path("samples/weekly-review-source.json").read_text(encoding="utf-8")
            )
            data["week_end"] = "../escaped"
            bad_input.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            stdout, stderr, status = self._run_protocol(
                "weekly-review",
                str(bad_input),
                "--output-root",
                str(root / "outputs"),
                "--vault-root",
                str(root / "vault"),
            )

            self.assertEqual(status, 1)
            self.assertEqual(stdout, "")
            self.assertIn("ERROR:", stderr)
            self.assertFalse((root / "escaped").exists())
            self.assertFalse((root / "vault" / "escaped.md").exists())

    def _run_protocol(self, *args: str) -> tuple[str, str, int]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = study_protocol_cli.main(list(args))
        return stdout.getvalue(), stderr.getvalue(), status


if __name__ == "__main__":
    unittest.main()
