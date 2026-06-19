#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fish_study_wiki.cli import main as cli_main


def main() -> None:
    raise SystemExit(cli_main(["inventory"]))


if __name__ == "__main__":
    main()
