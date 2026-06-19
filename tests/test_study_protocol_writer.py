import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    HomeworkItem,
    HomeworkPlan,
    KnowledgeMatch,
    WrongQuestionItem,
    WrongQuestionReview,
)
from fish_study_wiki.study_protocol_writer import (
    write_homework_outputs,
    write_wrong_question_outputs,
)


def knowledge(note: str = "第1章 1.1 直线的相交") -> KnowledgeMatch:
    return KnowledgeMatch(
        grade="七年级",
        volume="下册",
        chapter="第1章",
        note=note,
        confidence="high",
    )


def homework_plan() -> HomeworkPlan:
    return HomeworkPlan(
        task_type="homework_plan",
        date="2026-06-19",
        items=(
            HomeworkItem(
                subject="数学",
                raw_text="完成作业本第12页第1-3题",
                book_or_source="作业本",
                page="12",
                question_range="1-3",
                deadline="今晚",
                matched_knowledge=(knowledge(),),
                status="matched",
            ),
        ),
        uncertain_items=("无",),
    )


def wrong_review() -> WrongQuestionReview:
    return WrongQuestionReview(
        task_type="wrong_question_review",
        date="2026-06-19",
        items=(
            WrongQuestionItem(
                subject="数学",
                question_id="第12题",
                sticker_color="yellow",
                reason="马虎",
                problem_type="计算",
                matched_knowledge=(knowledge(),),
                next_action="整理审题和符号检查清单",
            ),
        ),
        uncertain_items=(),
    )


class StudyProtocolWriterTests(unittest.TestCase):
    def test_write_homework_outputs_to_dated_output_and_daily_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_homework_outputs(
                homework_plan(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            self.assertEqual(result.student_html.name, "today-study-plan.html")
            self.assertEqual(result.parent_markdown.name, "today-study-plan-parent.md")
            self.assertEqual(result.student_html.parent.name, "2026-06-19")
            self.assertTrue(result.student_html.exists())
            self.assertTrue(result.parent_markdown.exists())
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "30-每日学习计划" / "2026-06-19.md",
            )
            self.assertIn("每日学习计划", result.obsidian_note.read_text(encoding="utf-8"))
            self.assertIn(str(result.student_html), result.obsidian_note.read_text(encoding="utf-8"))

    def test_write_wrong_question_outputs_and_wrong_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_wrong_question_outputs(
                wrong_review(),
                output_root=root / "outputs",
                vault_root=root / "vault",
            )

            self.assertEqual(result.student_html.name, "wrong-question-review.html")
            self.assertEqual(result.parent_markdown.name, "wrong-question-review-parent.md")
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "20-错题归因" / "2026-06-19.md",
            )
            text = result.obsidian_note.read_text(encoding="utf-8")
            self.assertIn("错题归因", text)
            self.assertIn("第12题", text)
            self.assertIn("下次复测：2026-06-22", text)

    def test_wrong_question_records_append_to_matched_knowledge_note_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            note_path = (
                vault
                / "10-教材Wiki"
                / "七年级"
                / "下册"
                / "数学"
                / "第1章 1.1 直线的相交.md"
            )
            note_path.parent.mkdir(parents=True)
            note_path.write_text("# 第1章 1.1 直线的相交\n\n## 错题记录\n", encoding="utf-8")

            first = write_wrong_question_outputs(
                wrong_review(),
                output_root=root / "outputs",
                vault_root=vault,
            )
            write_wrong_question_outputs(
                wrong_review(),
                output_root=root / "outputs",
                vault_root=vault,
            )

            text = note_path.read_text(encoding="utf-8")
            self.assertEqual(first.knowledge_notes, (note_path,))
            self.assertEqual(text.count("2026-06-19 错题记录"), 1)
            self.assertIn("复测状态：待复测", text)

    def test_wrong_question_records_merge_same_note_with_different_match_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            note_path = (
                vault
                / "10-教材Wiki"
                / "七年级"
                / "下册"
                / "数学"
                / "第1章 1.1 直线的相交.md"
            )
            note_path.parent.mkdir(parents=True)
            note_path.write_text("# 第1章 1.1 直线的相交\n\n## 错题记录\n", encoding="utf-8")
            review = WrongQuestionReview(
                task_type="wrong_question_review",
                date="2026-06-19",
                items=(
                    WrongQuestionItem(
                        subject="数学",
                        question_id="第1题",
                        sticker_color="red",
                        reason="不会",
                        problem_type="证明",
                        matched_knowledge=(knowledge(),),
                        next_action="复习基础定义",
                    ),
                    WrongQuestionItem(
                        subject="数学",
                        question_id="第2题",
                        sticker_color="yellow",
                        reason="马虎",
                        problem_type="计算",
                        matched_knowledge=(
                            KnowledgeMatch(
                                grade="七年级",
                                volume="下册",
                                chapter="第1章",
                                note="第1章 1.1 直线的相交",
                                confidence="medium",
                            ),
                        ),
                        next_action="检查符号",
                    ),
                ),
                uncertain_items=(),
            )

            result = write_wrong_question_outputs(
                review,
                output_root=root / "outputs",
                vault_root=vault,
            )

            text = note_path.read_text(encoding="utf-8")
            self.assertEqual(result.knowledge_notes, (note_path,))
            self.assertEqual(text.count("2026-06-19 错题记录"), 1)
            self.assertIn("数学 第1题", text)
            self.assertIn("数学 第2题", text)


if __name__ == "__main__":
    unittest.main()
