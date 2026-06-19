import unittest

from fish_study_wiki.models import SourceRecord, TopicNote


class ModelTests(unittest.TestCase):
    def test_source_record_requires_local_path_for_local_source(self):
        source = SourceRecord(
            source_id="5star-math-zjjy-g7b-2026spring",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_type="courseware",
            status="available",
            local_path="/Users/kwang/fish-study/sources/raw/5star-math-zjjy-g7b-2026spring.zip",
            sha256="25cb0437ab0d8fa94eb661d402ffda3b06165545d50d591785705a4890d4e6ff",
        )

        self.assertEqual(source.key, "七年级/下册/数学")
        self.assertTrue(source.is_available)

    def test_topic_note_slug_is_filesystem_safe(self):
        note = TopicNote(
            title="第1章 1.2 同位角、内错角、同旁内角",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_id="5star-math-zjjy-g7b-2026spring",
            source_file="第1章　1.2　同位角、内错角、同旁内角.pptx",
            status="source_index",
            summary="同位角、内错角、同旁内角的识别。",
        )

        self.assertEqual(note.safe_filename, "第1章 1.2 同位角、内错角、同旁内角.md")


if __name__ == "__main__":
    unittest.main()
