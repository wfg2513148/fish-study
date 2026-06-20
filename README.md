# Fish Study

这是一个给家长使用的本地学习辅助工具。

它把 Codex Desktop、Obsidian 和本地教材资料连起来，用来做三件事：

1. 根据孩子的错题照片，整理错因和知识点。
2. 生成可以打印的学生训练卷和家长答案页。
3. 把错题、知识点和复习计划长期记录到 Obsidian，方便每周复盘。

它不是自动判卷 App，也不是完整题库。看不清、不确定、没有资料的内容，应该先标为“待确认”，不要硬猜。

## 现在能用哪些资料

当前已经整理好的资料范围是：

| 年级 | 册别 | 学科 | 版本 | 知识点笔记 |
|---|---|---|---|---:|
| 七年级 | 下册 | 数学 | 浙教版 | 112 篇 |
| 七年级 | 下册 | 科学 | 浙教版 | 84 篇 |
| 七年级 | 下册 | 英语 | 人教版 | 53 篇 |

其他学科、七上、八下还没有完整接入。遇到这些内容时，不要让工具直接编知识点。

## 适合谁用

适合这样的家庭学习场景：

- 家长愿意先和孩子一起看错题。
- 家长能给错题贴一个简单颜色标签。
- 希望把错题变成后续训练，而不是只讲一遍就结束。
- 希望每周知道孩子反复错在哪里。

不适合：

- 直接把整本教材上传让工具出完整题库。
- 让工具替代老师判卷。
- 让工具在没有资料、照片模糊时强行分析。

## 每天怎么用

### 第 1 步：给错题贴颜色

只贴一级原因，不需要分析太细。

| 颜色 | 含义 | 怎么判断 |
|---|---|---|
| 红色 | 不会 | 知识点不会、方法不会、不会迁移 |
| 黄色 | 马虎 | 审题漏条件、计算错、单位符号错、步骤写漏 |
| 蓝色 | 时间不够 | 会做但慢、卡第一步、计算太久、时间分配不合理 |

### 第 2 步：打开项目目录

```bash
cd /path/to/fish-study
```

### 第 3 步：先看当前知识库范围

```bash
python3 -m fish_study_wiki.cli study-context
```

把这段输出复制给 Codex Desktop，作为它分析照片前的上下文。

### 第 4 步：上传错题照片给 Codex

在 Codex Desktop 里说：

```text
请基于当前 Fish Study 知识库上下文，分析这些贴了红黄蓝标签的错题。
生成 wrong_question_training JSON。
看不清或知识点不确定的题，不要猜，放入 uncertain_items。
```

生成的 JSON 可以参考：

```text
samples/wrong-question-training.json
```

### 第 5 步：生成训练卷和答案页

```bash
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json
```

成功后会生成：

- 学生训练卷：`outputs/YYYY-MM-DD/wrong-question-training.html`
- 家长答案页：`outputs/YYYY-MM-DD/wrong-question-training-answers.html`
- Obsidian 错题记录：`$FISH_STUDY_VAULT_ROOT/20-错题归因/YYYY-MM-DD.md`

学生只看训练卷。答案页给家长批改，不要提前给孩子。

## 每周怎么用

每周做一次复盘，不需要每天做大报告。

在 Codex Desktop 里说：

```text
请根据本周错题归因记录和训练结果，生成 weekly_review JSON。
重点看反复知识点、红黄蓝错因分布、复测队列和下周优先级。
```

生成的 JSON 可以参考：

```text
samples/weekly-review-source.json
```

然后运行：

```bash
python3 -m fish_study_wiki.cli study-weekly-review samples/weekly-review-source.json
```

成功后会生成：

- 周复盘报告：`outputs/YYYY-MM-DD/weekly-review.md`
- 周巩固测试卷：`outputs/YYYY-MM-DD/weekly-review.html`
- 周巩固答案页：`outputs/YYYY-MM-DD/weekly-review-answers.html`
- Obsidian 复习计划：`$FISH_STUDY_VAULT_ROOT/40-复习计划/YYYY-MM-DD.md`

## 想生成正式模拟卷怎么办

如果你想要“像真实试卷一样”的数学、科学、英语模拟卷，可以让 Codex 说清楚：

```text
请基于 Fish Study 当前资料，生成三科独立模拟卷。
要求按真实试卷格式排版，涉及绘图的题必须使用 gpt-image-2。
最终输出 PDF，图片必须嵌入 PDF，底部加 当前页/总页数 页码。
```

模拟卷输出规范见：

- `docs/exam-paper-output.md`
- `.codex/skills/fish-study-exam-paper/SKILL.md`

在 Codex 会话里发送本地 PDF 时，使用 Markdown 文件链接：

```md
[math-grade7-mock-paper.pdf](/absolute/path/to/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)
```

不要优先用 `127.0.0.1` 或 `/mnt/data`。

## 常用命令

看当前可用资料：

```bash
python3 -m fish_study_wiki.cli study-context
```

生成日常错题训练：

```bash
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json
```

生成每周复盘：

```bash
python3 -m fish_study_wiki.cli study-weekly-review samples/weekly-review-source.json
```

检查知识库质量：

```bash
python3 -m fish_study_wiki.cli verify
```

重建资料索引和知识点：

```bash
python3 -m fish_study_wiki.cli inventory
python3 -m fish_study_wiki.cli build
python3 -m fish_study_wiki.cli verify
```

## 文件都在哪里

| 内容 | 位置 |
|---|---|
| 项目仓库 | 当前 git clone 目录 |
| Obsidian 知识库 | `$FISH_STUDY_VAULT_ROOT`，默认 `$HOME/Downloads/obsidian/fish-study` |
| 原始 ZIP/PDF/课件 | `sources/raw` |
| 解压后的资料 | `sources/extracted` |
| 生成的训练卷/模拟卷 | `outputs` |
| 知识库质量报告 | `reports/wiki-quality.md` |

## 新增资料怎么接入

新增资料时只接入本地可用的 ZIP，不提交原始文件。

1. 把 ZIP 放入 `sources/raw/`。
2. 在 `data/sources/source-ledger.json` 增加一条记录。
3. 运行 `python3 -m fish_study_wiki.cli inventory`。
4. 运行 `python3 -m fish_study_wiki.cli build`。
5. 运行 `python3 -m fish_study_wiki.cli verify`。

更完整的流程见：

- `docs/source-intake.md`
- `docs/source-policy.md`

## 重要原则

- 学生卷和答案页一定分开。
- 红色错因先补基础，不要直接上难题。
- 黄色错因重点练审题和检查习惯。
- 蓝色错因重点练限时和解题路径。
- 没资料、看不清、不确定，就不要猜。
- 原始教材、教辅、课件、完整 PDF、完整图片扫描件不要提交到 GitHub。

## 更多说明

- 家长使用手册：`docs/parent-user-manual.md`
- Codex 错题学习工具说明：`docs/codex-study-task-usage.md`
- AI 安装配置说明：`docs/ai-installation-setup.md`
- 真实试卷式模拟卷输出规范：`docs/exam-paper-output.md`
- 资料接入说明：`docs/source-intake.md`
- 版权和资料边界：`docs/source-policy.md`
