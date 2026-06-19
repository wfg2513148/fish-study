# fish-study

面向杭州初中学习场景的 Codex Desktop + Obsidian 本地学习工作流。

## 当前目标

- 用拍照方式识别已贴红黄蓝标签的错题卷。
- 根据错因、知识点、题型和历史训练结果生成可打印训练卷与独立答案页。
- 日常数据分析静默写入 Obsidian，每周输出完整复盘报告和巩固测试。
- 将初一、初二各学科知识点沉淀到独立 Obsidian vault，减少每次从 PDF/课件重新解析。
- 原始教材、教辅、课件只保存在本地；GitHub 仓库只保存流程、索引、模板和可复用脚本。

家长使用说明见：`docs/parent-user-manual.md`
真实试卷式模拟卷输出规范见：`docs/exam-paper-output.md`

## 常用指令

在 Codex Desktop 中上传照片后使用：

- `帮我生成错题知识点和测试题`
- `帮我生成本周错题复盘和巩固测试`

对应 CLI：

```bash
python3 -m fish_study_wiki.cli study-context
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json
python3 -m fish_study_wiki.study_protocol_cli weekly-review samples/weekly-review-source.json
```

颜色约定：

- 红色：不会
- 黄色：马虎
- 蓝色：时间不够

学生训练卷不包含答案、参考答案、解析或解答；批改答案页单独保存。

需要输出独立模拟卷时，先按 `docs/exam-paper-output.md` 的标准生成 HTML，再导出自包含 PDF：图片必须嵌入 PDF，底部页码使用 `当前页/总页数`，交付时使用 Markdown 绝对路径文件链接。

## 本地目录

- 项目仓库：`/Users/kwang/fish-study`
- Obsidian vault：`/Users/kwang/Downloads/obsidian/fish-study`
- 原始下载资料：`/Users/kwang/fish-study/sources/raw`
- 解压资料：`/Users/kwang/fish-study/sources/extracted`

## 初始化顺序

```bash
scripts/download_sources.sh
scripts/init_vault.sh
```

## Wiki 重建

资料 ZIP 已在 `sources/raw/` 后，按这个顺序重建索引、写入 Obsidian，并生成质量报告：

```bash
python3 -m fish_study_wiki.cli inventory
python3 -m fish_study_wiki.cli build
python3 -m fish_study_wiki.cli verify
```

兼容脚本仍可使用：

```bash
scripts/rebuild_zip_inventories.py
scripts/build_vault_indexes.py
```

`verify` 会同时写入：

- `reports/wiki-quality.md`
- `/Users/kwang/Downloads/obsidian/fish-study/00-入口/wiki-quality.md`

`build` 会同时写入本地知识图谱：

- `data/wiki/knowledge-graph.json`

质量报告覆盖初一、初二上下册 7 个学科的 28 个年级/册别/学科组合。当前没有本地资料的组合会标为 `missing_source`，不阻塞已下载资料的校验和重建。
已生成的 `type: knowledge` 或旧 `type: source-index` 知识点笔记会保留正文和错题事件，只迁移 frontmatter，用于记录 `source_id`、`confidence`、`last_confirmed`、`lifecycle_status` 等生命周期元数据。

## 增量资料接入

新增资料时只接入本地可用的 ZIP，不提交原始文件：

1. 将 ZIP 放入 `sources/raw/`。
2. 在 `data/sources/source-ledger.json` 增加一条记录，填写年级、册别、学科、版本、本地路径和 SHA256。
3. 运行 `python3 -m fish_study_wiki.cli inventory` 更新清单。
4. 运行 `python3 -m fish_study_wiki.cli build` 写入知识点笔记和学科索引。
5. 运行 `python3 -m fish_study_wiki.cli verify` 更新质量报告。

更完整的流程见 `docs/source-intake.md`。

## 版权边界

本项目只为家庭学习本地使用。不要把教材、课件 ZIP、完整 PDF、完整图片扫描件或大段原文提交到 GitHub；可以提交目录索引、校验值、知识点摘要、知识图谱、错题归因结构和自编练习。
