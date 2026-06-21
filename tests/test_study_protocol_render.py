import unittest
from dataclasses import replace
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    KnowledgeMatch,
    load_weekly_review_source,
    load_wrong_question_training,
)
from fish_study_wiki.study_protocol_checks import forbidden_knowledge_card_matches
from fish_study_wiki.study_protocol_render import (
    knowledge_card_display_title,
    render_subject_knowledge_cards_html,
    render_subject_knowledge_cards_markdown,
    render_subject_knowledge_html,
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


def diagram_assets(training=None, subject="数学"):
    training = training or wrong_training()
    return {
        match.note: f"/tmp/{index}-{subject}-knowledge.png"
        for index, cluster in enumerate(
            (item for item in training.clusters if item.subject == subject),
            start=1,
        )
        for match in cluster.matched_knowledge
    }


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

    def test_training_student_html_keeps_sixty_percent_choice_questions(self):
        training = wrong_training()
        total_questions = sum(
            len(cluster.training_questions) for cluster in training.clusters
        )
        expected_choice_count = round(total_questions * 0.6)
        html = render_training_student_html(training)

        self.assertEqual(html.count('class="options"'), expected_choice_count)
        self.assertEqual(html.count('class="answer-box"'), total_questions - expected_choice_count)
        self.assertIn("选择题", html)
        self.assertIn("非选择题", html)

    def test_science_training_html_uses_illustrated_question_figures(self):
        training = wrong_training()
        html = render_training_student_html(training)
        science_cluster_count = sum(
            1 for cluster in training.clusters if cluster.subject == "科学"
        )

        self.assertGreater(science_cluster_count, 0)
        self.assertEqual(html.count('class="question-figure"'), science_cluster_count)
        self.assertIn("<svg", html)
        self.assertIn("科学图示", html)

    def test_training_answer_html_contains_answers_scoring_mastery_and_next_difficulty(self):
        html = render_training_answer_html(wrong_training())

        self.assertIn("错题分析训练答案", html)
        self.assertIn("答案", html)
        self.assertIn("评分点", html)
        self.assertIn("掌握判断", html)
        self.assertIn("下一次难度建议", html)
        self.assertIn("原子核在中心", html)

    def test_training_answer_html_marks_choice_question_keys(self):
        html = render_training_answer_html(wrong_training())

        self.assertIn("选择题答案", html)
        self.assertIn("正确选项", html)

    def test_subject_knowledge_markdown_is_subject_scoped(self):
        text = render_subject_knowledge_markdown(wrong_training(), "数学")

        self.assertIn("# 数学 错题知识点讲解", text)
        self.assertIn("知识点与根因", text)
        self.assertIn("photo-002", text)
        self.assertIn("[[第1章 1.2 同位角、内错角、同旁内角]]", text)
        self.assertIn("审题漏条件", text)
        self.assertNotIn("photo-001", text)
        self.assertNotIn("原子结构模型", text)

    def test_subject_knowledge_html_contains_illustrated_sections(self):
        html = render_subject_knowledge_html(wrong_training(), "数学")

        self.assertIn("数学 错题知识点讲解", html)
        self.assertIn("图示讲解", html)
        self.assertIn("knowledge-card", html)
        self.assertIn("<svg", html)
        self.assertIn("知识点与根因", html)
        self.assertNotIn("photo-001", html)

    def test_subject_knowledge_cards_are_student_facing_without_diagnosis_noise(self):
        training = wrong_training()
        assets = diagram_assets(training)
        text = render_subject_knowledge_cards_markdown(training, "数学", assets)
        html = render_subject_knowledge_cards_html(training, "数学", assets)

        self.assertIn("# 数学 知识点复习卡", text)
        self.assertIn("数学 知识点复习卡", html)
        self.assertIn("同位角、内错角、同旁内角", text)
        self.assertIn("平行线的性质与判定", text)
        self.assertIn("必须记住", text)
        self.assertIn("复习重点", text)
        self.assertIn("易混点", text)
        self.assertIn("自检问题", text)
        self.assertIn("<img", html)
        self.assertIn('data-generator="gpt-image-2"', html)
        self.assertNotIn("<svg", html)
        self.assertEqual(forbidden_knowledge_card_matches(text), ())
        self.assertEqual(forbidden_knowledge_card_matches(html), ())
        self.assertNotIn("审题漏条件", text)
        self.assertNotIn("审题漏条件", html)
        self.assertNotIn("。；", text)
        self.assertNotIn("。；", html)

    def test_knowledge_card_image_labels_use_concept_titles(self):
        training = wrong_training()
        science_cluster = next(
            cluster for cluster in training.clusters if cluster.subject == "科学"
        )
        match = KnowledgeMatch(
            grade="七年级",
            volume="上册",
            chapter="第1章",
            note="第1章 第3节 第2课时 种子的结构与萌发",
            confidence="high",
        )
        training = replace(
            training,
            clusters=(replace(science_cluster, matched_knowledge=(match,)),),
        )
        assets = {match.note: "/tmp/seed-card.png"}

        text = render_subject_knowledge_cards_markdown(training, "科学", assets)
        html = render_subject_knowledge_cards_html(training, "科学", assets)

        self.assertEqual(
            knowledge_card_display_title(match.note),
            "种子的结构与萌发",
        )
        self.assertIn("![种子的结构与萌发](/tmp/seed-card.png)", text)
        self.assertNotIn("![第1章", text)
        self.assertIn('alt="种子的结构与萌发"', html)
        self.assertIn("<figcaption>种子的结构与萌发</figcaption>", html)
        self.assertNotIn('alt="第1章', html)

    def test_subject_knowledge_cards_dedupe_filter_and_sort_by_learning_order(self):
        training = wrong_training()
        math_clusters = [
            cluster for cluster in training.clusters if cluster.subject == "数学"
        ]
        reversed_training = replace(
            training,
            clusters=tuple(reversed(math_clusters))
            + (
                replace(
                    math_clusters[0],
                    matched_knowledge=(
                        math_clusters[0].matched_knowledge[0],
                        KnowledgeMatch(
                            grade="七年级",
                            volume="下册",
                            chapter="第9章",
                            note="待定位",
                            confidence="high",
                        ),
                        KnowledgeMatch(
                            grade="七年级",
                            volume="下册",
                            chapter="第1章",
                            note="低置信示例知识点",
                            confidence="low",
                        ),
                        KnowledgeMatch(
                            grade="七年级",
                            volume="下册",
                            chapter="综合专题",
                            note="无法定位章节的知识点",
                            confidence="high",
                        ),
                        KnowledgeMatch(
                            grade="七年级",
                            volume="下册",
                            chapter="第二章",
                            note="第二章 物质密度",
                            confidence="high",
                        ),
                        KnowledgeMatch(
                            grade="七年级",
                            volume="下册",
                            chapter="第十章",
                            note="第十章 熔点与凝固点",
                            confidence="high",
                        ),
                    ),
                ),
            ),
        )

        assets = {
            match.note: f"/tmp/card-{index}.png"
            for index, cluster in enumerate(reversed_training.clusters, start=1)
            for match in cluster.matched_knowledge
        }
        text = render_subject_knowledge_cards_markdown(reversed_training, "数学", assets)

        self.assertEqual(text.count("## 同位角、内错角、同旁内角"), 1)
        self.assertLess(text.index("同位角、内错角、同旁内角"), text.index("平行线的性质与判定"))
        self.assertLess(text.index("物质密度"), text.index("熔点与凝固点"))
        self.assertNotIn("待定位", text)
        self.assertNotIn("低置信示例知识点", text)
        self.assertNotIn("无法定位章节的知识点", text)

    def test_subject_knowledge_cards_use_specific_science_bodies(self):
        training = wrong_training()
        science_cluster = next(
            cluster for cluster in training.clusters if cluster.subject == "科学"
        )
        matches = (
            KnowledgeMatch(
                grade="七年级",
                volume="上册",
                chapter="第1章",
                note="第1章 第3节 第2课时 种子的结构与萌发",
                confidence="high",
            ),
            KnowledgeMatch(
                grade="七年级",
                volume="上册",
                chapter="第1章",
                note="第1章 第4节 第1课时 细菌与真菌",
                confidence="high",
            ),
            KnowledgeMatch(
                grade="七年级",
                volume="下册",
                chapter="第2章",
                note="第2章 专题11 分子、原子、离子、元素与物质之间的关系",
                confidence="high",
            ),
            KnowledgeMatch(
                grade="七年级",
                volume="下册",
                chapter="第3章",
                note="第3章 第3节 第1课时 物质的变化与性质",
                confidence="high",
            ),
            KnowledgeMatch(
                grade="七年级",
                volume="下册",
                chapter="第3章",
                note="第3章 第3节 第2课时 温度对物质性质的影响、探索物质变化和性质的方法",
                confidence="high",
            ),
        )
        specific_training = replace(
            training,
            clusters=(replace(science_cluster, matched_knowledge=matches),),
        )
        assets = {match.note: f"/tmp/science-card-{index}.png" for index, match in enumerate(matches)}

        text = render_subject_knowledge_cards_markdown(specific_training, "科学", assets)

        self.assertIn("胚根先发育成根", text)
        self.assertIn("没有成形细胞核", text)
        self.assertIn("元素描述同一类原子的总称", text)
        self.assertIn("物理变化不生成新物质", text)
        self.assertIn("控制变量", text)
        self.assertNotIn("先理解概念的定义、条件和适用范围", text)

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
