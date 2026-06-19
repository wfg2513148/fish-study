from pathlib import Path


REPO_ROOT = Path("/Users/kwang/fish-study")
VAULT_ROOT = Path("/Users/kwang/Downloads/obsidian/fish-study")
RAW_SOURCE_DIR = REPO_ROOT / "sources" / "raw"
INVENTORY_DIR = REPO_ROOT / "sources" / "inventory"
EXTRACTED_DIR = REPO_ROOT / "sources" / "extracted"
REPORT_DIR = REPO_ROOT / "reports"

GRADES = ["七年级", "八年级"]
VOLUMES = ["上册", "下册"]
SUBJECTS = ["语文", "数学", "英语", "科学", "地理", "中国历史", "道德与法治"]
STATUSES = ["available", "missing_source", "source_index", "extracted", "verified"]
