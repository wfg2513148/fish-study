import unittest
from dataclasses import replace

from fish_study_wiki.study_protocol_checks import (
    check_homework_plan,
    check_review_plan_source,
    check_wrong_question_review,
)
from fish_study_wiki.study_protocol_models import (
    HomeworkItem,
    HomeworkPlan,
    KnowledgeMatch,
    ReviewPlanSource,
    WrongQuestionItem,
    WrongQuestionReview,
)


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
                raw_text="完成第1题",
                book_or_source="作业本",
                page="12",
                question_range="1",
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
                subject="数学",
                question_id="第3题",
                sticker_color="red",
                reason="不会",
                problem_type="概念识别",
                matched_knowledge=(knowledge(),),
                next_action="先补知识点，再做基础变式",
            ),
        ),
        uncertain_items=(),
    )


class StudyProtocolCheckTests(unittest.TestCase):
    def test_passing_homework_checks(self):
        rows = check_homework_plan(homework_plan(), "知识点预习\n练习区", "out.html")

        self.assertTrue(all(row.passed for row in rows))
        self.assertEqual(
            {row.code for row in rows},
            {
                "student_no_answers",
                "knowledge_note_valid",
                "knowledge_link_or_pending",
                "low_confidence_flagged",
                "printable_path_present",
            },
        )

    def test_missing_knowledge_fails_without_pending(self):
        plan = homework_plan()
        item = replace(plan.items[0], matched_knowledge=())
        rows = check_homework_plan(replace(plan, items=(item,)), "练习区", "out.html")

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertFalse(row.passed)

    def test_multi_item_empty_unmarked_item_fails_knowledge_check(self):
        plan = homework_plan()
        empty_item = replace(
            plan.items[0],
            raw_text="完成第2题",
            matched_knowledge=(),
        )
        rows = check_homework_plan(
            replace(plan, items=(plan.items[0], empty_item)),
            "练习区",
            "out.html",
        )

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertFalse(row.passed)

    def test_pending_knowledge_must_be_in_uncertain_items(self):
        plan = homework_plan()
        item = replace(plan.items[0], matched_knowledge=(knowledge(note="待定位"),))
        rows = check_homework_plan(replace(plan, items=(item,)), "练习区", "out.html")

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertFalse(row.passed)

    def test_pending_knowledge_passes_when_explicitly_uncertain(self):
        plan = homework_plan()
        item = replace(plan.items[0], matched_knowledge=(knowledge(note="待定位"),))
        rows = check_homework_plan(
            replace(plan, items=(item,), uncertain_items=("完成第1题 待定位",)),
            "练习区",
            "out.html",
        )

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertTrue(row.passed)

    def test_empty_knowledge_note_fails(self):
        plan = homework_plan()
        item = replace(plan.items[0], matched_knowledge=(knowledge(note=""),))
        rows = check_homework_plan(
            replace(plan, items=(item,), uncertain_items=("完成第1题 待确认",)),
            "练习区",
            "out.html",
        )

        row = next(row for row in rows if row.code == "knowledge_note_valid")
        self.assertFalse(row.passed)

    def test_empty_knowledge_note_fails_even_with_real_match(self):
        plan = homework_plan()
        item = replace(
            plan.items[0],
            matched_knowledge=(knowledge(), knowledge(note="")),
        )
        rows = check_homework_plan(replace(plan, items=(item,)), "练习区", "out.html")

        row = next(row for row in rows if row.code == "knowledge_note_valid")
        self.assertFalse(row.passed)

    def test_low_confidence_must_be_flagged(self):
        plan = homework_plan()
        item = replace(plan.items[0], matched_knowledge=(knowledge("low"),))
        rows = check_homework_plan(replace(plan, items=(item,)), "练习区", "out.html")

        row = next(row for row in rows if row.code == "low_confidence_flagged")
        self.assertFalse(row.passed)

    def test_unrelated_uncertain_item_does_not_flag_low_confidence(self):
        plan = homework_plan()
        item = replace(
            plan.items[0],
            raw_text="完成第2题",
            matched_knowledge=(knowledge("low", "第1章 1.2 同位角"),),
        )
        rows = check_homework_plan(
            replace(plan, items=(item,), uncertain_items=("第99题 待确认",)),
            "练习区",
            "out.html",
        )

        row = next(row for row in rows if row.code == "low_confidence_flagged")
        self.assertFalse(row.passed)

    def test_answer_leakage_fails(self):
        rows = check_homework_plan(homework_plan(), "参考答案：A", "out.html")

        row = next(row for row in rows if row.code == "student_no_answers")
        self.assertFalse(row.passed)

    def test_wrong_question_sticker_rules_used(self):
        rows = check_wrong_question_review(wrong_review(), "错题复盘练习", "wrong.html")

        row = next(row for row in rows if row.code == "sticker_rules_used")
        self.assertTrue(row.passed)

    def test_wrong_question_pending_knowledge_must_be_uncertain(self):
        review = wrong_review()
        item = replace(review.items[0], matched_knowledge=(knowledge(note="待定位"),))
        rows = check_wrong_question_review(
            replace(review, items=(item,)), "错题复盘练习", "wrong.html"
        )

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertFalse(row.passed)

    def test_review_plan_pending_knowledge_must_be_uncertain(self):
        review = wrong_review()
        item = replace(review.items[0], matched_knowledge=(knowledge(note="待定位"),))
        source = ReviewPlanSource(
            task_type="review_plan_source",
            date=review.date,
            items=(item,),
            uncertain_items=(),
        )
        rows = check_review_plan_source(source)

        row = next(row for row in rows if row.code == "knowledge_link_or_pending")
        self.assertFalse(row.passed)

    def test_unknown_sticker_color_fails_check(self):
        review = wrong_review()
        item = replace(review.items[0], sticker_color="green")
        rows = check_wrong_question_review(
            replace(review, items=(item,)), "错题复盘练习", "wrong.html"
        )

        row = next(row for row in rows if row.code == "sticker_rules_used")
        self.assertFalse(row.passed)


if __name__ == "__main__":
    unittest.main()
