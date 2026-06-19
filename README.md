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

## 版权边界

本项目只为家庭学习本地使用。不要把教材、课件 ZIP、完整 PDF、完整图片扫描件或大段原文提交到 GitHub；可以提交目录索引、校验值、知识点摘要、错题归因结构和自编练习。

