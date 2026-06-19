# Codex 学习任务使用说明

本工具面向 Codex Desktop + Obsidian 学习流程。照片和 OCR 不在仓库内实现；Codex Desktop 先理解照片内容，再把结果整理成结构化 JSON，本仓库负责确定性检查、渲染和写入文件。

## 从照片到 JSON

在 Codex Desktop 中上传作业、错题或贴纸记录照片后，让 Codex 只输出 JSON，不要输出讲解正文。JSON 需要包含：

- `task_type`：`homework_plan`、`wrong_question_review` 或 `review_plan_source`。
- `date`：学习日期，格式如 `2026-06-19`。
- `items`：每条作业或错题的结构化信息。
- `matched_knowledge`：已匹配的教材知识点；不能确定时使用 `note: "待定位"`。
- `confidence`：`high`、`medium` 或 `low`。
- `uncertain_items`：低置信度、待定位、看不清或需要家长确认的内容。

可直接参考仓库内样例：

- `samples/homework-plan.json`
- `samples/wrong-question-review.json`
- `samples/review-plan-source.json`

## 今日学习计划

生成学生可打印 HTML、家长 Markdown 参考和 Obsidian 每日学习记录：

```bash
python3 -m fish_study_wiki.study_protocol_cli homework samples/homework-plan.json
```

主 CLI alias：

```bash
python3 -m fish_study_wiki.cli study-homework samples/homework-plan.json
```

默认输出：

- 学生版：`outputs/YYYY-MM-DD/today-study-plan.html`
- 家长参考：`outputs/YYYY-MM-DD/today-study-plan-parent.md`
- Obsidian：`/Users/kwang/Downloads/obsidian/fish-study/30-每日学习计划/YYYY-MM-DD.md`

## 错题知识点和测试题

生成错题复盘学生 HTML、家长 Markdown 参考，并写入错题归因和教材知识点记录：

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-review.json
```

主 CLI alias：

```bash
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-review.json
```

默认输出：

- 学生版：`outputs/YYYY-MM-DD/wrong-question-review.html`
- 家长参考：`outputs/YYYY-MM-DD/wrong-question-review-parent.md`
- Obsidian 错题归因：`/Users/kwang/Downloads/obsidian/fish-study/20-错题归因/YYYY-MM-DD.md`
- Obsidian 知识点记录：`/Users/kwang/Downloads/obsidian/fish-study/10-教材Wiki/.../*.md`

## 红黄蓝复习计划

根据错题贴纸颜色生成 3 到 7 天复习计划，并写入 Obsidian 复习计划记录：

```bash
python3 -m fish_study_wiki.study_protocol_cli review-plan samples/review-plan-source.json
```

主 CLI alias：

```bash
python3 -m fish_study_wiki.cli study-review-plan samples/review-plan-source.json
```

默认输出：

- 复习计划 Markdown：`outputs/YYYY-MM-DD/review-plan.md`
- Obsidian：`/Users/kwang/Downloads/obsidian/fish-study/40-复习计划/YYYY-MM-DD.md`

## 输出隔离

学生 HTML 不包含答案或解析，只保留知识点预习、热身、正式任务、复盘策略、自我检查和同类练习。家长 Markdown 单独保存，可包含参考说明和低置信度提醒，避免学生打印材料泄漏答案。

如需改输出位置，使用：

```bash
python3 -m fish_study_wiki.study_protocol_cli homework samples/homework-plan.json \
  --output-root /tmp/fish-study-outputs \
  --vault-root /tmp/fish-study-vault
```

## 低置信度和待定位

Codex 看不清题目、无法确认知识点或知识点匹配置信度为 `low` 时，不要猜。处理规则：

- 在 `matched_knowledge` 中写 `note: "待定位"`，并把对应题目写入 `uncertain_items`。
- 低置信度匹配必须在 `uncertain_items` 中点名题目或知识点。
- CLI 会运行质量检查；缺知识点、低置信度未标记、学生输出疑似含答案时，会在 stderr 输出 `ERROR:` 并返回非 0。
- 失败后先修正 JSON，再重新运行命令。
