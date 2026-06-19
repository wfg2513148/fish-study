from __future__ import annotations

from pathlib import Path

from fish_study_wiki.models import TopicNote
from fish_study_wiki.note_renderer import render_topic_frontmatter, render_topic_note


GENERATED_BEGIN = "<!-- fish-study-wiki:generated-topic-links:start -->"
GENERATED_END = "<!-- fish-study-wiki:generated-topic-links:end -->"


def subject_dir(vault: Path, grade: str, volume: str, subject: str) -> Path:
    return vault / "10-教材Wiki" / grade / volume / subject


def topic_link(note: TopicNote) -> str:
    return f"[[{note.safe_filename[:-3]}]]"


def _generated_section(links: list[str]) -> str:
    link_text = "\n".join(f"- {link}" for link in sorted(set(links)))
    if not link_text:
        link_text = "- 本学科本册已建索引；源资料覆盖情况见 [[wiki-quality]]。"
    return f"{GENERATED_BEGIN}\n{link_text}\n{GENERATED_END}"


def _new_subject_index(
    grade: str, volume: str, subject: str, version: str, links: list[str]
) -> str:
    return f"""# {subject}{grade}{volume}索引

## 教材版本

{version or "待确认或待补齐。"}

## 知识点

{_generated_section(links)}

## 关联

- [[教材版本索引]]
- [[wiki-quality]]
"""


def _merge_generated_section(current: str, links: list[str]) -> str:
    section = _generated_section(links)
    if GENERATED_BEGIN in current and GENERATED_END in current:
        before = current.split(GENERATED_BEGIN, 1)[0].rstrip()
        after = current.split(GENERATED_END, 1)[1].lstrip()
        return f"{before}\n\n{section}\n\n{after}".rstrip() + "\n"
    return current.rstrip() + f"\n\n## 本地课件索引\n\n{section}\n"


def write_subject_index(
    vault: Path,
    grade: str,
    volume: str,
    subject: str,
    version: str,
    links: list[str],
) -> Path:
    folder = subject_dir(vault, grade, volume, subject)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"00-{subject}{grade}{volume}索引.md"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        path.write_text(_merge_generated_section(current, links), encoding="utf-8")
    else:
        path.write_text(
            _new_subject_index(grade, volume, subject, version, links),
            encoding="utf-8",
        )
    return path


def write_topic_note(vault: Path, note: TopicNote) -> Path:
    folder = subject_dir(vault, note.grade, note.volume, note.subject)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / note.safe_filename
    if not path.exists():
        path.write_text(render_topic_note(note), encoding="utf-8")
    else:
        current = path.read_text(encoding="utf-8")
        updated = _merge_topic_frontmatter(current, note)
        if updated != current:
            path.write_text(updated, encoding="utf-8")
    return path


def _merge_topic_frontmatter(current: str, note: TopicNote) -> str:
    if not current.startswith("---\n"):
        return current
    end_marker = "\n---"
    end = current.find(end_marker, 4)
    if end == -1:
        return current
    frontmatter = current[4:end]
    if "type: knowledge" not in frontmatter and "type: source-index" not in frontmatter:
        return current
    body = current[end + len(end_marker) :].lstrip("\n")
    return f"{render_topic_frontmatter(note).rstrip()}\n\n{body}"
