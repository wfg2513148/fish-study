#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fish_study_wiki.zip_inventory import rebuild_inventories

RAW_DIR = ROOT / "sources" / "raw"
INV_DIR = ROOT / "sources" / "inventory"


def main() -> None:
    rebuild_inventories(RAW_DIR, INV_DIR)


if __name__ == "__main__":
    main()
