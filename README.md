# fish-study

面向杭州初中学习场景的 Codex Desktop + Obsidian 本地学习工作流。

## 当前目标

- 用拍照方式识别作业清单、错题卷和颜色贴纸标识。
- 在做作业前生成清晰知识要点和可打印练习。
- 将初一、初二各学科知识点沉淀到独立 Obsidian vault，减少每次从 PDF/课件重新解析。
- 原始教材、教辅、课件只保存在本地；GitHub 仓库只保存流程、索引、模板和可复用脚本。

## 常用指令

在 Codex Desktop 中上传照片后使用：

- `帮我生成今日学习计划`
- `帮我生成错题知识点和测试题`
- `根据这张作业清单生成打印版学习要点和练习`
- `根据红黄蓝贴纸归因生成复习计划`

颜色约定：

- 红色：不会
- 黄色：马虎
- 蓝色：时间不够

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

质量报告覆盖初一、初二上下册 7 个学科的 28 个年级/册别/学科组合。当前没有本地资料的组合会标为 `missing_source`，不阻塞已下载资料的校验和重建。

## 增量资料接入

新增资料时只接入本地可用的 ZIP，不提交原始文件：

1. 将 ZIP 放入 `sources/raw/`。
2. 在 `data/sources/source-ledger.json` 增加一条记录，填写年级、册别、学科、版本、本地路径和 SHA256。
3. 运行 `python3 -m fish_study_wiki.cli inventory` 更新清单。
4. 运行 `python3 -m fish_study_wiki.cli build` 写入知识点笔记和学科索引。
5. 运行 `python3 -m fish_study_wiki.cli verify` 更新质量报告。

更完整的流程见 `docs/source-intake.md`。

## 版权边界

本项目只为家庭学习本地使用。不要把教材、课件 ZIP、完整 PDF、完整图片扫描件或大段原文提交到 GitHub；可以提交目录索引、校验值、知识点摘要、错题归因结构和自编练习。
