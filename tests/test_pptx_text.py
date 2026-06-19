import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.pptx_text import extract_pptx_text
from tests.fixtures.make_pptx_fixture import make_pptx


class PptxTextTests(unittest.TestCase):
    def test_extract_pptx_text_returns_slide_text_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.pptx"
            make_pptx(path, ["直线的相交", "垂线与垂线段"])

            text = extract_pptx_text(path)

        self.assertEqual(text, "直线的相交\n\n垂线与垂线段")


if __name__ == "__main__":
    unittest.main()
