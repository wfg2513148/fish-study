from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from fish_study_wiki.models import SourceRecord, TopicNote
from fish_study_wiki.study_protocol_models import WrongQuestionTraining


SCHEMA_VERSION = 1


def build_topic_graph(
    sources: Iterable[SourceRecord],
    notes: Iterable[TopicNote],
) -> dict[str, Any]:
    graph = _empty_graph()
    for source in sources:
        _upsert_node(
            graph,
            {
                "id": source_node_id(source.source_id),
                "type": "source",
                "label": source.source_id,
                "subject": source.subject,
                "grade": source.grade,
                "volume": source.volume,
                "version": source.version,
                "status": source.status,
            },
        )
        _upsert_node(
            graph,
            {
                "id": scope_node_id(source.grade, source.volume, source.subject),
                "type": "curriculum_scope",
                "label": f"{source.subject}{source.grade}{source.volume}",
                "subject": source.subject,
                "grade": source.grade,
                "volume": source.volume,
            },
        )
        _upsert_edge(
            graph,
            source_node_id(source.source_id),
            scope_node_id(source.grade, source.volume, source.subject),
            "covers",
        )

    for note in notes:
        _upsert_node(
            graph,
            {
                "id": note.graph_id,
                "type": "knowledge_point",
                "label": note.title,
                "subject": note.subject,
                "grade": note.grade,
                "volume": note.volume,
                "version": note.version,
                "source_id": note.source_id,
                "source_file": note.source_file,
                "status": note.status,
                "confidence": note.confidence,
                "last_confirmed": note.last_confirmed,
                "lifecycle_status": note.lifecycle_status,
                "supersedes": list(note.supersedes),
                "reinforced_by": list(note.reinforced_by),
            },
        )
        _upsert_edge(graph, source_node_id(note.source_id), note.graph_id, "contains")
        _upsert_edge(
            graph,
            scope_node_id(note.grade, note.volume, note.subject),
            note.graph_id,
            "includes",
        )
    return _sorted_graph(graph)


def write_graph(graph: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_sorted_graph(graph), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def merge_training_events(path: Path, training: WrongQuestionTraining) -> None:
    graph = read_graph(path)
    for index, cluster in enumerate(training.clusters, start=1):
        diagnosis = cluster.diagnosis
        if diagnosis.confidence != "high":
            continue
        if diagnosis.confirmation_status not in {"auto", "confirmed"}:
            continue
        event_id = f"study_event:{training.date}:{training.source_batch}:{index}"
        error_id = error_node_id(diagnosis.primary_reason, diagnosis.secondary_reason)
        _upsert_node(
            graph,
            {
                "id": event_id,
                "type": "study_event",
                "label": f"{training.date} {cluster.subject} {cluster.problem_type}",
                "date": training.date,
                "source_batch": training.source_batch,
                "subject": cluster.subject,
                "problem_type": cluster.problem_type,
                "sticker_color": diagnosis.sticker_color,
                "primary_reason": diagnosis.primary_reason,
                "secondary_reason": diagnosis.secondary_reason,
                "confidence": diagnosis.confidence,
                "confirmation_status": diagnosis.confirmation_status,
                "difficulty_mix": list(cluster.difficulty_mix),
            },
        )
        _upsert_node(
            graph,
            {
                "id": error_id,
                "type": "error_type",
                "label": f"{diagnosis.primary_reason}/{diagnosis.secondary_reason}",
                "primary_reason": diagnosis.primary_reason,
                "secondary_reason": diagnosis.secondary_reason,
                "sticker_color": diagnosis.sticker_color,
            },
        )
        _upsert_edge(graph, event_id, error_id, "diagnosed_as")
        for match in cluster.matched_knowledge:
            if match.is_pending:
                continue
            topic_id = topic_node_id(
                match.grade,
                match.volume,
                cluster.subject,
                match.note,
            )
            _upsert_node(
                graph,
                {
                    "id": topic_id,
                    "type": "knowledge_point",
                    "label": match.note,
                    "subject": cluster.subject,
                    "grade": match.grade,
                    "volume": match.volume,
                    "confidence": match.confidence,
                    "lifecycle_status": "active",
                },
            )
            _upsert_edge(graph, event_id, topic_id, "targets")
            _upsert_edge(graph, error_id, topic_id, "affects")
    write_graph(graph, path)


def read_graph(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_graph()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"knowledge graph must be a JSON object: {path}")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    return data


def source_node_id(source_id: str) -> str:
    return f"source:{source_id}"


def scope_node_id(grade: str, volume: str, subject: str) -> str:
    return f"scope:{grade}:{volume}:{subject}"


def topic_node_id(grade: str, volume: str, subject: str, title: str) -> str:
    return f"topic:{grade}:{volume}:{subject}:{title}"


def error_node_id(primary_reason: str, secondary_reason: str) -> str:
    return f"error:{primary_reason}:{secondary_reason}"


def _empty_graph() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "nodes": [], "edges": []}


def _upsert_node(graph: dict[str, Any], node: dict[str, Any]) -> None:
    nodes = {item["id"]: item for item in graph.get("nodes", [])}
    current = nodes.get(node["id"], {})
    merged = {**current, **node}
    nodes[node["id"]] = merged
    graph["nodes"] = list(nodes.values())


def _upsert_edge(graph: dict[str, Any], source: str, target: str, edge_type: str) -> None:
    edge_id = f"{source}->{edge_type}->{target}"
    edges = {item["id"]: item for item in graph.get("edges", [])}
    edges[edge_id] = {
        "id": edge_id,
        "source": source,
        "target": target,
        "type": edge_type,
    }
    graph["edges"] = list(edges.values())


def _sorted_graph(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": graph.get("schema_version", SCHEMA_VERSION),
        "nodes": sorted(graph.get("nodes", []), key=lambda item: item["id"]),
        "edges": sorted(graph.get("edges", []), key=lambda item: item["id"]),
    }
