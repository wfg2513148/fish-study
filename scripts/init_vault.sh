#!/usr/bin/env bash
set -euo pipefail

VAULT="${FISH_STUDY_VAULT_ROOT:-$HOME/Downloads/obsidian/fish-study}"
mkdir -p \
  "$VAULT/.obsidian" \
  "$VAULT/00-入口" \
  "$VAULT/10-教材Wiki/七年级/下册" \
  "$VAULT/10-教材Wiki/八年级/上册" \
  "$VAULT/10-教材Wiki/八年级/下册" \
  "$VAULT/20-错题归因" \
  "$VAULT/30-每日学习计划" \
  "$VAULT/40-打印输出" \
  "$VAULT/90-资料索引" \
  "$VAULT/99-模板"

cat > "$VAULT/.obsidian/app.json" <<'JSON'
{
  "legacyEditor": false,
  "livePreview": true,
  "showLineNumber": false,
  "attachmentFolderPath": "90-资料索引/附件"
}
JSON

cat > "$VAULT/.obsidian/core-plugins.json" <<'JSON'
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "canvas",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "daily-notes",
  "templates",
  "note-composer",
  "command-palette",
  "editor-status",
  "bookmarks"
]
JSON

cat > "$VAULT/.obsidian/templates.json" <<'JSON'
{
  "folder": "99-模板"
}
JSON

cat > "$VAULT/00-入口/Fish Study 首页.md" <<'MD'
# Fish Study 首页

## 快速入口

- [[教材版本索引]]
- [[错题归因规则]]
- [[今日学习计划模板]]
- [[知识点笔记模板]]

## Codex 常用指令

- 帮我生成今日学习计划
- 帮我生成错题知识点和测试题
- 根据这张作业清单生成打印版学习要点和练习
- 根据红黄蓝贴纸归因生成复习计划

MD

cat > "$VAULT/00-入口/教材版本索引.md" <<'MD'
# 教材版本索引

## 七年级下册

| 学科 | 版本 | 状态 |
|---|---|---|
| 语文 | 统编/人教版 2024 | 封面已确认 |
| 数学 | 浙教版 | 封面已确认 |
| 英语 | 人教版 2024 审核通过 | 用户上传封面 |
| 科学 | 浙教版 2024，蓝色封面 | 待补齐目录 |
| 地理 | 人教版 2024 审核通过 | 用户上传封面 |
| 中国历史 | 人教版 2024 审核通过 | 用户上传封面 |
| 道德与法治 | 人教版 2024 审核通过 | 用户上传封面 |

## 八年级

待补齐八上、八下各学科教材版本和目录。

MD

cat > "$VAULT/20-错题归因/错题归因规则.md" <<'MD'
# 错题归因规则

| 颜色 | 归因 | Codex 处理重点 |
|---|---|---|
| 红色 | 不会 | 补知识点、补例题、生成基础变式 |
| 黄色 | 马虎 | 审题、计算、符号、单位、书写检查 |
| 蓝色 | 时间不够 | 固定解题路径、限时训练、优先级 |

每次错题复盘后，在对应知识点笔记里追加“错题记录”和“下一次小测”。

MD

cat > "$VAULT/99-模板/知识点笔记模板.md" <<'MD'
---
type: knowledge
subject:
grade:
volume:
chapter:
source:
confidence:
---

# 标题

## 一句话

## 必须掌握

## 常见题型

## 易错点

## 错题记录

## 关联

- [[教材版本索引]]

MD

cat > "$VAULT/99-模板/今日学习计划模板.md" <<'MD'
# 今日学习计划

日期：

## 作业清单

## 做题前知识点

## 打印练习

## 家长检查要点

MD

printf 'Initialized Obsidian vault at %s\n' "$VAULT"
