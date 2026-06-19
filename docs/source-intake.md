# Source Intake

本流程用于把新的本地教材、教辅或课件 ZIP 增量接入 Obsidian wiki。原始 ZIP 只保存在本机，不提交 Git。

## 1. 放入原始资料

把下载或家长提供的 ZIP 放到：

```bash
/Users/kwang/fish-study/sources/raw
```

文件名建议使用稳定的来源 ID，例如：

```text
5star-math-zjjy-g8a-2026fall.zip
```

## 2. 计算校验值

```bash
shasum -a 256 sources/raw/<source-id>.zip
```

记录输出中的 SHA256。后续 `verify` 会用它确认本地 ZIP 没有被替换或损坏。

## 3. 登记来源

编辑 `data/sources/source-ledger.json`，新增一条记录：

```json
{
  "source_id": "<source-id>",
  "subject": "数学",
  "grade": "八年级",
  "volume": "上册",
  "version": "浙教版",
  "source_type": "courseware",
  "status": "available",
  "local_path": "/Users/kwang/fish-study/sources/raw/<source-id>.zip",
  "sha256": "<sha256>"
}
```

字段必须和 `data/catalog/subject-matrix.json` 中的年级、册别、学科一致，否则质量报告无法把它归到 28 个覆盖行里。

## 4. 重建文件清单

```bash
python3 -m fish_study_wiki.cli inventory
```

该命令会更新 `sources/inventory/` 下的 `.sha256`、`.files.md` 和 `downloaded-sources.md`。

## 5. 写入 Obsidian

```bash
python3 -m fish_study_wiki.cli build
```

该命令会读取可用 ZIP 中的 PPTX，生成知识点笔记，并更新每个学科册别的 `00-...索引.md`。已有知识点笔记不会被覆盖，避免改掉手工整理过的内容。
如果已有笔记是 `type: knowledge` 或旧 `type: source-index`，命令只会迁移 frontmatter，补齐 `source_id`、`confidence`、`last_confirmed`、`lifecycle_status` 等生命周期字段，正文和错题分析事件保持不变。

命令还会刷新：

```text
data/wiki/knowledge-graph.json
```

该图谱记录教材来源、年级册别学科范围、知识点节点及它们之间的 `covers`、`contains`、`includes` 关系。

## 6. 校验质量报告

```bash
python3 -m fish_study_wiki.cli verify
```

该命令会写入两份相同的报告：

- `reports/wiki-quality.md`
- `/Users/kwang/Downloads/obsidian/fish-study/00-入口/wiki-quality.md`

报告必须保持 28 行覆盖矩阵。新增资料对应行应从 `missing_source` 变为 `verified` 或 `source_index`。如果出现 `ERROR`，先修复来源路径、SHA256、vault 索引、知识点生命周期字段或知识图谱，再提交。

## 7. 提交边界

可以提交：

- `data/sources/source-ledger.json`
- `sources/inventory/*.sha256`
- `sources/inventory/*.files.md`
- `sources/inventory/downloaded-sources.md`
- `data/wiki/knowledge-graph.json`
- `reports/wiki-quality.md`
- 文档、模板和 Python 脚本

不要提交：

- `sources/raw/*.zip`
- `sources/extracted/`
- 完整教材、完整课件、完整扫描件
