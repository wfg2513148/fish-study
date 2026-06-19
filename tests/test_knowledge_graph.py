import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.knowledge_graph import build_topic_graph, merge_training_events
from fish_study_wiki.models import SourceRecord, TopicNote
from fish_study_wiki.study_protocol_models import load_wrong_question_training


class KnowledgeGraphTests(unittest.TestCase):
    def test_build_topic_graph_links_source_scope_and_topic(self):
        source = SourceRecord(
            source_id="source",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_type="courseware",
            status="available",
            local_path="/tmp/source.zip",
            sha256="abc",
        )
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

        graph = build_topic_graph([source], [note])

        node_ids = {node["id"] for node in graph["nodes"]}
        edge_types = {edge["type"] for edge in graph["edges"]}
        self.assertIn("source:source", node_ids)
        self.assertIn(note.graph_id, node_ids)
        self.assertIn("contains", edge_types)
        self.assertIn("includes", edge_types)

    def test_merge_training_events_skips_unconfirmed_clusters(self):
        training = load_wrong_question_training("samples/wrong-question-training.json")
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = Path(tmp) / "data" / "wiki" / "knowledge-graph.json"

            merge_training_events(graph_path, training)
            data = json.loads(graph_path.read_text(encoding="utf-8"))

        study_events = [
            node for node in data["nodes"] if node["type"] == "study_event"
        ]
        event_labels = "\n".join(node["label"] for node in study_events)
        self.assertEqual(len(study_events), 2)
        self.assertIn("科学 概念识别", event_labels)
        self.assertIn("数学 限时计算", event_labels)
        self.assertNotIn("数学 角关系计算", event_labels)


if __name__ == "__main__":
    unittest.main()
