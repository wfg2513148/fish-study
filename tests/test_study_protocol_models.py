import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    load_weekly_review_source,
    load_wrong_question_training,
)


class StudyProtocolModelTests(unittest.TestCase):
    def test_sample_wrong_question_training_loads(self):
        training = load_wrong_question_training(
            Path("samples/wrong-question-training.json")
        )

        self.assertEqual(training.task_type, "wrong_question_training")
        self.assertEqual(training.date, "2026-06-19")
        self.assertEqual(training.clusters[0].diagnosis.sticker_color, "red")
        self.assertEqual(
            training.clusters[0].diagnosis.visual_mark.color_normalized,
            "red",
        )
        self.assertEqual(training.clusters[1].diagnosis.visual_mark.mark_type, "circle")
        self.assertEqual(training.clusters[1].diagnosis.sticker_color, "yellow")
        self.assertEqual(training.clusters[2].diagnosis.sticker_color, "blue")
        self.assertEqual(training.clusters[0].training_questions[0].difficulty, "basic")
        self.assertEqual(training.clusters[1].difficulty_mix, ("standard", "variant"))

    def test_sample_weekly_review_source_loads(self):
        source = load_weekly_review_source(Path("samples/weekly-review-source.json"))

        self.assertEqual(source.task_type, "weekly_review")
        self.assertEqual(source.week_start, "2026-06-12")
        self.assertEqual(source.week_end, "2026-06-21")
        self.assertEqual(len(source.events), 4)
        self.assertEqual(source.results[0].difficulty, "basic")
        self.assertEqual(source.results[0].completion_status, "overtime")
        self.assertEqual(source.results[1].next_difficulty, "variant")
        self.assertEqual(source.review_queue[0].status, "D+7 review")

    def test_invalid_task_type_fails(self):
        data = _sample_training()
        data["task_type"] = "unsupported_plan"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_invalid_date_fails(self):
        data = _sample_training()
        data["date"] = "../escaped"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_invalid_difficulty_fails(self):
        data = _sample_training()
        data["clusters"][0]["training_questions"][0]["difficulty"] = "expert"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_invalid_confirmation_status_fails(self):
        data = _sample_training()
        data["clusters"][0]["diagnosis"]["confirmation_status"] = "maybe"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_medium_confidence_auto_confirmation_fails(self):
        data = _sample_training()
        data["clusters"][0]["diagnosis"]["confidence"] = "medium"
        data["clusters"][0]["diagnosis"]["confirmation_status"] = "auto"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_secondary_reason_must_match_sticker_color(self):
        data = _sample_training()
        data["clusters"][0]["diagnosis"]["secondary_reason"] = "计算错误"

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_visual_mark_color_must_match_diagnosis_color(self):
        data = _sample_training()
        data["clusters"][0]["diagnosis"]["visual_mark"] = {
            "color_detected": "黄色贴纸",
            "color_normalized": "yellow",
            "mark_type": "sticker",
            "evidence": "题号旁看似黄色。",
            "confidence": "high",
        }

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_unknown_visual_color_requires_pending_confirmation(self):
        data = _sample_training()
        diagnosis = data["clusters"][0]["diagnosis"]
        diagnosis["sticker_color"] = "unknown"
        diagnosis["primary_reason"] = "待确认"
        diagnosis["secondary_reason"] = "待确认"
        diagnosis["confidence"] = "low"
        diagnosis["confirmation_status"] = "needs_confirmation"
        diagnosis["visual_mark"] = {
            "color_detected": "绿色贴纸",
            "color_normalized": "unknown",
            "mark_type": "sticker",
            "evidence": "绿色不属于红黄蓝自动归因规则。",
            "confidence": "low",
        }

        training = load_wrong_question_training(_write_json(data))

        self.assertEqual(training.clusters[0].diagnosis.sticker_color, "unknown")

    def test_unknown_visual_color_cannot_be_confirmed(self):
        data = _sample_training()
        diagnosis = data["clusters"][0]["diagnosis"]
        diagnosis["sticker_color"] = "unknown"
        diagnosis["primary_reason"] = "待确认"
        diagnosis["secondary_reason"] = "待确认"
        diagnosis["confidence"] = "medium"
        diagnosis["confirmation_status"] = "confirmed"
        diagnosis["visual_mark"] = {
            "color_detected": "绿色贴纸",
            "color_normalized": "unknown",
            "mark_type": "sticker",
            "evidence": "绿色不属于红黄蓝自动归因规则。",
            "confidence": "medium",
        }

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_nested_non_object_fails_with_value_error(self):
        data = _sample_training()
        data["clusters"][0]["diagnosis"] = None

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_nested_non_list_fails_with_value_error(self):
        data = _sample_training()
        data["clusters"] = None

        with self.assertRaises(ValueError):
            load_wrong_question_training(_write_json(data))

    def test_invalid_week_range_fails(self):
        data = _sample_weekly()
        data["week_start"] = "2026-06-20"
        data["week_end"] = "2026-06-19"

        with self.assertRaises(ValueError):
            load_weekly_review_source(_write_json(data))

    def test_invalid_correct_rate_fails(self):
        data = _sample_weekly()
        data["results"][0]["correct_rate"] = 1.5

        with self.assertRaises(ValueError):
            load_weekly_review_source(_write_json(data))

    def test_negative_elapsed_minutes_fails(self):
        data = _sample_weekly()
        data["results"][0]["elapsed_minutes"] = -1

        with self.assertRaises(ValueError):
            load_weekly_review_source(_write_json(data))

    def test_null_correct_rate_fails_with_value_error(self):
        data = _sample_weekly()
        data["results"][0]["correct_rate"] = None

        with self.assertRaises(ValueError):
            load_weekly_review_source(_write_json(data))

    def test_null_elapsed_minutes_fails_with_value_error(self):
        data = _sample_weekly()
        data["results"][0]["elapsed_minutes"] = None

        with self.assertRaises(ValueError):
            load_weekly_review_source(_write_json(data))


def _sample_training():
    return {
        "task_type": "wrong_question_training",
        "date": "2026-06-19",
        "source_batch": "unit-test",
        "clusters": [
            {
                "subject": "数学",
                "problem_type": "计算",
                "diagnosis": {
                    "sticker_color": "red",
                    "primary_reason": "不会",
                    "secondary_reason": "概念不清",
                    "evidence": "不会使用平行线性质。",
                    "confidence": "high",
                    "confirmation_status": "confirmed",
                },
                "matched_knowledge": [
                    {
                        "grade": "七年级",
                        "volume": "下册",
                        "chapter": "第1章",
                        "note": "第1章 1.3 平行线的性质与判定",
                        "confidence": "high",
                    }
                ],
                "training_questions": [
                    {
                        "prompt": "写出平行线的一个性质。",
                        "difficulty": "basic",
                        "target_reason": "概念不清",
                        "answer": "两直线平行，同位角相等。",
                        "scoring_points": ["写出平行线条件", "写出角关系"],
                        "mastery_signal": "能独立说出性质。",
                    }
                ],
                "difficulty_mix": ["basic", "standard"],
            }
        ],
        "uncertain_items": [],
    }


def _sample_weekly():
    return json.loads(Path("samples/weekly-review-source.json").read_text(encoding="utf-8"))


def _write_json(data):
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    _TEMP_DIRS.append(temp_dir)
    return path


_TEMP_DIRS = []


if __name__ == "__main__":
    unittest.main()
