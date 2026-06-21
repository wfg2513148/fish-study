import contextlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from fish_study_wiki import cli
from fish_study_wiki import study_protocol_cli


TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00"
    b"\x1b\xb6\xeeV\x00\x00\x00\x00IEND\xaeB`\x82"
)


class StudyProtocolCliTests(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "fish_study_wiki.study_protocol_writer.prepare_knowledge_card_diagrams",
            side_effect=_fake_knowledge_card_diagrams,
        )
        self.addCleanup(patcher.stop)
        patcher.start()

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
                root / "outputs" / "2026-06-19" / "wrong-question-training.pdf",
                root / "outputs" / "2026-06-19" / "wrong-question-training-answers.pdf",
                root / "outputs" / "2026-06-19" / "science-training.pdf",
                root / "outputs" / "2026-06-19" / "science-training-answers.pdf",
                root / "outputs" / "2026-06-19" / "science-knowledge.md",
                root / "outputs" / "2026-06-19" / "math-training.pdf",
                root / "outputs" / "2026-06-19" / "math-training-answers.pdf",
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
                root / "outputs" / "2026-06-21" / "weekly-review.pdf",
                root / "outputs" / "2026-06-21" / "weekly-review-answers.pdf",
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
                    output_root / "2026-06-19" / "wrong-question-training.pdf",
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


def _fake_knowledge_card_diagrams(training, subject, output_dir):
    asset_dir = output_dir / "test-knowledge-card-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets = {}
    for index, cluster in enumerate(
        (item for item in training.clusters if item.subject == subject),
        start=1,
    ):
        for match in cluster.matched_knowledge:
            path = asset_dir / f"{subject}-{index}.png"
            path.write_bytes(TINY_PNG)
            assets[match.note] = path
    return assets


if __name__ == "__main__":
    unittest.main()
