# 科学源截图试卷 A4 PDF 工作流

本文档用于把手机截图中的科学原题整理成 A4 纸张版 PDF。目标不是“重写一份相似试卷”，而是保留原题题意、图文关系和关键标注，并输出可在手机上稳定打开的 PDF。

## 适用范围

- 用户提供科学类题目截图，要求提取原题、套用 A4 试卷模板、输出 PDF。
- 题目包含实验装置、生物结构、曲线图、表格、A-D 图像选项、图 1/图 2 等配图。
- 用户要求“保留原题原图”“不要自由发挥”“图片只做清晰化处理”。

不适用：用户明确要求新编试卷或生成全新示意图。那种任务可以使用 `gpt-image-2`，但仍要遵守试卷版式和 PDF 验收规则。

## 总体原则

1. 先结构化，再排版。不要边看截图边直接拼 HTML。
2. 科学源题默认裁剪净化原图，不自由重绘。
3. 配图必须跟随题干或具体小问，不按题号粗暴堆叠。
4. `subquestions` 和 `options` 是不同概念。选择题选项不是子题。
5. manifest 必须参与硬校验，不只是备注。
6. 最终验收以 PDF 渲染页图为准，不以中间 HTML 或裁图为准。

## 执行计划模板

每次处理新的科学源截图卷，按下面顺序推进。每一步没有通过验证，不进入下一步。

1. 输入盘点 → 验证：截图数量、题号范围、缺失区域和 hash 已记录。
2. OCR / 人工转写 → 验证：题干、单位、上下标、图号、选项、表格行列已人工核对。
3. 题目模型 → 验证：每题都有 `question_id`、`stem`、`type`、`figures`、`subquestions`、`options`；选择题选项没有写入 `subquestions`。
4. 源图裁剪净化 → 验证：每张最终图都有 manifest，且 `source_sha256`、`source_crop_bbox`、`cleaned_sha256`、`belongs_to`、`render_near` 完整。
5. HTML A4 排版 → 验证：题号和题干同行，子题号为 `1）`，无子题的题没有空子题标记，选项是 A/B/C/D 块。
6. PDF 导出与页图渲染 → 验证：PDF 是 A4、图片已嵌入、页脚 `当前/总页数` 可见且可提取，页图 `page-01.png ... page-N.png` 连续且晚于 PDF。
7. 脚本硬校验 → 验证：`scripts/validate_science_source_paper.py` 通过。
8. 视觉验收 → 验证：逐页检查图像归属、图号、选项字母、坐标轴、表格、标签、分页。
9. 交付 → 验证：PDF 已复制到 `outputs/codex-session-files/`，聊天里使用文件名完全一致的 Markdown 绝对路径链接。

## 1. 输入盘点

为每张截图记录：

- 本地路径。
- 文件 hash。
- 可见题号范围。
- 是否存在截图裁切、滚动截断、题图缺边、答案区干扰。
- 低置信区域，例如图像选项只露出字母但图形不可见。

如果截图本身缺失关键内容，标记为 `source_limited`。不得凭记忆、常识或图像模型补画缺失区域，除非用户明确要求补图。

## 2. 题目模型

每道题先整理成结构化数据：

```json
{
  "question_id": 6,
  "type": "experiment",
  "stem": "...",
  "figures": ["q06-fig1", "q06-options", "q06-fig2"],
  "tables": [],
  "subquestions": [
    {"id": 1, "text": "..."},
    {"id": 4, "text": "...", "figures": ["q06-options"]}
  ],
  "options": []
}
```

版式规则：

- 题号：`1.`、`2.`、`3.`，并与题干同一行。
- 子题号：`1）`、`2）`、`3）`。
- 无子题的题目不渲染空的 `1）`。
- 选择题选项使用 A/B/C/D 选项块，不放入 `subquestions`。
- 如果选项内容本身是表格行 `A/B/C/D`，显示为“表中A项”等，避免 `A.A`。

## 3. 配图 manifest

每张最终图片必须有 manifest 条目：

```json
{
  "figure_id": "q06-options",
  "question_id": 6,
  "source_photo": "/tmp/.../7-照片-7.jpg",
  "source_sha256": "...",
  "source_crop_bbox": {
    "left": 25,
    "top": 260,
    "right": 590,
    "bottom": 590,
    "coordinate_system": "source image pixel, origin at top-left"
  },
  "cleaned_path": "/Users/kwang/fish-study/outputs/.../q06-options.png",
  "cleaned_sha256": "...",
  "belongs_to": "subquestion_4",
  "render_near": "inside_subquestion_4",
  "must_preserve_details": ["A", "B", "C", "D", "坐标轴V-t", "①②曲线"],
  "verification_status": "source_limited",
  "issues": ["源截图中C选项只显示字母，图像本体不可见。"]
}
```

要求：

- 每个 HTML `<img>` 必须对应一个 manifest 条目。
- 每个必用 manifest 图必须在 HTML/PDF 中出现一次。
- `source_sha256` 和 `cleaned_sha256` 都必须锁定，避免源截图或清理图被替换。
- `source_crop_bbox` 必须在源图尺寸范围内，且不能是异常小的裁剪。
- `render_near` 必须精确，例如 `after_stem`、`inside_subquestion_4`、`after_options_table`。
- `must_preserve_details` 至少列出图号、选项字母、坐标轴、单位、对象数量、实验变量或控制关系。

## 4. 图像处理规则

允许：

- 裁剪源截图。
- 去掉手机 UI、卡片阴影、灰底。
- 增强对比度、锐度。
- 轻微校正倾斜。
- 压缩图片体积。

禁止：

- 默认用 `gpt-image-2` 重绘源题图。
- 改变对象数量、相对位置、标签、坐标轴、刻度、数据点、表格数值。
- 添加原图没有的说明文字。
- 删除实验对照组或多步骤关系。
- 用“更好看”的图替代原图。

## 5. 多图题放置规则

多图题必须按归属拆分。

示例：

- 电解水题：图 1 属于题干；A-D 图像选项属于第 4 小问；图 2 属于第 5 小问。
- 水沸腾题：A/B/C 图属于第 1、2 小问；A-D 冷却曲线属于第 3 小问。
- 植物结构题：甲乙丙丁整排图属于题干，A-D 是选项块。

不要用一个 `source-stack` 把所有图堆在题干后面。

## 6. HTML 硬校验

交付前必须通过脚本：

```bash
python3 scripts/validate_science_source_paper.py \
  --manifest outputs/2026-06-20/source-figure-manifest.json \
  --html outputs/2026-06-20/science-source-paper-verified.html \
  --pdf outputs/2026-06-20/science-source-paper-verified.pdf \
  --render-dir outputs/2026-06-20/layout-check-verified/pages
```

脚本会拦截：

- manifest 字段缺失。
- 源图 hash 不一致。
- 清理图 hash 不一致。
- bbox 越界或异常小。
- HTML 图片没有 manifest。
- manifest 图片没有渲染。
- 图片渲染到错误题号或错误子题。
- `<svg>`、`data:image`、CSS 图片绕过、旧 gpt 重绘路径。
- 空子题号。
- 选择题选项被渲染成子题。
- `A.A` / `B.B` 式混淆选项。
- PDF 非 A4、页脚缺失或页图过期。
- PDF 图片数不足。
- 没有最终渲染页图。

## 7. PDF 视觉验收

导出 PDF 后，把每页渲染成图片。短 PDF 直接检查每页；长 PDF 至少检查所有含图、表、A-D 图像选项、密集标签的页面。

必须看：

- 题号 `1.` 是否和题干同行。
- 子题号是否为 `1）`，且只用于真实小问。
- A-D 选项是否是选项块，不是子题。
- 多图题图像是否在对应小问附近。
- 图 1、图 2、甲乙丙丁、A-D、坐标轴、单位、表格文字是否完整。
- 图片是否过窄、被分页截断、与文字重叠。
- 页脚是否真实可见。

当前回归样例：

- 第 1 页：检查题号同行、子题 `1）2）3）`、露点图和水珠图标签。
- 第 4-5 页：检查第 6 题图 1、第 4 小问 A-D 图、第 5 小问图 2 的归属。
- 第 6 页：检查第 8 题无空 `1）`，第 9 题主图和 A-D 图分别属于对应小问。
- 第 8 页：检查第 13 题彩色分层图、表格和横排 A-D 选项。
- 第 9 页：检查第 17 题“表中A项”等选项格式，以及第 18 题甲乙丙丁图号。

验收记录至少写清：

- PDF 文件名、页数、图片数。
- 脚本命令和输出结果。
- 已检查的页图范围。
- 任何 `source_limited` 图的原因和是否影响题意。

历史重点样例：

- 第 6 题页面：检查图 1、第 4 小问 A-D 图、第 5 小问图 2。
- 第 8/10 题页面：检查无空 `1）`。
- 第 17 题页面：检查“表中A项”等选项格式。
- 第 18 题页面：检查 A-D 选项块和甲乙丙丁图号。

## 8. 交付

最终 PDF 必须复制到：

```text
outputs/codex-session-files/
```

如果用户需要在当前 Codex 会话里直接打开，也复制一份到仓库根目录。

回复使用 Markdown 绝对路径链接：

```md
[2026-06-20-science-source-paper-verified.pdf](/Users/kwang/fish-study/2026-06-20-science-source-paper-verified.pdf)
```

不要使用：

- 普通文本路径。
- `127.0.0.1`。
- `/mnt/data`。
- 只给 HTML。

## 9. 不得交付的情况

- 有未登记图片。
- 有 manifest 图未渲染。
- 有 `needs_human_review` / `fail` / `uncertain` 状态。
- 有空子题号。
- 有选择题被当成子题。
- 有源图被默认重绘。
- 未生成 PDF 渲染页图。
- 未做主代理最终视觉检查。
