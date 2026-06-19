#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INV_DIR = ROOT / "sources" / "inventory"
VAULT = Path("/Users/kwang/Downloads/obsidian/fish-study")

SOURCE_MAP = {
    "5star-math-zjjy-g7b-2026spring": ("数学", "七年级", "下册", "浙教版", "5星学霸课件"),
    "5star-science-zjjy-g7b-2026spring": ("科学", "七年级", "下册", "浙教版", "5星学霸课件"),
    "5star-english-pep-g7b-2026spring": ("英语", "七年级", "下册", "人教版", "5星学霸课件"),
}

SUBJECTS = ["语文", "数学", "英语", "科学", "地理", "中国历史", "道德与法治"]
VOLUMES = [
    ("七年级", "上册"),
    ("七年级", "下册"),
    ("八年级", "上册"),
    ("八年级", "下册"),
]


def safe_name(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120] or "未命名"


def files_from_inventory(source_id: str) -> list[str]:
    path = INV_DIR / f"{source_id}.files.md"
    if not path.exists():
        return []

    files: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| File ") or line.startswith("|---"):
            continue
        parts = line.strip().strip("|").rsplit("|", 1)
        if len(parts) != 2:
            continue
        files.append(parts[0].strip().replace("\\|", "|"))
    return files


def write_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def make_subject_indexes() -> None:
    for grade, volume in VOLUMES:
        for subject in SUBJECTS:
            folder = VAULT / "10-教材Wiki" / grade / volume / subject
            index = folder / f"00-{subject}{grade}{volume}索引.md"
            write_if_missing(
                index,
                f"""# {subject}{grade}{volume}索引

## 教材版本

待确认或待补齐。

## 知识点

待从教材目录、作业清单、错题和本地资料逐步补齐。

## 关联

- [[教材版本索引]]

""",
            )


def make_courseware_notes() -> None:
    for source_id, (subject, grade, volume, version, source_type) in SOURCE_MAP.items():
        files = files_from_inventory(source_id)
        folder = VAULT / "10-教材Wiki" / grade / volume / subject
        index_path = folder / f"00-{subject}{grade}{volume}索引.md"
        links = []
        if index_path.exists():
            current = index_path.read_text(encoding="utf-8")
            current = current.replace(
                "待确认或待补齐。",
                f"{version}（本地课件来源：{source_type}；最终以孩子纸质教材和官方目录为准。）",
                1,
            )
            index_path.write_text(current, encoding="utf-8")

        for file_name in files:
            title = Path(file_name).stem
            note_name = safe_name(title)
            note_path = folder / f"{note_name}.md"
            links.append(f"- [[{note_name}]]")
            write_if_missing(
                note_path,
                f"""---
type: source-index
subject: {subject}
grade: {grade}
volume: {volume}
version: {version}
source: {source_id}
source_type: {source_type}
confidence: medium
---

# {note_name}

## 定位

- 学科：{subject}
- 年级：{grade}
- 册别：{volume}
- 版本：{version}
- 来源文件：`{file_name}`

## 知识点摘要

待从课件内容、教材目录和孩子错题中补齐。

## 常见题型

待补齐。

## 易错点

待补齐。

## 关联

- [[00-{subject}{grade}{volume}索引]]
- [[教材版本索引]]

""",
            )

        if links:
            current = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
            generated = "\n".join(links)
            marker = "## 本地课件索引"
            if marker not in current:
                index_path.write_text(
                    current.rstrip()
                    + f"\n\n{marker}\n\n来源：`{source_id}`\n\n{generated}\n",
                    encoding="utf-8",
                )


def main() -> None:
    make_subject_indexes()
    make_courseware_notes()
    print(f"Built vault indexes under {VAULT}")


if __name__ == "__main__":
    main()
