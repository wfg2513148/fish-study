from __future__ import annotations

from collections import Counter
from html import escape

from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    KnowledgeMatch,
    SourcePhoto,
    TrainingQuestion,
    TrainingResult,
    WeeklyReviewSource,
    WrongQuestionTraining,
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


def _html_document(title: str, body: str) -> str:
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
<div class="seal">学校 班级 姓名 考号 密封线内不要答题</div>
{body.strip()}
</main>
</body>
</html>
"""


def _training_student_clusters(clusters: tuple[AnalysisCluster, ...]) -> str:
    rows = []
    question_index = 1
    for index, cluster in enumerate(clusters, start=1):
        rows.append(
            "<article>"
            f"<h3>{index}. {_training_group_title(cluster)}</h3>"
            f"<p class=\"knowledge\">补救：{_knowledge_repair_text(cluster)}</p>"
            f"<ol class=\"task-list\">"
            f"{_training_question_prompts(cluster.training_questions, start_index=question_index)}</ol>"
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


def _training_question_prompts(
    questions: tuple[TrainingQuestion, ...],
    start_index: int = 1,
) -> str:
    rows = []
    for index, question in enumerate(questions, start=start_index):
        rows.append(
            "<li class=\"question\">"
            f"<span class=\"points\">第 {index} 题</span> "
            f"<span class=\"tag\">难度："
            f"{escape(_difficulty_label(question.difficulty))}</span>"
            f"{escape(question.prompt)}"
            "<div class=\"answer-box\"></div>"
            "</li>"
        )
    return "\n".join(rows)


def _training_answer_clusters(clusters: tuple[AnalysisCluster, ...]) -> str:
    rows = []
    for index, cluster in enumerate(clusters, start=1):
        rows.append(
            "<article>"
            f"<h3>{index}. {_training_group_title(cluster)}</h3>"
            f"<ol class=\"task-list\">"
            f"{_training_question_answers(cluster.training_questions)}</ol>"
            "</article>"
        )
    return "\n".join(rows) if rows else "<p>暂无答案。</p>"


def _training_question_answers(questions: tuple[TrainingQuestion, ...]) -> str:
    rows = []
    for question in questions:
        rows.append(
            "<li>"
            f"<p><span class=\"tag\">难度："
            f"{escape(_difficulty_label(question.difficulty))}</span>"
            f"{escape(question.prompt)}</p>"
            f"<p><strong>答案：</strong>{escape(question.answer)}</p>"
            f"<p><strong>评分点：</strong>"
            f"{escape('；'.join(question.scoring_points) or '按关键步骤给分')}</p>"
            f"<p><strong>掌握判断：</strong>{escape(question.mastery_signal)}</p>"
            f"<p><strong>下一次难度建议：</strong>"
            f"{escape(_next_difficulty_suggestion(question.difficulty))}</p>"
            "</li>"
        )
    return "\n".join(rows)


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
