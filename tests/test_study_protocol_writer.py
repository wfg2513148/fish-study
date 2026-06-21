import tempfile
import unittest
import unicodedata
from unittest.mock import patch
from pathlib import Path

from pypdf import PdfReader

from fish_study_wiki import settings
from fish_study_wiki.study_protocol_models import (
    load_weekly_review_source,
    load_wrong_question_training,
)
from fish_study_wiki.study_protocol_checks import forbidden_knowledge_card_matches
from fish_study_wiki.study_protocol_writer import (
    DEFAULT_VAULT_ROOT,
    write_training_outputs,
    write_weekly_review_outputs,
)


ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00"
    b"\x1b\xb6\xeeV\x00\x00\x00\x00IEND\xaeB`\x82"
)


def training_sample():
    return load_wrong_question_training(Path("samples/wrong-question-training.json"))


def weekly_sample():
    return load_weekly_review_source(Path("samples/weekly-review-source.json"))


class StudyProtocolWriterTests(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "fish_study_wiki.study_protocol_writer.prepare_knowledge_card_diagrams",
            side_effect=_fake_knowledge_card_diagrams,
        )
        self.addCleanup(patcher.stop)
        patcher.start()

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

            self.assertEqual(result.student_pdf.name, "wrong-question-training.pdf")
            self.assertEqual(result.answer_pdf.name, "wrong-question-training-answers.pdf")
            self.assertEqual(result.student_pdf.parent.name, "2026-06-19")
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "20-错题归因" / "2026-06-19.md",
            )
            self.assertTrue(result.student_pdf.exists())
            self.assertTrue(result.answer_pdf.exists())
            self.assertIn("错题分析训练卷", _pdf_text(result.student_pdf))
            self.assertIn("错题分析训练答案", _pdf_text(result.answer_pdf))
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
                    output.student_pdf,
                    output.answer_pdf,
                    output.knowledge_markdown,
                    output.knowledge_pdf,
                )
            }
            self.assertEqual(
                subject_files,
                {
                    "science-training.pdf",
                    "science-training-answers.pdf",
                    "science-knowledge.md",
                    "science-knowledge.pdf",
                    "math-training.pdf",
                    "math-training-answers.pdf",
                    "math-knowledge.md",
                    "math-knowledge.pdf",
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

            student_text = _pdf_text(result.student_pdf)
            answer_text = _pdf_text(result.answer_pdf)
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
            math_text = _pdf_text(by_subject["数学"].student_pdf)
            science_text = _pdf_text(by_subject["科学"].student_pdf)
            math_knowledge = by_subject["数学"].knowledge_markdown.read_text(
                encoding="utf-8"
            )
            math_knowledge_pdf = _pdf_text(by_subject["数学"].knowledge_pdf)
            self.assertIn("限时计算", math_text)
            self.assertNotIn("概念识别", math_text)
            self.assertIn("概念识别", science_text)
            self.assertNotIn("限时计算", science_text)
            self.assertIn("数学 知识点复习卡", math_knowledge)
            self.assertIn("同位角、内错角、同旁内角", math_knowledge)
            self.assertIn("必须记住", math_knowledge)
            self.assertIn("易混点", math_knowledge)
            self.assertIn("数学 知识点复习卡", math_knowledge_pdf)
            self.assertIn("平行线的性质与判定", math_knowledge_pdf)
            self.assertEqual(forbidden_knowledge_card_matches(math_knowledge), ())
            self.assertEqual(forbidden_knowledge_card_matches(math_knowledge_pdf), ())
            self.assertGreaterEqual(
                _pdf_image_object_count(by_subject["数学"].knowledge_pdf),
                2,
            )
            self.assertGreaterEqual(
                _pdf_image_object_count(by_subject["科学"].knowledge_pdf),
                1,
            )

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
            self.assertEqual(result.student_pdf.name, "weekly-review.pdf")
            self.assertEqual(result.answer_pdf.name, "weekly-review-answers.pdf")
            self.assertEqual(result.report_markdown.parent.name, "2026-06-21")
            self.assertEqual(
                result.obsidian_note,
                root / "vault" / "40-复习计划" / "2026-06-21.md",
            )
            self.assertIn("难度是否合适", result.report_markdown.read_text(encoding="utf-8"))
            self.assertIn("错题周复盘", result.obsidian_note.read_text(encoding="utf-8"))
            self.assertIn("周复盘训练卷", _pdf_text(result.student_pdf))
            for marker in ANSWER_MARKERS:
                self.assertNotIn(marker, _pdf_text(result.student_pdf))
            self.assertIn("答案", _pdf_text(result.answer_pdf))


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return unicodedata.normalize("NFKC", text)


def _pdf_image_object_count(path: Path) -> int:
    reader = PdfReader(str(path))
    count = 0
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        xobjects = resources.get("/XObject") or {}
        if hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()
        for value in xobjects.values():
            obj = value.get_object() if hasattr(value, "get_object") else value
            if obj.get("/Subtype") == "/Image":
                count += 1
    return count


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
