import unittest

from fish_study_wiki.models import SourceRecord
from fish_study_wiki.topic_builder import topic_from_source_file


class TopicBuilderTests(unittest.TestCase):
    def test_topic_from_source_file_uses_filename_title(self):
        source = SourceRecord(
            source_id="5star-science-zjjy-g7b-2026spring",
            subject="科学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_type="courseware",
            status="available",
            local_path="/tmp/science.zip",
            sha256="abc",
        )

        note = topic_from_source_file(
            source,
            "第2章　第3节　第1课时　原子结构模型与原子的构成.pptx",
            "原子由原子核和核外电子构成。",
        )

        self.assertEqual(note.title, "第2章 第3节 第1课时 原子结构模型与原子的构成")
        self.assertEqual(note.status, "extracted")
        self.assertIn("原子由原子核", note.summary)

    def test_topic_without_text_stays_source_index(self):
        source = SourceRecord(
            source_id="demo",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_type="courseware",
            status="available",
            local_path="/tmp/demo.zip",
            sha256="abc",
        )

        note = topic_from_source_file(source, "专题1.pptx", "")

        self.assertEqual(note.status, "source_index")
        self.assertIn("正文抽取未获得可用文本", note.summary)


if __name__ == "__main__":
    unittest.main()
