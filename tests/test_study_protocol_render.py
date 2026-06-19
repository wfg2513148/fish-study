import unittest

from fish_study_wiki.study_protocol_models import (
    HomeworkItem,
    HomeworkPlan,
    KnowledgeMatch,
    ReviewPlanSource,
    WrongQuestionItem,
    WrongQuestionReview,
)
from fish_study_wiki.study_protocol_render import (
    render_homework_parent_markdown,
    render_homework_student_html,
    render_review_plan_markdown,
    render_wrong_question_parent_markdown,
    render_wrong_question_student_html,
)


ANSWER_MARKERS = ("答案", "解析", "参考答案")


def knowledge(confidence: str = "high", note: str = "第1章 1.1 直线的相交"):
    return KnowledgeMatch(
        grade="七年级",
        volume="下册",
        chapter="第1章",
        note=note,
        confidence=confidence,
    )


def homework_plan() -> HomeworkPlan:
    return HomeworkPlan(
        task_type="homework_plan",
        date="2026-06-19",
        items=(
            HomeworkItem(
                subject="数学",
                raw_text="完成第1-3题",
                book_or_source="作业本",
                page="12",
                question_range="1-3",
                deadline="今晚",
                matched_knowledge=(knowledge(),),
                status="matched",
            ),
        ),
        uncertain_items=(),
    )


def wrong_review() -> WrongQuestionReview:
    return WrongQuestionReview(
        task_type="wrong_question_review",
        date="2026-06-19",
        items=(
            WrongQuestionItem(
                subject="科学",
                question_id="第8题",
                sticker_color="red",
                reason="不会",
                problem_type="概念识别",
                matched_knowledge=(
                    knowledge("medium", "第2章 第3节 第1课时 原子结构模型与原子的构成"),
                ),
                next_action="补概念并做基础变式",
            ),
        ),
        uncertain_items=(),
    )


class StudyProtocolRenderTests(unittest.TestCase):
    def test_homework_student_html_has_required_print_sections_without_answers(self):
        html = render_homework_student_html(homework_plan())

        self.assertIn("@page { size: A4", html)
        self.assertIn("知识点预习", html)
        self.assertIn("热身区", html)
        self.assertIn("正式任务清单", html)
        self.assertIn("自我检查区", html)
        for marker in ANSWER_MARKERS:
            self.assertNotIn(marker, html)

    def test_wrong_question_student_html_uses_color_strategy_without_answers(self):
        html = render_wrong_question_student_html(wrong_review())

        self.assertIn("知识点回顾", html)
        self.assertIn("贴纸策略", html)
        self.assertIn("同类变式题", html)
        self.assertIn("红色", html)
        self.assertIn("先补知识点", html)
        for marker in ANSWER_MARKERS:
            self.assertNotIn(marker, html)

    def test_parent_markdown_is_separate_and_can_include_reference_notes(self):
        text = render_homework_parent_markdown(homework_plan())

        self.assertIn("家长参考", text)
        self.assertIn("预计用时", text)
        self.assertIn("检查顺序", text)
        self.assertIn("答案/参考说明", text)

    def test_wrong_parent_markdown_includes_low_confidence_warning(self):
        review = WrongQuestionReview(
            task_type="wrong_question_review",
            date="2026-06-19",
            items=(
                WrongQuestionItem(
                    subject="数学",
                    question_id="第12题",
                    sticker_color="yellow",
                    reason="马虎",
                    problem_type="计算",
                    matched_knowledge=(knowledge("low", "第1章 1.2 同位角"),),
                    next_action="整理检查清单",
                ),
            ),
            uncertain_items=("第12题 知识点需家长确认",),
        )

        text = render_wrong_question_parent_markdown(review)

        self.assertIn("低置信度提醒", text)
        self.assertIn("第1章 1.2 同位角", text)
        self.assertIn("第12题 知识点需家长确认", text)

    def test_review_plan_markdown_uses_red_yellow_blue_counts(self):
        source = ReviewPlanSource(
            task_type="review_plan_source",
            date="2026-06-19",
            items=(
                wrong_review().items[0],
                WrongQuestionItem(
                    subject="数学",
                    question_id="第12题",
                    sticker_color="blue",
                    reason="时间不够",
                    problem_type="计算",
                    matched_knowledge=(knowledge("high", "第1章 1.2 同位角"),),
                    next_action="做限时训练",
                ),
            ),
            uncertain_items=(),
        )

        text = render_review_plan_markdown(source)

        self.assertIn("红色：1 题", text)
        self.assertIn("黄色：0 题", text)
        self.assertIn("蓝色：1 题", text)
        self.assertIn("未来 3 天安排", text)


if __name__ == "__main__":
    unittest.main()
