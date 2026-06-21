import unittest
from dataclasses import replace
from pathlib import Path

from fish_study_wiki.study_protocol_checks import (
    check_subject_knowledge_cards_output,
    check_weekly_review,
    check_wrong_question_training,
    forbidden_knowledge_card_matches,
)
from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    VisualMark,
    KnowledgeMatch,
    load_weekly_review_source,
    load_wrong_question_training,
)


def daily_training():
    return load_wrong_question_training(Path("samples/wrong-question-training.json"))


def weekly_source():
    return load_weekly_review_source(Path("samples/weekly-review-source.json"))


class StudyProtocolCheckTests(unittest.TestCase):
    def test_passing_daily_training_check(self):
        rows = check_wrong_question_training(
            daily_training(),
            "错题分析训练卷\n知识点补救\n自检区",
            "参考答案\n评分点\n掌握判断",
            "wrong-question-training.pdf",
            "wrong-question-training-answers.pdf",
        )

        self.assertTrue(all(row.passed for row in rows))
        self.assertEqual(
            {row.code for row in rows},
            {
                "student_no_answers",
                "answer_page_contains_answers",
                "knowledge_note_valid",
                "pending_items_are_uncertain",
                "source_photos_are_uncertain",
                "training_questions_present",
                "difficulty_mix_valid",
                "printable_path_present",
                "sticker_rules_used",
            },
        )

    def test_student_answer_leakage_fails(self):
        rows = check_wrong_question_training(
            daily_training(),
            "参考答案：A",
            "参考答案\n评分点",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "student_no_answers")
        self.assertFalse(row.passed)

    def test_missing_answer_page_answers_fails(self):
        rows = check_wrong_question_training(
            daily_training(),
            "错题分析训练卷\n自检区",
            "评分点\n掌握判断",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "answer_page_contains_answers")
        self.assertFalse(row.passed)

    def test_needs_confirmation_must_be_uncertain(self):
        training = daily_training()
        rows = check_wrong_question_training(
            replace(training, uncertain_items=()),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "pending_items_are_uncertain")
        self.assertFalse(row.passed)

    def test_pending_source_photo_must_be_uncertain(self):
        training = daily_training()
        rows = check_wrong_question_training(
            replace(
                training,
                uncertain_items=("数学 角关系计算 审题漏条件 待确认",),
            ),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "source_photos_are_uncertain")
        self.assertFalse(row.passed)

    def test_unknown_color_must_be_uncertain(self):
        training = daily_training()
        unknown = _unknown_color_cluster(training.clusters[0])
        rows = check_wrong_question_training(
            replace(training, clusters=(unknown,) + training.clusters[1:], uncertain_items=()),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "pending_items_are_uncertain")
        self.assertFalse(row.passed)

    def test_unknown_color_passes_when_isolated_with_known_colors(self):
        training = daily_training()
        unknown = _unknown_color_cluster(training.clusters[0])
        rows = check_wrong_question_training(
            replace(
                training,
                clusters=(unknown,) + training.clusters[1:],
                uncertain_items=(
                    "科学 概念识别 待确认：绿色贴纸不属于红黄蓝规则",
                    "数学 角关系计算 审题漏条件 待确认",
                    "photo-004 unclear-subject-green-mark.jpg 学科待确认",
                ),
            ),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        self.assertTrue(all(row.passed for row in rows))

    def test_broad_uncertain_item_does_not_confirm_pending_cluster(self):
        training = daily_training()
        rows = check_wrong_question_training(
            replace(training, uncertain_items=("数学",)),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "pending_items_are_uncertain")
        self.assertFalse(row.passed)

    def test_empty_knowledge_note_fails(self):
        training = daily_training()
        cluster = _replace_knowledge(training.clusters[0], note="")
        rows = check_wrong_question_training(
            replace(training, clusters=(cluster,) + training.clusters[1:]),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "knowledge_note_valid")
        self.assertFalse(row.passed)

    def test_empty_training_questions_fail(self):
        training = daily_training()
        cluster = replace(training.clusters[0], training_questions=())
        rows = check_wrong_question_training(
            replace(training, clusters=(cluster,) + training.clusters[1:]),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "training_questions_present")
        self.assertFalse(row.passed)

    def test_challenge_only_difficulty_fails(self):
        training = daily_training()
        cluster = replace(training.clusters[0], difficulty_mix=("challenge",))
        rows = check_wrong_question_training(
            replace(training, clusters=(cluster,) + training.clusters[1:]),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "difficulty_mix_valid")
        self.assertFalse(row.passed)

    def test_challenge_requires_foundation_difficulty_fails(self):
        training = daily_training()
        cluster = replace(training.clusters[0], difficulty_mix=("standard", "challenge"))
        rows = check_wrong_question_training(
            replace(training, clusters=(cluster,) + training.clusters[1:]),
            "错题分析训练卷",
            "参考答案",
            "wrong.pdf",
            "answers.pdf",
        )

        row = next(row for row in rows if row.code == "difficulty_mix_valid")
        self.assertFalse(row.passed)

    def test_challenge_question_must_be_declared_in_difficulty_mix(self):
        training = daily_training()
        question = replace(training.clusters[0].training_questions[0], difficulty="challenge")
        cluster = replace(
            training.clusters[0],
            training_questions=(question,) + training.clusters[0].training_questions[1:],
            difficulty_mix=("basic", "standard"),
        )
        rows = check_wrong_question_training(
            replace(training, clusters=(cluster,) + training.clusters[1:]),
            "错题分析训练卷",
            "参考答案",
            "wrong.html",
            "answers.html",
        )

        row = next(row for row in rows if row.code == "difficulty_mix_valid")
        self.assertFalse(row.passed)

    def test_passing_weekly_review_check(self):
        rows = check_weekly_review(
            weekly_source(),
            "周巩固测试卷\n自检区",
            "参考答案\n评分点",
            "weekly-review.md",
            "weekly-review.pdf",
            "weekly-review-answers.pdf",
        )

        self.assertTrue(all(row.passed for row in rows))

    def test_weekly_review_requires_training_questions(self):
        source = weekly_source()
        event = replace(source.events[0], training_questions=())
        rows = check_weekly_review(
            replace(source, events=(event,) + source.events[1:]),
            "周巩固测试卷\n自检区",
            "参考答案\n评分点",
            "weekly-review.md",
            "weekly-review.pdf",
            "weekly-review-answers.pdf",
        )

        row = next(row for row in rows if row.code == "training_questions_present")
        self.assertFalse(row.passed)

    def test_knowledge_card_output_passes_when_student_facing(self):
        rows = check_subject_knowledge_cards_output(
            "# 数学 知识点复习卡\n\n## 1. 平行线的性质与判定\n",
            '<h1>数学 知识点复习卡</h1><img src="file:///tmp/a.png" data-generator="gpt-image-2"><p>同位角相等</p>',
        )

        self.assertTrue(all(row.passed for row in rows))

    def test_knowledge_card_output_rejects_source_and_diagnosis_noise(self):
        noisy_text = "# 科学 知识点复习卡\nphoto-001 第1题 错因 红色 训练建议"
        noisy_html = '<h1>科学 知识点复习卡</h1><img src="file:///tmp/a.png" data-generator="gpt-image-2"><p>照片 依据 诊断</p>'

        rows = check_subject_knowledge_cards_output(noisy_text, noisy_html)

        self.assertFalse(
            next(
                row
                for row in rows
                if row.code == "knowledge_card_no_forbidden_text_markdown"
            ).passed
        )
        self.assertFalse(
            next(
                row
                for row in rows
                if row.code == "knowledge_card_no_forbidden_text_html"
            ).passed
        )
        self.assertIn("photo-", forbidden_knowledge_card_matches(noisy_text))
        self.assertIn("照片", forbidden_knowledge_card_matches(noisy_html))

    def test_knowledge_card_output_rejects_chapter_labels_in_image_metadata(self):
        rows = check_subject_knowledge_cards_output(
            "# 科学 知识点复习卡\n\n## 1. 第1章 第3节 第2课时 种子的结构与萌发\n",
            '<h1>科学 知识点复习卡</h1><figure><img src="file:///tmp/a.png" alt="第1章 第3节 第2课时 种子的结构与萌发" data-generator="gpt-image-2"><figcaption>第1章 第3节 第2课时 种子的结构与萌发</figcaption></figure>',
        )

        row = next(
            row for row in rows if row.code == "knowledge_card_image_labels_are_concept_only"
        )
        self.assertFalse(row.passed)


def _replace_knowledge(cluster: AnalysisCluster, note: str) -> AnalysisCluster:
    match = cluster.matched_knowledge[0]
    return replace(
        cluster,
        matched_knowledge=(
            KnowledgeMatch(
                grade=match.grade,
                volume=match.volume,
                chapter=match.chapter,
                note=note,
                confidence=match.confidence,
            ),
        ),
    )


def _unknown_color_cluster(cluster: AnalysisCluster) -> AnalysisCluster:
    diagnosis = replace(
        cluster.diagnosis,
        sticker_color="unknown",
        primary_reason="待确认",
        secondary_reason="待确认",
        confidence="low",
        confirmation_status="needs_confirmation",
        visual_mark=VisualMark(
            color_detected="绿色贴纸",
            color_normalized="unknown",
            mark_type="sticker",
            evidence="绿色不属于红黄蓝自动归因规则。",
            confidence="low",
        ),
    )
    return replace(cluster, diagnosis=diagnosis)


if __name__ == "__main__":
    unittest.main()
