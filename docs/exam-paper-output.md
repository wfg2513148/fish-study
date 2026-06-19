# 真实试卷式模拟卷输出规范

这份文档复盘三科模拟卷打磨过程中的稳定做法。后续需要生成“像真实试卷一样”的模拟卷时，按这里执行。

## 已确认的改进要点

1. 三科必须独立成卷，不再合并到一个预览页。
2. 版式按正式试卷处理：A4、密封线、标题、版本/分值/时长、姓名班级得分用时栏、注意事项、分大题、题量和分值说明。
3. 题目不能只做示例题，要接近真实试卷结构：选择题、填空题、解答题、阅读/实验/图文综合题分层出现。
4. 涉及绘图的题必须使用 `gpt-image-2` 生成正式配图，不能用占位图、CSS 示意图或临时 SVG 冒充。
5. 科学卷需要大量图文题，图片以黑白教材/试卷风格线稿为主，便于打印。
6. 图片不能过窄。数学图 A、英语地图、科学图示都要保持足够阅读宽度。
7. 数学解答题答题框要足够大，避免学生写不下完整过程。
8. 最终交付 PDF，不交付依赖外链图片的 HTML；PDF 内必须嵌入图片，避免换电脑或手机后图片丢失。
9. PDF 底部必须有页码，格式为 `当前页/总页数`，例如 `1/5`、`1/8`。
10. 科学卷图片多，必须控制 PDF 体积，避免手机打开超时。
11. 交付到 Codex 会话时，使用 Markdown 绝对路径文件链接，例如 `[math-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)`。

## 推荐输出流程

1. 先生成三份 HTML：
   - `outputs/exam-preview/math-mock-paper.html`
   - `outputs/exam-preview/science-mock-paper.html`
   - `outputs/exam-preview/english-mock-paper.html`

2. 所有配图先落到本地目录：
   - `outputs/exam-preview/assets/`
   - 科学卷手机版或压缩版可使用 `outputs/exam-preview/mobile/science-assets/`

3. 图片规则：
   - 使用 `gpt-image-2`。
   - 黑白线稿优先，避免彩色照片风格。
   - 图中只保留必要标注，如 A/B/C/D、图 1、图 2。
   - 避免生成大段文字，题干文字放在 HTML 里。
   - 常规图宽建议不小于正文栏宽的 60%。
   - 关键图、地图、实验装置图建议使用中等或大图宽。

4. HTML 视觉检查：
   - 用 Playwright 截图检查桌面视口。
   - 检查图片是否加载失败。
   - 检查图片宽度是否明显偏小。
   - 检查文字、图、答题框是否重叠。
   - 检查每页底部是否有足够留白给页码。

5. 导出 PDF：
   - 用 Playwright 的 `page.pdf`。
   - `printBackground: true`。
   - `preferCSSPageSize: true`。
   - `displayHeaderFooter: true`。
   - footer 使用 Chrome PDF 页脚变量：

```html
<div style="width:100%;font-size:10px;color:#111;text-align:center;margin-bottom:5mm;">
  <span class="pageNumber"></span>/<span class="totalPages"></span>
</div>
```

6. PDF 验证：
   - 用 `pypdf` 检查页数。
   - 用 `pypdf` 检查每页是否能提取到对应页码。
   - 用 `pypdf` 检查图片对象数量。
   - 用 `qlmanage -t` 生成高分辨率首屏预览，人工确认页码真实可见。
   - 科学卷建议控制在 2MB 左右，至少应明显低于手机容易超时的体积。

## 当前稳定样例

当前三份样例的稳定状态：

| 学科 | 页数 | 图片数 | 说明 |
|---|---:|---:|---|
| 数学 | 5 | 3 | 解答题答题框已加大，图 A 宽度已优化 |
| 科学 | 8 | 16 | 使用压缩后本地图片，手机打开更稳 |
| 英语 | 5 | 1 | 地图宽度已优化 |

交付目录：

```text
outputs/codex-session-files/
```

交付链接格式：

```md
[math-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)
[science-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/science-grade7-mock-paper.pdf)
[english-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/english-grade7-mock-paper.pdf)
```

## 不要再走的弯路

- 不要把本地 `127.0.0.1` 链接当作手机可打开交付方式。
- 不要只给普通绝对路径文本；要用 Markdown 文件链接。
- 不要用 `/mnt/data` 作为默认附件目录；当前宿主机里 `/mnt` 是只读的。
- 不要直接给 HTML 作为最终交付物；HTML 可以预览，最终交付必须是 PDF。
- 不要手写 PDF 文本层补页码；某些阅读器能解析但不渲染。页码应在 Playwright 导出 PDF 时通过浏览器页脚生成。
