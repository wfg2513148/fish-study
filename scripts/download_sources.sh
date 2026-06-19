#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="$ROOT/sources/raw"
INV_DIR="$ROOT/sources/inventory"
mkdir -p "$RAW_DIR" "$INV_DIR" "$ROOT/sources/extracted"

download() {
  local id="$1"
  local url="$2"
  local file="$RAW_DIR/$id.zip"

  if [[ ! -s "$file" ]]; then
    curl -L --fail --retry 3 --output "$file" "$url"
  fi

  shasum -a 256 "$file" > "$INV_DIR/$id.sha256"
}

download "5star-math-zjjy-g7b-2026spring" "https://cdn12.bookln.cn/aj/app/forever/product/booklnweb/default/54909465/54909465_d15231ca56064513b832c4455d7a4a94.zip?download=true&filename=%E8%AF%BE%E4%BB%B6-26%E6%98%A5%E5%88%9D%E4%B8%AD%E6%95%B0%E5%AD%A6%E3%80%8A5%E6%98%9F%E5%AD%A6%E9%9C%B8%E3%80%8B%E6%B5%99%E6%95%99%E7%89%88%E4%B8%83%E4%B8%8B.zip"
download "5star-science-zjjy-g7b-2026spring" "https://cdn12.bookln.cn/aj/app/forever/product/booklnweb/default/54909465/54909465_9c8c8e7bcd56487aaece519400f54f78.zip?download=true&filename=%E8%AF%BE%E4%BB%B6-26%E6%98%A5%E5%88%9D%E4%B8%AD%E7%A7%91%E5%AD%A6%E3%80%8A5%E6%98%9F%E5%AD%A6%E9%9C%B8%E3%80%8B%E6%B5%99%E6%95%99%E7%89%88%E4%B8%83%E4%B8%8B.zip"
download "5star-english-pep-g7b-2026spring" "https://cdn12.bookln.cn/aj/app/forever/product/booklnweb/default/54909465/54909465_2ecf3b31f2f7411a9aeafad7bc3fba18.zip?download=true&filename=%E8%AF%BE%E4%BB%B6-26%E6%98%A5%E5%88%9D%E4%B8%AD%E8%8B%B1%E8%AF%AD%E3%80%8A5%E6%98%9F%E5%AD%A6%E9%9C%B8%E3%80%8B%E4%BA%BA%E6%95%99%E7%89%88%E4%B8%83%E4%B8%8B.zip"

"$ROOT/scripts/rebuild_zip_inventories.py"

printf 'Downloaded sources and wrote inventories to %s\n' "$INV_DIR"
