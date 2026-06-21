from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def image_object_count(reader: PdfReader) -> int:
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


class ExamPaperTemplateTests(unittest.TestCase):
    def test_templates_keep_sixty_percent_choice_questions(self) -> None:
        for template in [
            ROOT / "templates" / "exam-paper" / "math-grade7.html",
            ROOT / "templates" / "exam-paper" / "science-grade7.html",
            ROOT / "templates" / "exam-paper" / "english-grade7.html",
        ]:
            with self.subTest(template=template.name):
                text = template.read_text(encoding="utf-8")
                question_chunks = text.split('<li class="question"')[1:]
                choice_count = sum('class="options"' in chunk for chunk in question_chunks)
                self.assertGreater(len(question_chunks), 0)
                self.assertEqual(choice_count / len(question_chunks), 0.6)

    def test_math_template_generates_formal_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "out"
            preview_dir = tmp_path / "preview"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_exam_paper.py"),
                    "--subject",
                    "math",
                    "--output-dir",
                    str(output_dir),
                    "--preview-dir",
                    str(preview_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            pdf_path = output_dir / "七年级下册数学模拟试卷.pdf"
            self.assertTrue(pdf_path.exists())
            html_path = preview_dir / "math-grade7.html"
            self.assertTrue(html_path.exists())
            self.assertIn("密封线内不要答题", html_path.read_text(encoding="utf-8"))

            reader = PdfReader(str(pdf_path))
            self.assertGreaterEqual(len(reader.pages), 5)
            page_texts = [page.extract_text() or "" for page in reader.pages]
            all_text = "\n".join(page_texts)
            self.assertIn("七年级下册数学模拟试卷", all_text)
            for index, page_text in enumerate(page_texts, start=1):
                self.assertIn(f"{index}/{len(reader.pages)}", page_text.replace(" ", ""))
            self.assertGreaterEqual(image_object_count(reader), 3)


if __name__ == "__main__":
    unittest.main()
