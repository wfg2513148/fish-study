from __future__ import annotations

from fish_study_wiki.models import TopicNote


def render_topic_note(note: TopicNote) -> str:
    index_name = f"00-{note.subject}{note.grade}{note.volume}索引"
    return f"""---
type: knowledge
subject: {note.subject}
grade: {note.grade}
volume: {note.volume}
version: {note.version}
source: {note.source_id}
source_file: {note.source_file}
status: {note.status}
---

# {note.title}

## 一句话

{note.summary}

## 必须掌握

- 能说出本知识点的定义、条件和使用场景。
- 能把题目中的关键词对应到本知识点。
- 能完成至少 2 道同类基础题。

## 常见题型

- 概念识别题
- 方法应用题
- 易错辨析题

## 易错点

- 未区分题目条件和结论。
- 跳过关键步骤直接写答案。
- 没有把单位、符号或关键词检查一遍。

## 错题记录

使用红黄蓝贴纸复盘后追加记录。

## 关联

- [[{index_name}]]
- [[教材版本索引]]
- [[错题归因规则]]
"""
