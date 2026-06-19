import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.models import TopicNote
from fish_study_wiki.vault_writer import write_subject_index, write_topic_note


class VaultWriterTests(unittest.TestCase):
    def test_write_topic_note_creates_subject_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            note = TopicNote(
                title="第1章 1.1 直线的相交",
                subject="数学",
                grade="七年级",
                volume="下册",
                version="浙教版",
                source_id="source",
                source_file="file.pptx",
                status="extracted",
                summary="summary",
            )

            path = write_topic_note(vault, note)

        self.assertTrue(path.name.endswith(".md"))
        self.assertIn("10-教材Wiki", str(path))

    def test_write_topic_note_does_not_overwrite_existing_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            note = TopicNote(
                title="第1章 1.1 直线的相交",
                subject="数学",
                grade="七年级",
                volume="下册",
                version="浙教版",
                source_id="source",
                source_file="file.pptx",
                status="extracted",
                summary="summary",
            )
            path = write_topic_note(vault, note)
            path.write_text("user note\n", encoding="utf-8")

            write_topic_note(vault, note)
            text = path.read_text(encoding="utf-8")

        self.assertEqual(text, "user note\n")

    def test_write_topic_note_updates_generated_frontmatter_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            note = TopicNote(
                title="第1章 1.1 直线的相交",
                subject="数学",
                grade="七年级",
                volume="下册",
                version="浙教版",
                source_id="source",
                source_file="file.pptx",
                status="extracted",
                summary="summary",
                confidence="high",
                last_confirmed="2026-06-19",
            )
            path = write_topic_note(vault, note)
            path.write_text(
                "---\ntype: source-index\nsubject: 数学\n---\n\n# 手写正文\n",
                encoding="utf-8",
            )

            write_topic_note(vault, note)
            text = path.read_text(encoding="utf-8")

        self.assertIn("source_id: source", text)
        self.assertIn("confidence: high", text)
        self.assertIn("# 手写正文", text)

    def test_write_subject_index_contains_topic_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            path = write_subject_index(
                vault,
                "七年级",
                "下册",
                "数学",
                "浙教版",
                ["[[第1章 1.1 直线的相交]]"],
            )
            text = path.read_text(encoding="utf-8")

        self.assertIn("# 数学七年级下册索引", text)
        self.assertIn("[[第1章 1.1 直线的相交]]", text)


if __name__ == "__main__":
    unittest.main()
