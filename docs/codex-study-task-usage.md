# Codex 错题学习工具使用说明

本工具面向 Codex Desktop + Obsidian 本地学习流程。照片识别和题目理解由 Codex Desktop 完成；仓库只处理结构化 JSON，负责质量检查、打印材料渲染、Obsidian 记录和周复盘。

当前只保留两个入口：

- 日常：贴好红黄蓝标签的错题照片 -> 错因分析训练卷。
- 每周：结构化错题数据 -> 周复盘报告和巩固测试。

## 家长最简入口

家长或学生不需要运行命令，也不需要填写 JSON。

在 Codex 中上传错题照片后，只说：

```text
帮我生成错题知识点和测试题
```

Codex 应自动完成：

1. 读取当前知识库范围。
2. 视觉识别每张照片中的题目、所属学科和颜色标注。
3. 按学科分组，再按红黄蓝规则归类错因。
4. 对看不清、绿色、偏色、多色、无明确颜色或无法判断学科的照片列入待确认。
5. 生成结构化 `wrong_question_training` JSON，其中包含 `source_photos` 和每组分析的 `source_photo_ids`。
6. 调用 CLI 输出总训练卷、分学科训练卷、答案页、知识点讲解和 Obsidian 记录。
7. 用 Markdown 绝对路径文件链接返回结果。

推荐 Codex 使用项目 skill：

```text
fish-study-photo-workflow
```

开始分析前，先输出当前可用资料范围：

```bash
python3 -m fish_study_wiki.cli study-context
```

把输出内容作为 Codex Desktop 的上下文。Codex 只能基于其中列出的资料定位知识点；没有资料或看不清的内容必须进入待确认项。

## 日常错题训练

家长先和孩子在线下看错题，并尽量只用红黄蓝标记一级错因：

- 红色：不会，表示知识、方法或迁移能力不足。
- 黄色：马虎，表示审题、计算、符号、单位或书写问题。
- 蓝色：时间不够，表示速度、路径选择或时间分配问题。
- 其他颜色、混合颜色、拍照偏色、看不清颜色：不自动归因，进入待确认项。

在 Codex Desktop 上传一张或多张照片后，可以说：

```text
帮我生成错题知识点和测试题
```

Codex 需要在后台把照片结果整理成 `wrong_question_training` JSON，可参考：

```bash
samples/wrong-question-training.json
```

运行：

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json
```

主 CLI alias：

```bash
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json
```

默认输出：

- 学生训练卷：`outputs/YYYY-MM-DD/wrong-question-training.pdf`
- 批改答案页：`outputs/YYYY-MM-DD/wrong-question-training-answers.pdf`
- 分学科学生训练卷：`outputs/YYYY-MM-DD/math-training.pdf`、`science-training.pdf`、`english-training.pdf`
- 分学科批改答案页：`outputs/YYYY-MM-DD/math-training-answers.pdf`、`science-training-answers.pdf`、`english-training-answers.pdf`
- 分学科知识点讲解：`outputs/YYYY-MM-DD/math-knowledge.md`、`science-knowledge.md`、`english-knowledge.md`
- Obsidian 错题归因：`$FISH_STUDY_VAULT_ROOT/20-错题归因/YYYY-MM-DD.md`
- Obsidian 知识点事件：`$FISH_STUDY_VAULT_ROOT/10-教材Wiki/.../*.md`
- 本地知识图谱事件：`data/wiki/knowledge-graph.json`

学生训练卷不包含答案、参考答案、解析或解答。答案页单独保存，用于家长批改和下一次难度调整。

## 每周复盘

每周复盘基于已经沉淀的错题分析事件和训练结果，日常数据分析保持静默，周复盘才输出完整报告。

在 Codex Desktop 中可以说：

```text
帮我生成本周错题复盘和巩固测试
```

Codex 在后台整理成 `weekly_review` JSON，可参考：

```bash
samples/weekly-review-source.json
```

运行：

```bash
python3 -m fish_study_wiki.study_protocol_cli weekly-review samples/weekly-review-source.json
```

主 CLI alias：

```bash
python3 -m fish_study_wiki.cli study-weekly-review samples/weekly-review-source.json
```

默认输出：

- 周复盘报告：`outputs/YYYY-MM-DD/weekly-review.md`
- 周巩固测试卷：`outputs/YYYY-MM-DD/weekly-review.pdf`
- 周巩固答案页：`outputs/YYYY-MM-DD/weekly-review-answers.pdf`
- Obsidian 复习计划：`$FISH_STUDY_VAULT_ROOT/40-复习计划/YYYY-MM-DD.md`

周复盘报告包含错因分布、反复知识点、高频二级错因、难度是否合适、遗忘风险、复测队列和下周优先级。

## 真实试卷式模拟卷

当家长要求“看排版”“生成模拟卷”“像真实试卷一样”时，不使用日常错题训练卷的简化模板，而是按 `docs/exam-paper-output.md` 输出独立模拟卷。

必须满足：

- 三科独立成卷。
- A4 正式试卷样式：密封线、考生信息栏、注意事项、分大题、题量和分值说明。
- 涉及绘图的题必须使用 `gpt-image-2` 生成正式配图。
- 科学卷应包含多张图文题配图。
- 图片必须嵌入最终 PDF，不能依赖远程图片或 HTML 外链。
- PDF 底部必须有 `当前页/总页数` 页码。
- 输出后必须做视觉检查和 PDF 结构检查。

交付到 Codex 会话时，用 Markdown 绝对路径文件链接：

```md
[math-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)
```

不要优先使用 `127.0.0.1` 或 `/mnt/data` 作为交付方式。

## 难度校准

出题不只按知识点生成，还会结合训练结果判断难度是否合适。结构化数据中需要保留：

- 同一知识点最近正确率。
- 同一题型耗时和目标耗时。
- 完成状态：完成、超时或未完成。
- 主要错误。
- 上一次题目难度。
- 下一次建议难度。
- D+1、D+3、D+7、D+14 复测窗口。

默认策略：

- 红色高风险知识点先用基础题和少量标准题，不直接上挑战题。
- 黄色问题以标准题为主，嵌入检查点。
- 蓝色问题以标准限时题为主，题量少而集中。
- 连续正确后加入标准和变式。
- 连续错误后降回基础和标准，避免过难打击积极性。

## 待确认规则

Codex 看不清题目、无法确认知识点或诊断置信度不高时，不要猜。

- `confidence: high` 且 `confirmation_status: auto/confirmed` 才进入长期统计。
- 只有进入长期统计的错题事件才会写入本地知识图谱。
- `confidence: medium/low` 必须进入 `uncertain_items`。
- `source_photos` 中无法判断学科、低置信度或 `needs_confirmation` 的照片必须进入 `uncertain_items`。
- 每个分析组合的 `source_photo_ids` 只能引用同学科且已识别的照片。
- 待确认项会出现在当次记录中，但不会写入知识点长期趋势事件。
- 空知识点、待确认缺失、学生卷疑似含答案、难度梯度不合格时，CLI 会输出 `ERROR:` 并返回非 0。

如需改输出位置：

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json \
  --output-root /tmp/fish-study-outputs \
  --vault-root /tmp/fish-study-vault
```
