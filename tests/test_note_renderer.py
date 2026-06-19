import unittest

from fish_study_wiki.models import TopicNote
from fish_study_wiki.note_renderer import render_topic_note


class NoteRendererTests(unittest.TestCase):
    def test_render_topic_note_contains_frontmatter_and_links(self):
        note = TopicNote(
            title="第1章 1.1 直线的相交",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_id="5star-math-zjjy-g7b-2026spring",
            source_file="第1章　1.1　直线的相交.pptx",
            status="extracted",
            summary="直线相交形成角，垂线是特殊的相交关系。",
        )

        markdown = render_topic_note(note)

        self.assertIn("type: knowledge", markdown)
        self.assertIn("source_id: 5star-math-zjjy-g7b-2026spring", markdown)
        self.assertIn("confidence: medium", markdown)
        self.assertIn("lifecycle_status: active", markdown)
        self.assertIn("# 第1章 1.1 直线的相交", markdown)
        self.assertIn("[[00-数学七年级下册索引]]", markdown)
        self.assertIn("直线相交形成角", markdown)


if __name__ == "__main__":
    unittest.main()
