from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
from pathlib import Path
import re
from typing import Mapping

from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    KnowledgeMatch,
    SourcePhoto,
    TrainingQuestion,
    TrainingResult,
    WeeklyReviewSource,
    WrongQuestionTraining,
)

LEARNING_LABEL_PATTERNS = (
    r"^第[0-9一二三四五六七八九十]+章\s*",
    r"^第[0-9一二三四五六七八九十]+节\s*",
    r"^第[0-9一二三四五六七八九十]+课时\s*",
    r"^专题[0-9一二三四五六七八九十]+\s*",
    r"^[0-9]+(?:\.[0-9]+)+\s*",
)


COLOR_LABELS = {
    "red": "红色",
    "yellow": "黄色",
    "blue": "蓝色",
    "unknown": "待确认颜色",
}

COLOR_STRATEGIES = {
    "red": "先补知识点，再做基础题和少量标准题。",
    "yellow": "先圈条件，再按审题、单位、符号、计算、书写顺序检查。",
    "blue": "做限时训练，先写步骤模板，再判断优先完成路径。",
    "unknown": "先确认照片标注和题目归因，再决定训练方式。",
}

DIFFICULTY_LABELS = {
    "basic": "基础",
    "standard": "标准",
    "variant": "变式",
    "challenge": "挑战",
}
CHOICE_RATIO = 0.6
CHOICE_LABELS = ("A", "B", "C", "D")


def render_training_student_html(training: WrongQuestionTraining) -> str:
    return _html_document(
        title=f"{training.date} 错题分析训练卷",
        body=f"""
<header>
  <h1>{escape(training.date)} 错题分析训练卷</h1>
  <p class="subtitle">错题巩固训练 · A4 打印版 · 先补知识点，再完成同类题</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>得分：<span class="blank"></span></div>
    <div>用时：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">注意：本卷按错误类型、知识点和题型编排。先阅读每组补救提示，再完成训练题；计算题须写出关键步骤和单位。</p>
<section class="section">
  <h2 class="section-title">一、训练任务 <span class="score">共 {len(training.clusters)} 组</span></h2>
  {_training_student_clusters(training.clusters)}
</section>
<section class="section">
  <h2 class="section-title">二、自检区 <span class="score">完成后勾选</span></h2>
  <ul class="check-list">
    <li>我能说出本组题对应的知识点。</li>
    <li>我能说明这次要避免的错误类型。</li>
    <li>我已圈出仍不确定的步骤，并写下原因。</li>
  </ul>
</section>
""",
    )


def render_training_answer_html(training: WrongQuestionTraining) -> str:
    return _html_document(
        title=f"{training.date} 错题分析训练答案",
        body=f"""
<header>
  <h1>{escape(training.date)} 错题分析训练答案</h1>
  <p class="subtitle">批改参考 · 评分点 · 掌握判断 · 下一次难度建议</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>批改人：<span class="blank"></span></div>
    <div>批改日期：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">说明：答案页用于家长或老师批改。先看评分点，再根据掌握判断决定是否升高难度。</p>
<section class="section">
  <h2 class="section-title">答案与评分 <span class="score">逐题核对</span></h2>
  {_training_answer_clusters(training.clusters)}
</section>
""",
    )


def render_subject_knowledge_markdown(
    training: WrongQuestionTraining,
    subject: str,
) -> str:
    clusters = tuple(cluster for cluster in training.clusters if cluster.subject == subject)
    photo_by_id = {photo.photo_id: photo for photo in training.source_photos}
    return f"""# {subject} 错题知识点讲解

## 照片来源

{_subject_source_photo_lines(clusters, photo_by_id)}

## 知识点与根因

{_subject_cluster_knowledge_lines(clusters, photo_by_id)}

## 待确认项

{_subject_uncertain_lines(training.uncertain_items, subject, clusters)}
"""


def render_subject_knowledge_html(
    training: WrongQuestionTraining,
    subject: str,
) -> str:
    clusters = tuple(cluster for cluster in training.clusters if cluster.subject == subject)
    photo_by_id = {photo.photo_id: photo for photo in training.source_photos}
    return _html_document(
        title=f"{training.date} {subject} 错题知识点讲解",
        body=f"""
<header>
  <h1>{escape(training.date)} {escape(subject)} 错题知识点讲解</h1>
  <p class="subtitle">错因归类 · 关键知识 · 图示讲解 · 训练建议</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>复习日期：<span class="blank"></span></div>
    <div>完成度：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">说明：本讲义根据本批错题照片生成。先看图示和错因，再回到训练卷完成同类题；照片颜色归因为自动归类，需以老师或家长复核为准。</p>
<section class="section">
  <h2 class="section-title">一、照片来源 <span class="score">共 {len(_cluster_source_photo_ids(clusters))} 张</span></h2>
  <ul class="compact-list">{_subject_source_photo_html_items(clusters, photo_by_id)}</ul>
</section>
<section class="section">
  <h2 class="section-title">二、知识点与根因 <span class="score">共 {len(clusters)} 组</span></h2>
  {_subject_cluster_knowledge_cards(clusters, photo_by_id)}
</section>
<section class="section">
  <h2 class="section-title">三、待确认项 <span class="score">复核后再入长期统计</span></h2>
  <ul class="compact-list">{_subject_uncertain_html_items(training.uncertain_items, subject, clusters)}</ul>
</section>
""",
    )


def render_subject_knowledge_cards_markdown(
    training: WrongQuestionTraining,
    subject: str,
    diagram_assets: Mapping[str, Path | str] | None = None,
) -> str:
    cards = _subject_knowledge_card_items(training, subject)
    focus_by_note = _knowledge_focus_by_note(training, subject)
    if not cards:
        return f"""# {subject} 知识点复习卡

暂无已定位知识点。
"""
    sections = []
    for index, match in enumerate(cards, start=1):
        body = _knowledge_card_body(match.note, focus_by_note.get(match.note, ()))
        asset = _knowledge_card_asset(match.note, diagram_assets)
        title = knowledge_card_display_title(match.note)
        image_lines = (f"![{title}]({asset})", "") if asset else ()
        title = knowledge_card_display_title(match.note)
        sections.extend(
            (
                f"## {title}",
                "",
                *image_lines,
                f"**核心定义或结构**：{body['core']}",
                "",
                "**必须记住**：",
                *[f"- {item}" for item in body["must_remember"]],
                "",
                f"**复习重点**：{body['focus_tip']}",
                "",
                "**易混点**：",
                *[f"- {item}" for item in body["pitfalls"]],
                "",
                f"**自检问题**：{body['self_check']}",
                "",
            )
        )
    return "\n".join((f"# {subject} 知识点复习卡", "", *sections)).strip() + "\n"


def render_subject_knowledge_cards_html(
    training: WrongQuestionTraining,
    subject: str,
    diagram_assets: Mapping[str, Path | str] | None = None,
) -> str:
    cards = _subject_knowledge_card_items(training, subject)
    focus_by_note = _knowledge_focus_by_note(training, subject)
    return _html_document(
        title=f"{training.date} {subject} 知识点复习卡",
        body=f"""
<header>
  <h1>{escape(training.date)} {escape(subject)} 知识点复习卡</h1>
  <p class="subtitle">按知识学习顺序排列 · 先理清路径，再复述概念和步骤</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>复习日期：<span class="blank"></span></div>
    <div>完成度：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">说明：本材料用于补齐基础知识。阅读每张卡后，合上材料复述核心定义、关键关系和易混点。</p>
<section class="section">
  <h2 class="section-title">知识点复习卡 <span class="score">共 {len(cards)} 张</span></h2>
  {_subject_knowledge_card_html(cards, focus_by_note, diagram_assets)}
</section>
""",
        show_seal=False,
    )


def knowledge_card_matches(
    training: WrongQuestionTraining,
    subject: str,
) -> tuple[KnowledgeMatch, ...]:
    return _subject_knowledge_card_items(training, subject)


def knowledge_card_needs_diagram(note: str) -> bool:
    visual_keywords = (
        "同位角",
        "内错角",
        "同旁内角",
        "平行线",
        "原子结构",
        "原子的构成",
        "化学式",
        "相对分子质量",
        "分子",
        "原子",
        "离子",
        "元素",
        "密度",
        "沸腾",
        "汽化",
        "液化",
        "变化与性质",
        "温度对物质性质",
        "探索物质变化",
        "种子",
        "萌发",
        "细菌",
        "真菌",
        "根",
        "茎",
        "植物",
    )
    return any(keyword in note for keyword in visual_keywords)


def knowledge_card_display_title(note: str) -> str:
    title = note.strip()
    changed = True
    while changed:
        changed = False
        for pattern in LEARNING_LABEL_PATTERNS:
            cleaned = re.sub(pattern, "", title).strip()
            if cleaned != title:
                title = cleaned
                changed = True
    return title or note.strip()


def render_weekly_review_markdown(source: WeeklyReviewSource) -> str:
    color_counts = Counter(cluster.diagnosis.sticker_color for cluster in source.events)
    secondary_counts = Counter(
        cluster.diagnosis.secondary_reason for cluster in source.events
    )
    knowledge_counts = _weekly_knowledge_counts(source.events)
    return f"""# {source.week_start} 至 {source.week_end} 错题周复盘

## 错因分布

- 红色（不会）：{color_counts["red"]} 组
- 黄色（马虎）：{color_counts["yellow"]} 组
- 蓝色（时间不够）：{color_counts["blue"]} 组
- 待确认颜色：{color_counts["unknown"]} 组

## 反复知识点

{_weekly_repeated_knowledge_lines(knowledge_counts)}

## 高频二级错因

{_weekly_secondary_reason_lines(secondary_counts)}

## 难度是否合适/过难过易

{_weekly_difficulty_fit_lines(source.results)}

## 遗忘风险/复测队列

{_weekly_review_queue_lines(source.review_queue)}

## 下周优先级

{_weekly_priority_lines(source.events, source.results, source.review_queue)}
"""


def render_weekly_worksheet_html(source: WeeklyReviewSource) -> str:
    return _html_document(
        title=f"{source.week_end} 周复盘训练卷",
        body=f"""
<header>
  <h1>{escape(source.week_start)} 至 {escape(source.week_end)} 周复盘训练卷</h1>
  <p class="subtitle">周复盘巩固 · A4 打印版 · 先复测再训练</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>得分：<span class="blank"></span></div>
    <div>用时：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">注意：优先完成到期复测队列，再做本周高频错因训练；限时题请记录实际用时。</p>
<section class="section">
  <h2 class="section-title">一、复测队列 <span class="score">先完成</span></h2>
  {_weekly_review_queue_tasks(source.review_queue)}
</section>
<section class="section">
  <h2 class="section-title">二、本周训练题 <span class="score">按错因分组</span></h2>
  {_training_student_clusters(source.events)}
</section>
<section class="section">
  <h2 class="section-title">三、自检区 <span class="score">完成后勾选</span></h2>
  <ul class="check-list">
    <li>复测题是否在目标时间内完成。</li>
    <li>同一知识点是否还能独立说出关键步骤。</li>
    <li>下周需要继续练的项目是否已标出。</li>
  </ul>
</section>
""",
    )


def render_weekly_answer_html(source: WeeklyReviewSource) -> str:
    return _html_document(
        title=f"{source.week_end} 周复盘训练答案",
        body=f"""
<header>
  <h1>{escape(source.week_start)} 至 {escape(source.week_end)} 周复盘训练答案</h1>
  <p class="subtitle">复测答案参考 · 本周训练题评分</p>
  <div class="info">
    <div>姓名：<span class="blank"></span></div>
    <div>班级：<span class="blank"></span></div>
    <div>批改人：<span class="blank"></span></div>
    <div>批改日期：<span class="blank"></span></div>
  </div>
</header>
<p class="notice">说明：答案页用于批改和调整下周训练优先级。</p>
<section class="section">
  <h2 class="section-title">一、复测答案参考 <span class="score">到期项目</span></h2>
  {_weekly_review_queue_answers(source.review_queue)}
</section>
<section class="section">
  <h2 class="section-title">二、训练题答案与评分 <span class="score">逐题核对</span></h2>
  {_training_answer_clusters(source.events)}
</section>
""",
    )


def _html_document(title: str, body: str, show_seal: bool = True) -> str:
    seal = (
        '<div class="seal">学校 班级 姓名 考号 密封线内不要答题</div>'
        if show_seal
        else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 12mm; }}
    * {{ box-sizing: border-box; }}
    body {{
      width: 210mm;
      margin: 0 auto;
      padding: 0;
      color: #111;
      background: #e8e8e8;
      font-family: "Songti SC", "Noto Serif CJK SC", "Microsoft YaHei", serif;
      line-height: 1.5;
    }}
    .paper {{
      position: relative;
      min-height: 297mm;
      padding: 13mm 13mm 13mm 20mm;
      background: #fff;
      border: 1px solid #999;
    }}
    .seal {{
      position: absolute;
      top: 13mm;
      bottom: 13mm;
      left: 7mm;
      width: 7mm;
      border-right: 1px dashed #333;
      color: #333;
      font-size: 12px;
      letter-spacing: 2px;
      writing-mode: vertical-rl;
      text-align: center;
    }}
    header {{
      text-align: center;
      border-bottom: 3px double #111;
      padding-bottom: 4mm;
    }}
    header h1 {{
      margin: 0;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 2mm 0 0;
      font-size: 14px;
    }}
    .info {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 3mm;
      margin-top: 5mm;
      text-align: left;
      font-size: 13px;
    }}
    .blank {{
      display: inline-block;
      min-width: 28mm;
      border-bottom: 1px solid #333;
    }}
    .notice {{
      margin: 5mm 0;
      padding: 2mm 3mm;
      border: 1px solid #222;
      font-size: 13px;
    }}
    .section {{
      margin-top: 6mm;
      break-inside: avoid;
    }}
    .section-title {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin: 0 0 3mm;
      padding: 1.5mm 0;
      border-top: 2px solid #111;
      border-bottom: 1px solid #111;
      font-size: 18px;
    }}
    .score {{
      font-size: 13px;
      font-weight: 400;
    }}
    p {{ margin: 0 0 3mm; }}
    ul, ol {{ margin: 0; padding-left: 7mm; }}
    li {{ margin: 3mm 0; }}
    article {{ break-inside: avoid; margin: 0 0 6mm; }}
    h3 {{
      margin: 4mm 0 2mm;
      font-size: 15px;
      font-weight: 700;
    }}
    .task-list li, .check-list li {{ break-inside: avoid; }}
    .knowledge {{
      margin: 1mm 0 2mm;
      color: #111;
      font-size: 13px;
    }}
    .tag {{
      display: inline-block;
      margin-right: 2mm;
      color: #111;
      font-size: 12px;
    }}
    .task-list > li {{
      padding-bottom: 2mm;
    }}
    .answer-line {{
      min-height: 9mm;
      margin-top: 2mm;
      border-bottom: 1px solid #555;
    }}
    .answer-box {{
      min-height: 28mm;
      margin-top: 2mm;
      border: 1px solid #333;
    }}
    .options {{
      margin-top: 2mm;
      padding-left: 8mm;
    }}
    .options li {{
      margin: 1.5mm 0;
    }}
    .choice-answer {{
      margin-top: 2mm;
      min-height: 8mm;
      border-bottom: 1px solid #555;
    }}
    .compact-list li {{
      margin: 1.5mm 0;
    }}
    .knowledge-card {{
      break-after: page;
      break-inside: avoid;
      margin: 0;
      padding: 0 0 4mm;
    }}
    .knowledge-card:last-child {{ break-after: auto; }}
    .concept-grid {{
      display: block;
    }}
    .diagram {{
      margin: 2mm 0 6mm;
      padding: 2.5mm;
      border: 1px solid #555;
      background: #fafafa;
      font-size: 11px;
      text-align: center;
    }}
    .question-figure {{
      margin: 2mm 0 3mm;
      padding: 2mm;
      border: 1px solid #555;
      background: #fafafa;
      font-size: 11px;
      text-align: center;
    }}
    .diagram img {{
      display: block;
      width: 100%;
      height: 95mm;
      object-fit: contain;
    }}
    .diagram figcaption {{
      margin-top: 1.5mm;
      color: #333;
    }}
    .question-figure svg {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .key-list {{
      margin-top: 0;
      font-size: 13px;
    }}
    .card-block {{
      margin: 0 0 3mm;
      padding: 2mm 0 0;
      border-top: 1px solid #ddd;
      font-size: 13px;
    }}
    .card-block strong {{
      display: inline-block;
      min-width: 17mm;
    }}
    @media print {{
      body {{
        width: auto;
        background: #fff;
      }}
      .paper {{
        min-height: auto;
        border: 0;
      }}
      .section,
      .question {{
        break-inside: auto;
      }}
    }}
  </style>
</head>
<body>
<main class="paper">
{seal}
{body.strip()}
</main>
</body>
</html>
"""


def _training_student_clusters(clusters: tuple[AnalysisCluster, ...]) -> str:
    rows = []
    question_index = 1
    choice_count = _choice_question_count(clusters)
    for index, cluster in enumerate(clusters, start=1):
        rows.append(
            "<article>"
            f"<h3>{index}. {_training_group_title(cluster)}</h3>"
            f"<p class=\"knowledge\">补救：{_knowledge_repair_text(cluster)}</p>"
            f"{_training_cluster_figure(cluster)}"
            f"<ol class=\"task-list\">"
            f"{_training_question_prompts(cluster.training_questions, question_index, choice_count)}</ol>"
            "</article>"
        )
        question_index += len(cluster.training_questions)
    return "\n".join(rows) if rows else "<p>暂无训练任务。</p>"


def _training_group_title(cluster: AnalysisCluster) -> str:
    label = COLOR_LABELS.get(
        cluster.diagnosis.sticker_color,
        cluster.diagnosis.sticker_color,
    )
    knowledge = _plain_knowledge_notes(cluster.matched_knowledge)
    return escape(
        f"{label}{cluster.diagnosis.primary_reason} / "
        f"{cluster.diagnosis.secondary_reason} × {knowledge} × {cluster.problem_type}"
    )


def _knowledge_repair_text(cluster: AnalysisCluster) -> str:
    strategy = COLOR_STRATEGIES.get(
        cluster.diagnosis.sticker_color,
        "先复述知识点，再完成同类训练。",
    )
    notes = _plain_knowledge_notes(cluster.matched_knowledge)
    return escape(f"{notes}：{strategy}")


def _training_cluster_figure(cluster: AnalysisCluster) -> str:
    if cluster.subject != "科学":
        return ""
    return _knowledge_diagram(cluster.problem_type).replace(
        'class="diagram"',
        'class="question-figure"',
        1,
    ).replace(
        "</svg><div>",
        "</svg><div>科学图示：",
        1,
    )


def _training_question_prompts(
    questions: tuple[TrainingQuestion, ...],
    start_index: int = 1,
    choice_count: int = 0,
) -> str:
    rows = []
    for index, question in enumerate(questions, start=start_index):
        question_type = "选择题" if index <= choice_count else "非选择题"
        answer_area = (
            _choice_question_options(question, index)
            if index <= choice_count
            else "<div class=\"answer-box\"></div>"
        )
        rows.append(
            "<li class=\"question\">"
            f"<span class=\"points\">第 {index} 题</span> "
            f"<span class=\"tag\">题型：{question_type}</span>"
            f"<span class=\"tag\">难度："
            f"{escape(_difficulty_label(question.difficulty))}</span>"
            f"{escape(question.prompt)}"
            f"{answer_area}"
            "</li>"
        )
    return "\n".join(rows)


def _training_answer_clusters(clusters: tuple[AnalysisCluster, ...]) -> str:
    rows = []
    question_index = 1
    choice_count = _choice_question_count(clusters)
    for index, cluster in enumerate(clusters, start=1):
        rows.append(
            "<article>"
            f"<h3>{index}. {_training_group_title(cluster)}</h3>"
            f"<ol class=\"task-list\">"
            f"{_training_question_answers(cluster.training_questions, question_index, choice_count)}</ol>"
            "</article>"
        )
        question_index += len(cluster.training_questions)
    return "\n".join(rows) if rows else "<p>暂无答案。</p>"


def _training_question_answers(
    questions: tuple[TrainingQuestion, ...],
    start_index: int = 1,
    choice_count: int = 0,
) -> str:
    rows = []
    for index, question in enumerate(questions, start=start_index):
        choice_key = ""
        if index <= choice_count:
            choice_key = (
                f"<p><strong>选择题答案：</strong>正确选项 "
                f"{escape(_choice_correct_label(index))}</p>"
            )
        rows.append(
            "<li>"
            f"<p><span class=\"tag\">难度："
            f"{escape(_difficulty_label(question.difficulty))}</span>"
            f"{escape(question.prompt)}</p>"
            f"{choice_key}"
            f"<p><strong>答案：</strong>{escape(question.answer)}</p>"
            f"<p><strong>评分点：</strong>"
            f"{escape('；'.join(question.scoring_points) or '按关键步骤给分')}</p>"
            f"<p><strong>掌握判断：</strong>{escape(question.mastery_signal)}</p>"
            f"<p><strong>下一次难度建议：</strong>"
            f"{escape(_next_difficulty_suggestion(question.difficulty))}</p>"
            "</li>"
        )
    return "\n".join(rows)


def _choice_question_count(clusters: tuple[AnalysisCluster, ...]) -> int:
    total = sum(len(cluster.training_questions) for cluster in clusters)
    return round(total * CHOICE_RATIO)


def _choice_question_options(question: TrainingQuestion, question_index: int) -> str:
    options = _choice_options(question, question_index)
    items = "\n".join(f"<li>{escape(option)}</li>" for option in options)
    return (
        f"<ol class=\"options\" type=\"A\">{items}</ol>"
        "<div class=\"choice-answer\">选择：________</div>"
    )


def _choice_options(question: TrainingQuestion, question_index: int) -> tuple[str, ...]:
    correct_index = CHOICE_LABELS.index(_choice_correct_label(question_index))
    distractors = _choice_distractors(question)
    options = list(distractors[:correct_index])
    options.append(question.answer)
    options.extend(distractors[correct_index:])
    return tuple(options[: len(CHOICE_LABELS)])


def _choice_correct_label(question_index: int) -> str:
    return CHOICE_LABELS[(question_index - 1) % len(CHOICE_LABELS)]


def _choice_distractors(question: TrainingQuestion) -> tuple[str, str, str]:
    return (
        f"只写出{question.target_reason}，不结合题目条件完成判断。",
        "忽略题目中的关键条件，直接套用结论。",
        "无法由题目条件判断，需要补充与本题无关的信息。",
    )


def _subject_source_photo_lines(
    clusters: tuple[AnalysisCluster, ...],
    photo_by_id: dict[str, SourcePhoto],
) -> str:
    photo_ids = _cluster_source_photo_ids(clusters)
    if not photo_ids:
        return "- 暂无明确照片来源。"
    lines = []
    for photo_id in photo_ids:
        photo = photo_by_id.get(photo_id)
        if photo is None:
            continue
        lines.append(
            f"- {photo.photo_id}：{photo.label_or_filename}，"
            f"学科置信度 {photo.confidence}，依据：{photo.evidence}"
        )
    return "\n".join(lines) if lines else "- 暂无明确照片来源。"


def _subject_source_photo_html_items(
    clusters: tuple[AnalysisCluster, ...],
    photo_by_id: dict[str, SourcePhoto],
) -> str:
    photo_ids = _cluster_source_photo_ids(clusters)
    if not photo_ids:
        return "<li>暂无明确照片来源。</li>"
    rows = []
    for photo_id in photo_ids:
        photo = photo_by_id.get(photo_id)
        if photo is None:
            continue
        rows.append(
            "<li>"
            f"{escape(photo.photo_id)}：{escape(photo.label_or_filename)}，"
            f"学科置信度 {escape(photo.confidence)}，依据：{escape(photo.evidence)}"
            "</li>"
        )
    return "\n".join(rows) if rows else "<li>暂无明确照片来源。</li>"


def _subject_cluster_knowledge_lines(
    clusters: tuple[AnalysisCluster, ...],
    photo_by_id: dict[str, SourcePhoto],
) -> str:
    if not clusters:
        return "- 暂无该学科训练内容。"
    lines = []
    for index, cluster in enumerate(clusters, start=1):
        diagnosis = cluster.diagnosis
        lines.extend(
            (
                f"### {index}. {cluster.problem_type}",
                "",
                f"- 照片：{_cluster_source_photo_text(cluster, photo_by_id)}",
                f"- 错因：{COLOR_LABELS.get(diagnosis.sticker_color, diagnosis.sticker_color)}，"
                f"{diagnosis.primary_reason}/{diagnosis.secondary_reason}",
                f"- 依据：{diagnosis.evidence}",
                f"- 知识点：{_subject_knowledge_links(cluster.matched_knowledge)}",
                f"- 训练建议：{COLOR_STRATEGIES.get(diagnosis.sticker_color, '先复述知识点，再完成同类训练。')}",
                f"- 难度梯度：{'/'.join(_difficulty_label(item) for item in cluster.difficulty_mix)}",
                "",
            )
        )
    return "\n".join(lines).strip()


def _subject_cluster_knowledge_cards(
    clusters: tuple[AnalysisCluster, ...],
    photo_by_id: dict[str, SourcePhoto],
) -> str:
    if not clusters:
        return "<p>暂无该学科训练内容。</p>"
    rows = []
    for index, cluster in enumerate(clusters, start=1):
        diagnosis = cluster.diagnosis
        rows.append(
            "<article class=\"knowledge-card\">"
            f"<h3>{index}. {escape(cluster.problem_type)}</h3>"
            "<div class=\"concept-grid\">"
            f"{_knowledge_diagram(cluster.problem_type)}"
            "<ul class=\"key-list\">"
            f"<li><strong>照片：</strong>{escape(_cluster_source_photo_text(cluster, photo_by_id))}</li>"
            f"<li><strong>错因：</strong>{escape(COLOR_LABELS.get(diagnosis.sticker_color, diagnosis.sticker_color))}，"
            f"{escape(diagnosis.primary_reason)}/{escape(diagnosis.secondary_reason)}</li>"
            f"<li><strong>依据：</strong>{escape(diagnosis.evidence)}</li>"
            f"<li><strong>知识点：</strong>{escape(_plain_knowledge_notes(cluster.matched_knowledge))}</li>"
            f"<li><strong>训练建议：</strong>{escape(COLOR_STRATEGIES.get(diagnosis.sticker_color, '先复述知识点，再完成同类训练。'))}</li>"
            f"<li><strong>难度梯度：</strong>{escape('/'.join(_difficulty_label(item) for item in cluster.difficulty_mix))}</li>"
            "</ul>"
            "</div>"
            "</article>"
        )
    return "\n".join(rows)


def _subject_knowledge_card_items(
    training: WrongQuestionTraining,
    subject: str,
) -> tuple[KnowledgeMatch, ...]:
    by_note: dict[str, KnowledgeMatch] = {}
    for cluster in training.clusters:
        if cluster.subject != subject:
            continue
        for match in cluster.matched_knowledge:
            note = match.note.strip()
            if (
                not note
                or match.is_pending
                or match.confidence.lower() == "low"
                or not _has_learning_order(match)
            ):
                continue
            by_note.setdefault(note, match)
    return tuple(sorted(by_note.values(), key=_knowledge_sort_key))


def _knowledge_focus_by_note(
    training: WrongQuestionTraining,
    subject: str,
) -> dict[str, tuple[str, ...]]:
    focus_by_note: dict[str, list[str]] = defaultdict(list)
    for cluster in training.clusters:
        if cluster.subject != subject:
            continue
        focus = _focus_tip_from_reason(cluster.diagnosis.secondary_reason)
        for match in cluster.matched_knowledge:
            note = match.note.strip()
            if (
                note
                and not match.is_pending
                and match.confidence.lower() != "low"
                and _has_learning_order(match)
                and focus not in focus_by_note[note]
            ):
                focus_by_note[note].append(focus)
    return {note: tuple(items) for note, items in focus_by_note.items()}


def _focus_tip_from_reason(reason: str) -> str:
    if reason in {"概念不清", "方法不会", "条件转化失败", "迁移失败"}:
        return "先复述定义和适用条件，再用图示或例子验证是否真正理解。"
    if reason in {"审题漏条件", "单位/符号错误", "步骤书写问题"}:
        return "先圈关键条件、单位和目标量，再按固定步骤写出关系式。"
    if reason in {"计算错误", "计算耗时"}:
        return "把可重复步骤压缩成固定顺序，先写核心关系，再代入数值。"
    if reason in {"读题慢", "路径选择慢", "卡在第一步", "时间分配不当"}:
        return "先判断属于哪类模型，再选择最短的标准解法路径。"
    return "先抓定义、条件和方法，再用一个小例子完成自检。"


def _has_learning_order(match: KnowledgeMatch) -> bool:
    return bool(_number_tuple(match.grade) and _number_tuple(match.chapter))


def _knowledge_sort_key(match: KnowledgeMatch) -> tuple:
    return (
        _first_number(match.grade),
        _volume_rank(match.volume),
        _number_tuple(match.chapter),
        _number_tuple(match.note),
        _knowledge_category_rank(match.note),
        match.note,
    )


def _first_number(text: str) -> int:
    numbers = _number_tuple(text)
    return numbers[0] if numbers else 999


def _number_tuple(text: str) -> tuple[int, ...]:
    numbers: list[int] = []
    for item in re.findall(r"\d+|[一二三四五六七八九十]+", text):
        if item.isdigit():
            numbers.append(int(item))
        else:
            numbers.append(_chinese_number(item))
    return tuple(numbers)


def _chinese_number(text: str) -> int:
    digits = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    return digits.get(text, 999)


def _volume_rank(volume: str) -> int:
    if "上" in volume:
        return 1
    if "下" in volume:
        return 2
    return 9


def _knowledge_category_rank(note: str) -> int:
    if any(word in note for word in ("结构", "构成", "元素", "概念", "种子", "根系")):
        return 1
    if any(word in note for word in ("性质", "密度", "质量", "公式", "化学式")):
        return 2
    if any(word in note for word in ("探究", "实验", "测量", "沸腾", "电解", "吸收")):
        return 3
    if any(word in note for word in ("图像", "图表", "推断", "计算", "判定")):
        return 4
    return 5


def _subject_knowledge_card_html(
    cards: tuple[KnowledgeMatch, ...],
    focus_by_note: Mapping[str, tuple[str, ...]],
    diagram_assets: Mapping[str, Path | str] | None,
) -> str:
    if not cards:
        return "<p>暂无已定位知识点。</p>"
    rows = []
    for index, match in enumerate(cards, start=1):
        body = _knowledge_card_body(match.note, focus_by_note.get(match.note, ()))
        has_image = _knowledge_card_asset(match.note, diagram_assets) is not None
        path_label = "图解提示" if has_image else "理解路径"
        path_text = (
            _knowledge_card_diagram_tip(match.note)
            if has_image
            else _knowledge_card_learning_path(match.note)
        )
        title = knowledge_card_display_title(match.note)
        rows.append(
            "<article class=\"knowledge-card\">"
            f"<h3>{escape(title)}</h3>"
            "<div class=\"concept-grid\">"
            f"{_knowledge_card_image(match.note, diagram_assets)}"
            "<div class=\"card-block\">"
            f"<strong>{path_label}：</strong>{escape(path_text)}"
            "</div>"
            "<div class=\"card-block\">"
            f"<strong>要点说明：</strong>{escape(body['core'])} "
            f"{escape(_join_chinese_clauses(body['must_remember']))}"
            "</div>"
            "<div class=\"card-block\">"
            f"<strong>注意事项：</strong>{escape(_join_chinese_clauses(body['pitfalls']))} "
            f"{escape(body['focus_tip'])}"
            "</div>"
            "<div class=\"card-block\">"
            f"<strong>速记技巧：</strong>{escape(_knowledge_card_memory_tip(match.note))} "
            f"{escape(body['self_check'])}"
            "</div>"
            "</div>"
            "</article>"
        )
    return "\n".join(rows)


def _knowledge_card_body(note: str, focus_tips: tuple[str, ...] = ()) -> dict[str, object]:
    focus_tip = _join_chinese_clauses(focus_tips) or "先抓定义、条件和方法，再用一个小例子完成自检。"
    if any(word in note for word in ("同位角", "内错角", "同旁内角")):
        return {
            "core": "两条直线被第三条直线所截时，会形成同位角、内错角和同旁内角三类位置关系。",
            "must_remember": (
                "先找截线，再找被截的两条直线。",
                "同位角在截线同侧且位置相同；内错角在两直线内侧且截线两侧；同旁内角在两直线内侧且截线同侧。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不先确定截线，角的位置关系就容易判断反。",),
            "self_check": "能否在一组平行线和截线图中快速圈出三类角？",
        }
    if "平行线" in note:
        return {
            "core": "平行线的性质用于由平行推出角相等或互补；判定用于由角关系推出两直线平行。",
            "must_remember": (
                "两直线平行，同位角相等、内错角相等、同旁内角互补。",
                "同位角相等、内错角相等或同旁内角互补，都可以判定两直线平行。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("性质和判定方向相反，不能把已知和结论写反。",),
            "self_check": "能否说清楚当前是在用性质，还是在用判定？",
        }
    if any(word in note for word in ("原子结构", "原子的构成")):
        return {
            "core": "原子由居于中心的原子核和核外电子构成，原子核由质子和中子构成。",
            "must_remember": (
                "质子带正电，电子带负电，中子不带电。",
                "普通原子中，质子数等于核外电子数，整体不显电性。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("原子核不是整个原子，电子在核外空间运动。",),
            "self_check": "能否画出原子核、质子、中子和电子的位置关系？",
        }
    if "相对分子质量" in note:
        return {
            "core": "相对分子质量等于化学式中各原子的相对原子质量总和。",
            "must_remember": (
                "计算时先数清每种原子的个数，再乘对应相对原子质量。",
                "元素质量比要用相对原子质量乘原子个数后再相比；质量分数要用该元素相对质量除以相对分子质量。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把原子个数比直接当成元素质量比，也不要把质量比写成质量分数。",),
            "self_check": "能否从H2O说出H:O的原子个数比、元素质量比和质量分数？",
        }
    if "化学式" in note:
        return {
            "core": "化学式表示物质的元素组成，也表示一个分子中的原子种类和个数。",
            "must_remember": (
                "元素质量比=相对原子质量乘原子个数后的比。",
                "元素质量分数=该元素相对质量总和/相对分子质量。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("物质由元素组成，分子由原子构成，二者不能混用。",),
            "self_check": "能否从一个化学式写出元素种类、原子个数比和质量分数？",
        }
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return {
            "core": "元素描述同一类原子的总称；分子、原子、离子是构成物质的微粒。",
            "must_remember": (
                "物质由元素组成，也可以由分子、原子或离子构成。",
                "分子由原子构成，原子得失电子形成离子；元素只讲种类，不讲个数。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把“元素组成物质”和“原子构成分子”写成同一层级关系。",),
            "self_check": "能否用一张包含关系图说出元素、原子、分子、离子和物质的关系？",
        }
    if "特殊情境下的密度计算" in note:
        return {
            "core": "特殊密度题要先分清研究对象，再分清总质量、总体积、空隙体积和实心体积。",
            "must_remember": (
                "平均密度=总质量/总体积，实心密度=实心部分质量/实心部分体积。",
                "多孔或空心物体常用V总=V实+V空；切割只会同比例改变质量和体积，密度不变。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把总体积、排水体积、空隙体积和实心体积混用。",),
            "self_check": "能否先列出m总、V总、V空、V实，再判断该用平均密度还是实心密度？",
        }
    if "测量石块和盐水的密度" in note:
        return {
            "core": "测量密度要分别获得同一对象的质量和体积，再用ρ=m/V计算。",
            "must_remember": (
                "石块体积常用排水法：V石=V2−V1。",
                "盐水质量常用差量法：m盐水=m1−m2，盐水体积读量筒。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把石块、烧杯、盐水的质量和体积混成同一个m或V。",),
            "self_check": "能否分别写出石块和盐水的m、V来自哪一步？",
        }
    if "密度" in note:
        return {
            "core": "密度表示单位体积物质的质量，公式为ρ=m/V。",
            "must_remember": (
                "质量、体积和密度必须统一单位。",
                "排水法中，排开水的体积等于浸没物体的体积。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不能把容器总质量、剩余质量和液体实际质量混在一起。",),
            "self_check": "能否先列出m、V、ρ分别来自哪里，再代入公式？",
        }
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return {
            "core": "汽化是液态变气态，液化是气态变液态；沸腾是液体内部和表面同时发生的剧烈汽化。",
            "must_remember": (
                "沸腾时继续吸热，但温度保持不变。",
                "水蒸气遇冷会液化，是否液化要看温度条件。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把蒸发、沸腾和液化的方向写反。",),
            "self_check": "能否用温度变化解释起雾、沸腾和冷却现象？",
        }
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return {
            "core": "物理变化不生成新物质，化学变化生成新物质；性质是物质在变化中表现出的特征。",
            "must_remember": (
                "外观、状态、密度、熔点、沸点、溶解性通常属于物理性质。",
                "可燃性、氧化性、还原性、酸碱反应等需要化学变化表现，属于化学性质。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("判断性质类别时，不看用途好不好，只看是否需要生成新物质来表现。",),
            "self_check": "能否把“呈红褐色、熔点高、不与水反应、可炼铁”分别归类？",
        }
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return {
            "core": "物质性质会受条件影响，探究时要控制变量，只改变一个研究因素。",
            "must_remember": (
                "设计对比实验时，除研究变量外，其他条件应保持相同。",
                "从图表读结论时，先看横轴变量，再看纵轴结果随变量如何变化。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不能只看最终大小，要同时说清楚变量、变化趋势和比较对象。",),
            "self_check": "能否用“变量-现象-结论”的句式描述一组探究实验？",
        }
    if any(word in note for word in ("种子", "萌发")):
        return {
            "core": "种子由种皮和胚等结构组成，胚是新植物体的幼体。",
            "must_remember": (
                "胚通常包括胚芽、胚轴、胚根和子叶；胚根先发育成根。",
                "种子萌发需要适量水分、充足空气和适宜温度。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("不要把子叶、胚乳和胚的各部分发育结果混淆。",),
            "self_check": "能否把胚芽、胚轴、胚根、子叶分别对应到发育结果？",
        }
    if any(word in note for word in ("细菌", "真菌")):
        return {
            "core": "细菌通常是单细胞、没有成形细胞核；真菌有成形细胞核，酵母菌是单细胞真菌。",
            "must_remember": (
                "细菌主要通过分裂繁殖，真菌多用孢子繁殖，酵母菌还可出芽生殖。",
                "比较微生物时，先看细胞结构，再看繁殖方式和生活条件。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("酵母菌不是细菌；有无成形细胞核是区分细菌和真菌的重要标准。",),
            "self_check": "能否说明细菌、大肠杆菌、酵母菌和曲霉的主要区别？",
        }
    if any(word in note for word in ("根", "茎", "植物")):
        return {
            "core": "根主要吸收水和无机盐，茎负责支持和运输，植物器官结构与功能相适应。",
            "must_remember": (
                "根尖成熟区有大量根毛，是吸水主要部位。",
                "形成层使茎长粗，筛管在韧皮部运输有机养料。",
            ),
            "focus_tip": focus_tip,
            "pitfalls": ("导管和筛管功能不同，木质部和韧皮部位置不能混淆。",),
            "self_check": "能否把根毛、形成层、导管、筛管分别对应到功能？",
        }
    return {
        "core": "先理解概念的定义、条件和适用范围，再记忆方法。",
        "must_remember": (
            "先说清楚概念是什么。",
            "再说清楚它和相近概念的区别。",
            "最后用一个简单例子检查是否真正理解。",
        ),
        "focus_tip": focus_tip,
        "pitfalls": ("只背名称、不知道使用条件，容易在综合应用中出错。",),
        "self_check": "能否不看材料，用自己的话解释这个知识点？",
    }


def _join_chinese_clauses(items: object) -> str:
    if isinstance(items, str):
        clauses = (items,)
    else:
        clauses = tuple(str(item) for item in items)
    cleaned = tuple(
        clause.strip().rstrip("。；;")
        for clause in clauses
        if clause and clause.strip()
    )
    if not cleaned:
        return ""
    return "；".join(cleaned) + "。"


def _knowledge_card_diagram_tip(note: str) -> str:
    if any(word in note for word in ("种子", "萌发")):
        return "看图时先找到胚根、胚芽、胚轴和子叶，再按萌发顺序对应到根、茎和叶。"
    if any(word in note for word in ("细菌", "真菌")):
        return "把细菌、酵母菌和霉菌并排比较，重点看有无成形细胞核和繁殖方式。"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "图中先分出原子核与核外电子，再把原子核放大看质子和中子。"
    if "化学式" in note or "相对分子质量" in note:
        return "从一个化学式出发，沿着元素种类、原子个数、质量比、质量分数四步看。"
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return "把元素、物质、分子、原子、离子放在不同层级，先区分“组成”和“构成”。"
    if "密度" in note:
        return "用质量m、体积V、密度ρ三角关系图记公式，再看排水法如何得到体积。"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "沿物态变化箭头看液态和气态的方向，再结合温度曲线判断沸腾和液化。"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "用左右对比图区分物理性质和化学性质，关键看是否需要生成新物质。"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "看图时先找横轴变量和纵轴现象，再用控制变量法读出结论。"
    if any(word in note for word in ("根", "茎", "植物")):
        return "把根毛、导管、筛管、形成层和功能连线，区分吸收、运输和长粗。"
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        return "先找截线，再看角在截线同侧还是两侧、在两条直线内侧还是外侧。"
    return "先看图中的关系箭头，再用自己的话复述每个节点的含义。"


def _knowledge_card_learning_path(note: str) -> str:
    if any(word in note for word in ("种子", "萌发")):
        return "先记胚的四个部分，再对应发育结果：胚根成根，胚芽成茎和叶。"
    if any(word in note for word in ("细菌", "真菌")):
        return "先按细胞结构区分细菌和真菌，再按繁殖方式比较分裂、出芽和孢子。"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "先分原子核和核外电子，再看原子核内的质子和中子。"
    if "化学式" in note or "相对分子质量" in note:
        return "先数原子个数，再乘相对原子质量，最后区分质量比和质量分数。"
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return "先分清组成和构成，再用层级关系说出元素、物质和微粒的关系。"
    if "密度" in note:
        return "先确认质量和体积属于同一对象，再统一单位代入ρ=m/V。"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "先判断物态变化方向，再结合温度条件解释是否发生沸腾或液化。"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "先判断是否生成新物质，再区分是在说变化过程还是物质性质。"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "先找唯一改变的变量，再把现象和结论用一句话连起来。"
    if any(word in note for word in ("根", "茎", "植物")):
        return "先把结构和功能一一对应，再区分吸收、运输和长粗。"
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        return "先找截线和被截直线，再判断角的位置关系或平行判定方向。"
    return "先说定义，再说条件和方法，最后用一个小例子自检。"


def _knowledge_card_memory_tip(note: str) -> str:
    if any(word in note for word in ("种子", "萌发")):
        return "胚根成根，胚芽成茎叶；萌发三条件是水、空气、适宜温度。"
    if any(word in note for word in ("细菌", "真菌")):
        return "细菌无成形核多分裂，真菌有成形核多孢子，酵母菌是真菌。"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "核内质子带正电，核外电子带负电；普通原子质子数等于电子数。"
    if "化学式" in note or "相对分子质量" in note:
        return "先数原子，再乘相对原子质量；质量分数等于该元素质量和除以相对分子质量。"
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return "元素讲种类，微粒讲构成；组成物质用元素，构成分子用原子。"
    if "密度" in note:
        return "ρ=m/V，先统一单位；排开多少水，就得到浸没部分多少体积。"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "汽化向气态，液化向液态；沸腾吸热但温度保持不变。"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "有新物质是化学变化；不经化学变化就能表现的是物理性质。"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "控制变量只改一个条件，读图结论用“变量变化，结果怎样变化”。"
    if any(word in note for word in ("根", "茎", "植物")):
        return "根毛吸水，导管运水，筛管运有机物，形成层让茎变粗。"
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        return "平行推出角关系叫性质，角关系推出平行叫判定。"
    return "定义、条件、方法、易混点按顺序复述一遍。"


def _knowledge_card_asset(
    note: str,
    diagram_assets: Mapping[str, Path | str] | None,
) -> str | None:
    if not diagram_assets:
        return None
    asset = diagram_assets.get(note)
    return str(asset) if asset is not None else None


def _knowledge_card_image(
    note: str,
    diagram_assets: Mapping[str, Path | str] | None,
) -> str:
    asset = _knowledge_card_asset(note, diagram_assets)
    if not asset:
        return ""
    src = Path(asset).expanduser().resolve().as_uri()
    title = knowledge_card_display_title(note)
    return (
        '<figure class="diagram">'
        f'<img src="{escape(src)}" alt="{escape(title)}" '
        'data-generator="gpt-image-2">'
        f"<figcaption>{escape(title)}</figcaption>"
        "</figure>"
    )


def _knowledge_card_diagram(note: str) -> str:
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="平行线角关系图">
  <path d="M22 36 H158 M22 92 H158 M60 16 L122 116" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M38 36 h18 M94 92 h18" stroke="#111" stroke-width="5"/>
  <text x="44" y="30" font-size="13">同位</text>
  <text x="96" y="86" font-size="13">内错</text>
  <text x="92" y="58" font-size="13">同旁内角互补</text>
</svg><div>先找截线，再判断角的位置。</div></div>"""
    if any(word in note for word in ("原子结构", "原子的构成")):
        return """<div class="diagram"><svg viewBox="0 0 180 140" role="img" aria-label="原子结构图">
  <circle cx="90" cy="66" r="18" fill="none" stroke="#111" stroke-width="3"/>
  <circle cx="82" cy="62" r="5" fill="#111"/><circle cx="98" cy="70" r="5" fill="#111"/>
  <ellipse cx="90" cy="66" rx="62" ry="36" fill="none" stroke="#111" stroke-width="2"/>
  <circle cx="35" cy="66" r="5" fill="none" stroke="#111" stroke-width="3"/>
  <circle cx="145" cy="66" r="5" fill="none" stroke="#111" stroke-width="3"/>
  <text x="90" y="118" text-anchor="middle" font-size="13">原子核：质子+中子</text>
  <text x="90" y="134" text-anchor="middle" font-size="13">核外：电子</text>
</svg><div>结构位置先记清，再记电性。</div></div>"""
    if "密度" in note:
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="密度关系图">
  <polygon points="90,22 34,108 146,108" fill="none" stroke="#111" stroke-width="3"/>
  <text x="90" y="54" text-anchor="middle" font-size="18">m</text>
  <text x="67" y="96" text-anchor="middle" font-size="18">rho</text>
  <text x="116" y="96" text-anchor="middle" font-size="18">V</text>
  <path d="M40 73 H140 M90 57 V106" stroke="#111" stroke-width="2"/>
</svg><div>rho = m / V，先找质量和体积。</div></div>"""
    if any(word in note for word in ("化学式", "相对分子质量")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="化学式层级图">
  <rect x="18" y="24" width="46" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="68" y="24" width="46" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="118" y="24" width="46" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M64 38 H68 M114 38 H118 M90 52 V92" stroke="#111" stroke-width="2"/>
  <text x="41" y="43" text-anchor="middle" font-size="13">元素</text>
  <text x="91" y="43" text-anchor="middle" font-size="13">原子</text>
  <text x="141" y="43" text-anchor="middle" font-size="13">分子</text>
  <text x="90" y="112" text-anchor="middle" font-size="13">个数比 -> 质量比 -> 质量分数</text>
</svg><div>先分层级，再做质量计算。</div></div>"""
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="物态变化图">
  <path d="M24 100 V24 M24 100 H154" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M28 90 C48 48 67 44 82 44 H146" fill="none" stroke="#111" stroke-width="3"/>
  <text x="90" y="38" text-anchor="middle" font-size="13">沸腾温度不变</text>
  <path d="M48 112 h84" stroke="#111" stroke-width="2"/>
  <text x="90" y="124" text-anchor="middle" font-size="12">遇冷液化，吸热汽化</text>
</svg><div>看状态变化方向和温度条件。</div></div>"""
    if any(word in note for word in ("根", "茎", "植物")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="植物运输结构图">
  <path d="M90 18 V108 M90 38 C58 34 48 50 32 62 M90 54 C122 50 132 66 148 78" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M78 108 C66 92 52 94 42 116 M102 108 C116 92 130 94 140 116" fill="none" stroke="#111" stroke-width="3"/>
  <text x="42" y="32" font-size="13">叶</text><text x="104" y="72" font-size="13">茎</text><text x="126" y="116" font-size="13">根毛</text>
</svg><div>根吸收，茎运输，结构对应功能。</div></div>"""
    return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="知识点学习流程图">
  <rect x="22" y="28" width="44" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="68" y="28" width="44" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="114" y="28" width="44" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M66 42 H68 M112 42 H114 M90 56 V94" stroke="#111" stroke-width="2"/>
  <text x="44" y="46" text-anchor="middle" font-size="12">定义</text>
  <text x="90" y="46" text-anchor="middle" font-size="12">关系</text>
  <text x="136" y="46" text-anchor="middle" font-size="12">应用</text>
  <text x="90" y="112" text-anchor="middle" font-size="13">先理解，再记忆，再自检</text>
</svg><div>按定义、关系、应用的顺序复习。</div></div>"""


def _subject_uncertain_html_items(
    uncertain_items: tuple[str, ...],
    subject: str,
    clusters: tuple[AnalysisCluster, ...],
) -> str:
    text = _subject_uncertain_lines(uncertain_items, subject, clusters)
    return "\n".join(
        f"<li>{escape(line.removeprefix('- ').strip())}</li>"
        for line in text.splitlines()
        if line.strip()
    )


def _knowledge_diagram(problem_type: str) -> str:
    if any(word in problem_type for word in ("密度", "体积", "溢水", "土壤", "圆柱", "冻豆腐", "洗手液")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="密度与排水法图示">
  <rect x="30" y="20" width="58" height="88" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M34 58 H84" stroke="#111" stroke-width="2"/>
  <circle cx="60" cy="84" r="16" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M105 38 h46 l-8 70 h-30 z" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M111 72 h34" stroke="#111" stroke-width="2"/>
  <text x="90" y="120" text-anchor="middle" font-size="15">rho = m / V</text>
</svg><div>先分清质量 m、体积 V、排开水体积。</div></div>"""
    if any(word in problem_type for word in ("物态", "沸腾", "露点", "分子")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="物态变化与分子运动图示">
  <path d="M25 105 V20 M25 105 H158" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M28 96 C55 35 70 35 86 35 H145" fill="none" stroke="#111" stroke-width="3"/>
  <circle cx="45" cy="78" r="5" fill="#111"/><circle cx="62" cy="70" r="5" fill="#111"/><circle cx="78" cy="82" r="5" fill="#111"/>
  <path d="M38 53 q20 -14 42 0" fill="none" stroke="#111" stroke-width="2"/>
  <text x="94" y="121" text-anchor="middle" font-size="14">温度-时间图像 + 分子间隙</text>
</svg><div>沸腾温度不变；液化看露点；界面模糊看分子运动。</div></div>"""
    if "电解" in problem_type:
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="电解水实验图示">
  <rect x="38" y="22" width="34" height="78" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="108" y="48" width="34" height="52" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M25 100 H155" stroke="#111" stroke-width="3"/>
  <text x="55" y="18" text-anchor="middle" font-size="14">H2 2份</text>
  <text x="125" y="44" text-anchor="middle" font-size="14">O2 1份</text>
  <text x="90" y="121" text-anchor="middle" font-size="14">体积比 H2:O2 = 2:1</text>
</svg><div>先认电极气体，再判断图像斜率和最终体积。</div></div>"""
    if "化学式" in problem_type:
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="化学式意义图示">
  <circle cx="48" cy="54" r="18" fill="none" stroke="#111" stroke-width="3"/><text x="48" y="59" text-anchor="middle" font-size="16">C</text>
  <circle cx="88" cy="39" r="12" fill="none" stroke="#111" stroke-width="3"/><text x="88" y="44" text-anchor="middle" font-size="13">H</text>
  <circle cx="122" cy="65" r="15" fill="none" stroke="#111" stroke-width="3"/><text x="122" y="70" text-anchor="middle" font-size="15">O</text>
  <path d="M65 49 L77 42 M101 48 L110 58" stroke="#111" stroke-width="2"/>
  <text x="90" y="111" text-anchor="middle" font-size="14">原子个数比 -> 质量比 -> 质量分数</text>
</svg><div>元素、原子、分子、质量比不能混用。</div></div>"""
    if any(word in problem_type for word in ("性质", "材料", "合金", "熔点")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="物质性质判断图示">
  <rect x="25" y="24" width="130" height="70" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M90 24 V94 M25 56 H155" stroke="#111" stroke-width="2"/>
  <text x="57" y="46" text-anchor="middle" font-size="14">物理性质</text>
  <text x="123" y="46" text-anchor="middle" font-size="14">化学性质</text>
  <text x="57" y="78" text-anchor="middle" font-size="12">颜色/熔点</text>
  <text x="123" y="78" text-anchor="middle" font-size="12">反应/炼铁</text>
</svg><div>不生成新物质的是物理性质；反应能力是化学性质。</div></div>"""
    if any(word in problem_type for word in ("植物", "根", "茎", "生殖", "种子")):
        return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="植物结构图示">
  <path d="M90 28 C76 52 76 78 90 101 C104 78 104 52 90 28 Z" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M90 101 V116 M90 73 H58 M90 73 H122 M90 52 H65 M90 52 H115" stroke="#111" stroke-width="3"/>
  <circle cx="90" cy="24" r="10" fill="none" stroke="#111" stroke-width="3"/>
  <text x="90" y="126" text-anchor="middle" font-size="14">根吸水；茎运输；花果种子有来源</text>
</svg><div>结构名称、发育来源和生殖方式分开记。</div></div>"""
    return """<div class="diagram"><svg viewBox="0 0 180 130" role="img" aria-label="错因分析流程图">
  <rect x="24" y="28" width="48" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="108" y="28" width="48" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <rect x="66" y="82" width="48" height="28" fill="none" stroke="#111" stroke-width="3"/>
  <path d="M72 42 H106 M90 56 V80" fill="none" stroke="#111" stroke-width="2"/>
  <text x="90" y="123" text-anchor="middle" font-size="14">条件 -> 知识点 -> 方法</text>
</svg><div>先找条件，再匹配知识点和题型方法。</div></div>"""


def _subject_uncertain_lines(
    uncertain_items: tuple[str, ...],
    subject: str,
    clusters: tuple[AnalysisCluster, ...],
) -> str:
    photo_ids = set(_cluster_source_photo_ids(clusters))
    lines = [
        item
        for item in uncertain_items
        if subject in item or any(photo_id in item for photo_id in photo_ids)
    ]
    return "\n".join(f"- {item}" for item in lines) if lines else "- 暂无。"


def _cluster_source_photo_ids(clusters: tuple[AnalysisCluster, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    for cluster in clusters:
        for photo_id in cluster.source_photo_ids:
            if photo_id not in ordered:
                ordered.append(photo_id)
    return tuple(ordered)


def _cluster_source_photo_text(
    cluster: AnalysisCluster,
    photo_by_id: dict[str, SourcePhoto],
) -> str:
    labels = []
    for photo_id in cluster.source_photo_ids:
        photo = photo_by_id.get(photo_id)
        labels.append(photo.label_or_filename if photo else photo_id)
    return "；".join(labels) if labels else "未记录"


def _subject_knowledge_links(matches: tuple[KnowledgeMatch, ...]) -> str:
    return "；".join(_md_link(match.note) for match in matches) or "[[待定位]]"


def _weekly_knowledge_counts(clusters: tuple[AnalysisCluster, ...]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for cluster in clusters:
        for note in _plain_knowledge_note_list(cluster.matched_knowledge):
            counts[note] += 1
    return counts


def _weekly_repeated_knowledge_lines(counts: Counter[str]) -> str:
    repeated = [
        (note, count)
        for note, count in counts.most_common()
        if count >= 2
    ]
    if not repeated:
        return "- 暂无重复 2 次以上的知识点。"
    return "\n".join(
        f"- {_md_link(note)}：出现 {count} 次，优先复测。"
        for note, count in repeated
    )


def _weekly_secondary_reason_lines(counts: Counter[str]) -> str:
    if not counts:
        return "- 暂无二级错因记录。"
    return "\n".join(
        f"- {reason}：{count} 次"
        for reason, count in counts.most_common(5)
    )


def _weekly_difficulty_fit_lines(results: tuple[TrainingResult, ...]) -> str:
    if not results:
        return "- 暂无训练结果，先按标准难度观察。"
    lines = []
    for result in results:
        fit = _difficulty_fit(result)
        lines.append(
            f"- {result.date} {_md_link(result.knowledge_note)}："
            f"{_difficulty_label(result.difficulty)}，正确率 {result.correct_rate:.0%}，"
            f"用时 {result.elapsed_minutes}/{result.target_minutes} 分钟，{fit}。"
        )
    return "\n".join(lines)


def _weekly_review_queue_lines(results: tuple[TrainingResult, ...]) -> str:
    if not results:
        return "- 暂无到期复测。"
    return "\n".join(
        f"- {result.due_date} {result.review_window}：{_md_link(result.knowledge_note)}，"
        f"{result.secondary_reason}，{result.review_result or '待复测'}。"
        for result in results
    )


def _weekly_priority_lines(
    clusters: tuple[AnalysisCluster, ...],
    results: tuple[TrainingResult, ...],
    review_queue: tuple[TrainingResult, ...],
) -> str:
    priorities = []
    if review_queue:
        priorities.append("先完成到期复测队列，尤其是 D+7 项目。")
    repeated_notes = [
        note
        for note, count in _weekly_knowledge_counts(clusters).items()
        if count >= 2
    ]
    if repeated_notes:
        priorities.append(f"重复知识点优先：{'；'.join(repeated_notes)}。")
    slow = [
        result.knowledge_note
        for result in results
        if result.elapsed_minutes > result.target_minutes
    ]
    if slow:
        priorities.append(f"限时训练继续跟踪：{'；'.join(dict.fromkeys(slow))}。")
    if not priorities:
        priorities.append("保持标准题稳定率，再逐步加入变式题。")
    return "\n".join(f"- {item}" for item in priorities)


def _weekly_review_queue_tasks(results: tuple[TrainingResult, ...]) -> str:
    if not results:
        return "<p>暂无到期复测。</p>"
    rows = []
    for result in results:
        rows.append(
            "<li>"
            f"{escape(result.subject)} {_knowledge_text_from_note(result.knowledge_note)}："
            f"{escape(result.problem_type)}，{escape(result.review_window)}，"
            f"目标 {result.target_minutes} 分钟内完成 1 组"
            f"{escape(_difficulty_label(result.next_difficulty))}复测题。"
            "</li>"
        )
    return f"<ol class=\"task-list\">{''.join(rows)}</ol>"


def _weekly_review_queue_answers(results: tuple[TrainingResult, ...]) -> str:
    if not results:
        return "<p>暂无复测答案参考。</p>"
    rows = []
    for result in results:
        rows.append(
            "<li>"
            f"<p>{escape(result.subject)} {_knowledge_text_from_note(result.knowledge_note)}："
            f"{escape(result.problem_type)}</p>"
            f"<p><strong>答案参考：</strong>"
            f"按本知识点核心步骤复测，重点核对："
            f"{escape(result.major_error or result.secondary_reason)}。</p>"
            f"<p><strong>评分点：</strong>正确率达到 {result.correct_rate:.0%} 以上、"
            f"目标时间 {result.target_minutes} 分钟内完成、错因不重复。</p>"
            f"<p><strong>掌握判断：</strong>"
            f"{escape(result.review_result or result.status)}</p>"
            f"<p><strong>下一次难度建议：</strong>"
            f"{escape(_difficulty_label(result.next_difficulty))}</p>"
            "</li>"
        )
    return f"<ol class=\"task-list\">{''.join(rows)}</ol>"


def _difficulty_fit(result: TrainingResult) -> str:
    if result.correct_rate < 0.75:
        return "过难，下一次降到基础或保持当前难度"
    if result.correct_rate >= 0.9 and result.elapsed_minutes <= result.target_minutes:
        return "偏易或已掌握，下一次可升难度"
    if result.elapsed_minutes > result.target_minutes:
        return "正确率可用但用时偏长，难度合适但需要限时"
    return "难度合适"


def _next_difficulty_suggestion(difficulty: str) -> str:
    order = ("basic", "standard", "variant", "challenge")
    try:
        index = order.index(difficulty)
    except ValueError:
        return "保持当前难度"
    next_index = min(index + 1, len(order) - 1)
    return (
        f"达成掌握判断后升到{DIFFICULTY_LABELS[order[next_index]]}；"
        f"未达成则保持{DIFFICULTY_LABELS[order[index]]}。"
    )


def _difficulty_label(difficulty: str) -> str:
    return DIFFICULTY_LABELS.get(difficulty, difficulty)


def _plain_knowledge_notes(matches: tuple[KnowledgeMatch, ...]) -> str:
    return "；".join(_plain_knowledge_note_list(matches)) or "待定位"


def _plain_knowledge_note_list(matches: tuple[KnowledgeMatch, ...]) -> list[str]:
    return [match.note for match in matches] or ["待定位"]


def _knowledge_text_from_note(note: str) -> str:
    return escape(note or "待定位")


def _md_link(note: str) -> str:
    return "[[待定位]]" if note == "待定位" else f"[[{note}]]"
