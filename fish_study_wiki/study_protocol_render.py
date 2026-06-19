from __future__ import annotations

from collections import Counter, defaultdict
from html import escape

from fish_study_wiki.study_protocol_models import (
    HomeworkItem,
    HomeworkPlan,
    KnowledgeMatch,
    ReviewPlanSource,
    WrongQuestionItem,
    WrongQuestionReview,
)


COLOR_LABELS = {
    "red": "红色",
    "yellow": "黄色",
    "blue": "蓝色",
}

COLOR_STRATEGIES = {
    "red": "先补知识点，再做基础变式，最后做 1 道迁移题。",
    "yellow": "按审题、单位、符号、计算、书写顺序做检查清单。",
    "blue": "做限时训练，先写步骤模板，再判断优先完成路径。",
}


def render_homework_student_html(plan: HomeworkPlan) -> str:
    return _html_document(
        title=f"{plan.date} 今日学习计划",
        body=f"""
<header>
  <h1>{escape(plan.date)} 今日学习计划</h1>
  <p>先看知识点，再做热身，最后完成正式任务。</p>
</header>
<section>
  <h2>知识点预习</h2>
  {_homework_knowledge_preview(plan.items)}
</section>
<section>
  <h2>热身区</h2>
  <ol>
    {_homework_warmups(plan.items)}
  </ol>
</section>
<section>
  <h2>正式任务清单</h2>
  <ol class="task-list">
    {_homework_tasks(plan.items)}
  </ol>
</section>
<section>
  <h2>自我检查区</h2>
  <ul class="check-list">
    <li>题号是否全部完成。</li>
    <li>单位、符号、步骤是否写清楚。</li>
    <li>不确定的题目是否已圈出。</li>
  </ul>
</section>
""",
    )


def render_wrong_question_student_html(review: WrongQuestionReview) -> str:
    return _html_document(
        title=f"{review.date} 错题复盘",
        body=f"""
<header>
  <h1>{escape(review.date)} 错题复盘</h1>
  <p>按贴纸颜色复盘，再完成同类变式。</p>
</header>
<section>
  <h2>知识点回顾</h2>
  {_wrong_knowledge_review(review.items)}
</section>
<section>
  <h2>贴纸策略</h2>
  <ul class="strategy-list">
    {_wrong_strategies(review.items)}
  </ul>
</section>
<section>
  <h2>同类变式题</h2>
  <ol class="task-list">
    {_variation_questions(review.items)}
  </ol>
</section>
<section>
  <h2>自我检查区</h2>
  <ul class="check-list">
    <li>是否能说出用到的知识点。</li>
    <li>是否按贴纸策略完成复盘。</li>
    <li>是否记录仍然不确定的步骤。</li>
  </ul>
</section>
""",
    )


def render_homework_parent_markdown(plan: HomeworkPlan) -> str:
    low_confidence = _low_confidence_lines(plan.items, plan.uncertain_items)
    return f"""# {plan.date} 今日学习计划家长参考

## 预计用时

{_estimated_homework_time(plan.items)}

## 检查顺序

{_homework_check_order(plan.items)}

## 知识点与任务

{_homework_parent_items(plan.items)}

## 答案/参考说明

- 本结构化输入未提供具体答案；家长可按作业原题另行核对。
- 优先检查步骤完整度、单位符号和被圈出的不确定题。

## 低置信度提醒

{low_confidence or "- 暂无。"}
"""


def render_wrong_question_parent_markdown(review: WrongQuestionReview) -> str:
    low_confidence = _low_confidence_lines(review.items, review.uncertain_items)
    return f"""# {review.date} 错题复盘家长参考

## 预计用时

{_estimated_wrong_time(review.items)}

## 检查顺序

{_wrong_check_order(review.items)}

## 错题讲解要点

{_wrong_parent_items(review.items)}

## 答案/参考说明

- 本结构化输入未提供标准答案；家长可对照原卷补充。
- 讲解时先确认错因颜色，再看孩子能否独立复述关键步骤。

## 低置信度提醒

{low_confidence or "- 暂无。"}
"""


def render_review_plan_markdown(source: ReviewPlanSource) -> str:
    counts = Counter(item.sticker_color for item in source.items)
    days = _review_day_count(len(source.items))
    grouped = _group_wrong_items_by_knowledge(source.items)
    priority = sorted(
        grouped.items(),
        key=lambda entry: (
            -sum(1 for item in entry[1] if item.sticker_color == "red"),
            -len(entry[1]),
            entry[0],
        ),
    )
    plan_lines = []
    for index in range(days):
        note, items = priority[index % len(priority)] if priority else ("待定位", ())
        colors = Counter(item.sticker_color for item in items)
        strategy = _review_strategy_from_counts(colors)
        plan_lines.append(
            f"- 第 {index + 1} 天：{_md_link(note)} - {strategy}"
        )
    retest = [
        f"- {_md_link(note)}：红色 {Counter(item.sticker_color for item in items)['red']} 次，建议优先复测。"
        for note, items in priority
        if Counter(item.sticker_color for item in items)["red"] >= 2
    ]
    return f"""# {source.date} 红黄蓝复习计划

## 贴纸统计

- 红色：{counts["red"]} 题
- 黄色：{counts["yellow"]} 题
- 蓝色：{counts["blue"]} 题

## 未来 {days} 天安排

{chr(10).join(plan_lines) if plan_lines else "- 暂无错题记录。"}

## 待复测知识点

{chr(10).join(retest) if retest else "- 暂无高优先级复测。"}
"""


def _html_document(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 16mm; }}
    * {{ box-sizing: border-box; }}
    body {{
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      padding: 12mm;
      color: #1f2933;
      background: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    h1 {{ margin: 0 0 6mm; font-size: 24px; }}
    h2 {{
      margin: 8mm 0 3mm;
      padding-bottom: 2mm;
      border-bottom: 1px solid #cbd5df;
      font-size: 18px;
    }}
    p {{ margin: 0 0 3mm; }}
    ul, ol {{ margin: 0; padding-left: 7mm; }}
    li {{ margin: 2mm 0; }}
    .task-list li, .strategy-list li, .check-list li {{ break-inside: avoid; }}
    .meta {{ color: #52606d; font-size: 13px; }}
    .knowledge {{ margin-top: 1mm; color: #334e68; }}
  </style>
</head>
<body>
{body.strip()}
</body>
</html>
"""


def _homework_knowledge_preview(items: tuple[HomeworkItem, ...]) -> str:
    rows = []
    for item in items:
        knowledge = _knowledge_text(item.matched_knowledge)
        rows.append(
            f"<article><h3>{escape(item.subject)}</h3>"
            f"<p class=\"knowledge\">{knowledge}</p></article>"
        )
    return "\n".join(rows) if rows else "<p>暂无任务。</p>"


def _homework_warmups(items: tuple[HomeworkItem, ...]) -> str:
    return "\n".join(
        f"<li>{escape(item.subject)}：用 2 分钟说出今天会用到的知识点，再完成 1 道基础热身。</li>"
        for item in items
    )


def _homework_tasks(items: tuple[HomeworkItem, ...]) -> str:
    rows = []
    for item in items:
        detail = "，".join(
            part
            for part in (
                item.book_or_source,
                f"第 {item.page} 页" if item.page else "",
                f"题号 {item.question_range}" if item.question_range else "",
                f"截止：{item.deadline}" if item.deadline else "",
            )
            if part
        )
        rows.append(
            f"<li><strong>{escape(item.subject)}</strong>：{escape(item.raw_text)}"
            f"<div class=\"meta\">{escape(detail)}</div></li>"
        )
    return "\n".join(rows)


def _wrong_knowledge_review(items: tuple[WrongQuestionItem, ...]) -> str:
    return "\n".join(
        f"<article><h3>{escape(item.subject)} {escape(item.question_id)}</h3>"
        f"<p class=\"knowledge\">{_knowledge_text(item.matched_knowledge)}</p></article>"
        for item in items
    )


def _wrong_strategies(items: tuple[WrongQuestionItem, ...]) -> str:
    return "\n".join(
        f"<li><strong>{escape(item.question_id)}</strong>："
        f"{escape(COLOR_LABELS.get(item.sticker_color, item.sticker_color))} - "
        f"{escape(COLOR_STRATEGIES.get(item.sticker_color, item.next_action))}</li>"
        for item in items
    )


def _variation_questions(items: tuple[WrongQuestionItem, ...]) -> str:
    rows = []
    for item in items:
        rows.append(
            f"<li>{escape(item.subject)} {escape(item.question_id)}："
            f"围绕“{escape(item.problem_type)}”完成 2 道同类基础题和 1 道小测题。</li>"
        )
    return "\n".join(rows)


def _knowledge_text(matches: tuple[KnowledgeMatch, ...]) -> str:
    if not matches:
        return "待定位"
    return "；".join(
        escape(
            f"{match.note}（{match.grade}{match.volume}，{match.chapter}，置信度：{match.confidence}）"
        )
        for match in matches
    )


def _estimated_homework_time(items: tuple[HomeworkItem, ...]) -> str:
    minutes = max(15, len(items) * 12 + 5)
    return f"- 约 {minutes} 分钟：知识点预习 5 分钟，每项作业约 12 分钟。"


def _estimated_wrong_time(items: tuple[WrongQuestionItem, ...]) -> str:
    per_color = {"red": 15, "yellow": 8, "blue": 10}
    minutes = sum(per_color.get(item.sticker_color, 10) for item in items)
    return f"- 约 {max(10, minutes)} 分钟：红色补概念，黄色查细节，蓝色做限时。"


def _homework_check_order(items: tuple[HomeworkItem, ...]) -> str:
    return "\n".join(
        f"- {index}. {item.subject}：{item.raw_text}"
        for index, item in enumerate(items, start=1)
    )


def _wrong_check_order(items: tuple[WrongQuestionItem, ...]) -> str:
    order = sorted(items, key=lambda item: {"red": 0, "yellow": 1, "blue": 2}.get(item.sticker_color, 3))
    return "\n".join(
        f"- {index}. {item.subject} {item.question_id}（{COLOR_LABELS.get(item.sticker_color, item.sticker_color)}）"
        for index, item in enumerate(order, start=1)
    )


def _homework_parent_items(items: tuple[HomeworkItem, ...]) -> str:
    lines = []
    for item in items:
        lines.append(f"- {item.subject}：{item.raw_text}")
        for match in item.matched_knowledge:
            lines.append(f"  - 知识点：{_md_link(match.note)}（置信度：{match.confidence}）")
    return "\n".join(lines) if lines else "- 暂无。"


def _wrong_parent_items(items: tuple[WrongQuestionItem, ...]) -> str:
    lines = []
    for item in items:
        lines.append(
            f"- {item.subject} {item.question_id}：{COLOR_LABELS.get(item.sticker_color, item.sticker_color)}，"
            f"错因：{item.reason}，建议：{item.next_action}"
        )
        for match in item.matched_knowledge:
            lines.append(f"  - 知识点：{_md_link(match.note)}（置信度：{match.confidence}）")
    return "\n".join(lines) if lines else "- 暂无。"


def _low_confidence_lines(
    items: tuple[HomeworkItem, ...] | tuple[WrongQuestionItem, ...],
    uncertain_items: tuple[str, ...],
) -> str:
    lines = [
        f"- {item.subject} {_item_name(item)}：{match.note}"
        for item in items
        for match in item.matched_knowledge
        if match.confidence == "low"
    ]
    lines.extend(f"- {item}" for item in uncertain_items)
    return "\n".join(lines)


def _item_name(item: HomeworkItem | WrongQuestionItem) -> str:
    return getattr(item, "raw_text", "") or getattr(item, "question_id", "")


def _group_wrong_items_by_knowledge(
    items: tuple[WrongQuestionItem, ...]
) -> dict[str, list[WrongQuestionItem]]:
    grouped: dict[str, list[WrongQuestionItem]] = defaultdict(list)
    for item in items:
        notes = [match.note for match in item.matched_knowledge] or ["待定位"]
        for note in notes:
            grouped[note].append(item)
    return grouped


def _review_day_count(item_count: int) -> int:
    return min(7, max(3, item_count))


def _review_strategy_from_counts(counts: Counter[str]) -> str:
    if counts["red"]:
        return "补概念 + 基础例题 + 迁移小测"
    if counts["yellow"]:
        return "审题检查清单 + 易错提醒"
    if counts["blue"]:
        return "限时训练 + 步骤模板"
    return "轻量复盘"


def _md_link(note: str) -> str:
    return "[[待定位]]" if note == "待定位" else f"[[{note}]]"
