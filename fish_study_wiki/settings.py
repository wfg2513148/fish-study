import os
from pathlib import Path


REPO_ROOT = Path(
    os.environ.get("FISH_STUDY_REPO_ROOT", Path(__file__).resolve().parents[1])
).expanduser()
VAULT_ROOT = Path(
    os.environ.get(
        "FISH_STUDY_VAULT_ROOT",
        Path.home() / "Downloads" / "obsidian" / "fish-study",
    )
).expanduser()
RAW_SOURCE_DIR = REPO_ROOT / "sources" / "raw"
INVENTORY_DIR = REPO_ROOT / "sources" / "inventory"
EXTRACTED_DIR = REPO_ROOT / "sources" / "extracted"
REPORT_DIR = REPO_ROOT / "reports"
WIKI_DATA_DIR = REPO_ROOT / "data" / "wiki"
KNOWLEDGE_GRAPH_PATH = WIKI_DATA_DIR / "knowledge-graph.json"

GRADES = ["七年级", "八年级"]
VOLUMES = ["上册", "下册"]
SUBJECTS = ["语文", "数学", "英语", "科学", "地理", "中国历史", "道德与法治"]
STATUSES = ["available", "missing_source", "source_index", "extracted", "verified"]
