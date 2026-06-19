import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    load_homework_plan,
    load_review_plan_source,
    load_wrong_question_review,
)


class StudyProtocolModelTests(unittest.TestCase):
    def test_sample_homework_plan_loads(self):
        plan = load_homework_plan(Path("samples/homework-plan.json"))

        self.assertEqual(plan.task_type, "homework_plan")
        self.assertEqual(plan.date, "2026-06-19")
        self.assertEqual(plan.items[0].matched_knowledge[0].confidence, "high")

    def test_sample_wrong_question_review_loads_and_normalizes_sticker(self):
        review = load_wrong_question_review(Path("samples/wrong-question-review.json"))

        self.assertEqual(review.task_type, "wrong_question_review")
        self.assertEqual(review.items[0].sticker_color, "red")
        self.assertEqual(review.items[1].sticker_color, "yellow")

    def test_sample_review_plan_source_loads(self):
        source = load_review_plan_source(Path("samples/review-plan-source.json"))

        self.assertEqual(source.task_type, "review_plan_source")
        self.assertEqual(source.items[1].sticker_color, "blue")

    def test_unknown_task_type_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps({"task_type": "unknown", "items": []}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_homework_plan(path)

    def test_invalid_date_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-date.json"
            path.write_text(
                json.dumps(
                    {
                        "task_type": "homework_plan",
                        "date": "../escaped",
                        "items": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_homework_plan(path)

    def test_unknown_sticker_color_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "task_type": "wrong_question_review",
                        "date": "2026-06-19",
                        "items": [
                            {
                                "question_id": "1",
                                "sticker_color": "green",
                                "matched_knowledge": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_wrong_question_review(path)


if __name__ == "__main__":
    unittest.main()
