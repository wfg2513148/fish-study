import tempfile
import unittest
from pathlib import Path

from fish_study_wiki import settings
from fish_study_wiki.study_protocol_models import (
    load_weekly_review_source,
    load_wrong_question_training,
)
from fish_study_wiki.study_protocol_writer import (
    DEFAULT_VAULT_ROOT,
    write_training_outputs,
    write_weekly_review_outputs,
)


ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")


def training_sample():
    return load_wrong_question_training(Path("samples/wrong-question-training.json"))


def weekly_sample():
    return load_weekly_review_source(Path("samples/weekly-review-source.json"))


class StudyProtocolWriterTests(unittest.TestCase):
    def test_default_vault_root_uses_settings_path(self):
        self.assertEqual(DEFAULT_VAULT_ROOT, settings.VAULT_ROOT)

    def test_training_outputs_write_student_answer_and_obsidian_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            self.assertEqual(result.student_html.name, "wrong-question-training.html")
            self.assertEqual(result.answer_html.name, "wrong-question-training-answers.html")
            self.assertEqual(result.student_html.parent.name, "2026-06-19")
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "20-错题归因" / "2026-06-19.md",
            )
            self.assertTrue(result.student_html.exists())
            self.assertTrue(result.answer_html.exists())
            self.assertTrue(result.obsidian_note.exists())
            self.assertEqual(
                [output.subject for output in result.subject_outputs],
                ["科学", "数学"],
            )
            self.assertTrue((root / "data" / "wiki" / "knowledge-graph.json").exists())
            self.assertIn("批改答案页", result.obsidian_note.read_text(encoding="utf-8"))
            subject_files = {
                path.name
                for output in result.subject_outputs
                for path in (
                    output.student_html,
                    output.answer_html,
                    output.knowledge_markdown,
                )
            }
            self.assertEqual(
                subject_files,
                {
                    "science-training.html",
                    "science-training-answers.html",
                    "science-knowledge.md",
                    "math-training.html",
                    "math-training-answers.html",
                    "math-knowledge.md",
                },
            )

    def test_training_student_file_has_no_answer_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            student_text = result.student_html.read_text(encoding="utf-8")
            answer_text = result.answer_html.read_text(encoding="utf-8")
            for marker in ANSWER_MARKERS:
                self.assertNotIn(marker, student_text)
            self.assertIn("答案", answer_text)

    def test_subject_training_outputs_are_subject_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            by_subject = {output.subject: output for output in result.subject_outputs}
            math_text = by_subject["数学"].student_html.read_text(encoding="utf-8")
            science_text = by_subject["科学"].student_html.read_text(encoding="utf-8")
            math_knowledge = by_subject["数学"].knowledge_markdown.read_text(
                encoding="utf-8"
            )
            self.assertIn("平行线", math_text)
            self.assertNotIn("原子结构", math_text)
            self.assertIn("原子结构", science_text)
            self.assertNotIn("平行线角关系", science_text)
            self.assertIn("photo-002", math_knowledge)
            self.assertIn("知识点与根因", math_knowledge)

    def test_training_appends_event_blocks_to_knowledge_notes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            result = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=vault,
            )
            second = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=vault,
            )

            self.assertEqual(result.event_notes, second.event_notes)
            self.assertEqual(len(result.event_notes), 2)
            for note_path in result.event_notes:
                text = note_path.read_text(encoding="utf-8")
                self.assertEqual(text.count("2026-06-19 错题分析事件"), 1)
                self.assertIn("来源批次：2026-06-19-evening-wrong-questions", text)

    def test_pending_training_cluster_does_not_append_long_term_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_training_outputs(
                training_sample(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            event_text = "\n".join(
                path.read_text(encoding="utf-8") for path in result.event_notes
            )
            self.assertNotIn("审题漏条件", event_text)
            self.assertIn(
                "数学 角关系计算 审题漏条件 待确认",
                result.obsidian_note.read_text(encoding="utf-8"),
            )

    def test_weekly_review_outputs_write_report_student_answer_and_obsidian_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_weekly_review_outputs(
                weekly_sample(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            self.assertEqual(result.report_markdown.name, "weekly-review.md")
            self.assertEqual(result.student_html.name, "weekly-review.html")
            self.assertEqual(result.answer_html.name, "weekly-review-answers.html")
            self.assertEqual(result.report_markdown.parent.name, "2026-06-21")
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "40-复习计划" / "2026-06-21.md",
            )
            self.assertIn("难度是否合适", result.report_markdown.read_text(encoding="utf-8"))
            self.assertIn("错题周复盘", result.obsidian_note.read_text(encoding="utf-8"))
            for marker in ANSWER_MARKERS:
                self.assertNotIn(marker, result.student_html.read_text(encoding="utf-8"))
            self.assertIn("答案", result.answer_html.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
