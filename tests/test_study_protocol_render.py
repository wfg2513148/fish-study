import unittest
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    load_weekly_review_source,
    load_wrong_question_training,
)
from fish_study_wiki.study_protocol_render import (
    render_subject_knowledge_markdown,
    render_training_answer_html,
    render_training_student_html,
    render_weekly_answer_html,
    render_weekly_review_markdown,
    render_weekly_worksheet_html,
)


ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")


def wrong_training():
    return load_wrong_question_training(Path("samples/wrong-question-training.json"))


def weekly_source():
    return load_weekly_review_source(Path("samples/weekly-review-source.json"))


class StudyProtocolRenderTests(unittest.TestCase):
    def test_training_student_html_groups_tasks_without_answers_or_source_ids(self):
        html = render_training_student_html(wrong_training())

        self.assertIn("2026-06-19 错题分析训练卷", html)
        self.assertIn("@page { size: A4", html)
        self.assertIn("错误", html)
        self.assertIn("×", html)
        self.assertIn("补救", html)
        self.assertIn("难度：基础", html)
        self.assertIn("难度：标准", html)
        self.assertIn("自检区", html)
        self.assertIn("用一句话说明原子核", html)
        self.assertNotIn("question_id", html)
        self.assertNotIn("第8题", html)
        for marker in ANSWER_MARKERS:
            self.assertNotIn(marker, html)

    def test_training_answer_html_contains_answers_scoring_mastery_and_next_difficulty(self):
        html = render_training_answer_html(wrong_training())

        self.assertIn("错题分析训练答案", html)
        self.assertIn("答案", html)
        self.assertIn("评分点", html)
        self.assertIn("掌握判断", html)
        self.assertIn("下一次难度建议", html)
        self.assertIn("原子核在中心", html)

    def test_subject_knowledge_markdown_is_subject_scoped(self):
        text = render_subject_knowledge_markdown(wrong_training(), "数学")

        self.assertIn("# 数学 错题知识点讲解", text)
        self.assertIn("知识点与根因", text)
        self.assertIn("photo-002", text)
        self.assertIn("[[第1章 1.2 同位角、内错角、同旁内角]]", text)
        self.assertIn("审题漏条件", text)
        self.assertNotIn("photo-001", text)
        self.assertNotIn("原子结构模型", text)

    def test_weekly_review_markdown_contains_required_review_sections(self):
        text = render_weekly_review_markdown(weekly_source())

        self.assertIn("错因分布", text)
        self.assertIn("反复知识点", text)
        self.assertIn("高频二级错因", text)
        self.assertIn("难度是否合适/过难过易", text)
        self.assertIn("遗忘风险/复测队列", text)
        self.assertIn("下周优先级", text)
        self.assertIn("红色（不会）：2 组", text)
        self.assertIn("D+7", text)

    def test_weekly_worksheet_html_has_no_answers(self):
        html = render_weekly_worksheet_html(weekly_source())

        self.assertIn("周复盘训练卷", html)
        self.assertIn("复测队列", html)
        self.assertIn("本周训练题", html)
        self.assertIn("自检区", html)
        self.assertIn("画出原子结构简图", html)
        for marker in ANSWER_MARKERS:
            self.assertNotIn(marker, html)

    def test_weekly_answer_html_contains_answers(self):
        html = render_weekly_answer_html(weekly_source())

        self.assertIn("周复盘训练答案", html)
        self.assertIn("答案参考", html)
        self.assertIn("训练题答案与评分", html)
        self.assertIn("评分点", html)
        self.assertIn("掌握判断", html)
        self.assertIn("下一次难度建议", html)


if __name__ == "__main__":
    unittest.main()
