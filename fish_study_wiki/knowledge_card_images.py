from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
import subprocess

from fish_study_wiki.models import safe_markdown_filename
from fish_study_wiki.study_protocol_models import WrongQuestionTraining
from fish_study_wiki.study_protocol_render import (
    knowledge_card_display_title,
    knowledge_card_matches,
    knowledge_card_needs_diagram,
)


GPT_IMAGE_SCRIPT = Path.home() / ".codex/skills/gpt-image-2/scripts/generate-image.sh"


def prepare_knowledge_card_diagrams(
    training: WrongQuestionTraining,
    subject: str,
    output_dir: Path,
) -> dict[str, Path]:
    cards = knowledge_card_matches(training, subject)
    asset_dir = output_dir / "knowledge-card-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets: dict[str, Path] = {}
    manifest: list[dict[str, str]] = []
    for index, match in enumerate(cards, start=1):
        spec = _knowledge_card_diagram_spec(match.note)
        if spec["status"] == "omit":
            manifest.append(
                {
                    "note": match.note,
                    "title": knowledge_card_display_title(match.note),
                    "status": "omit",
                    "reason": spec["reason"],
                }
            )
            continue
        path = asset_dir / _asset_filename(subject, index, match.note)
        if not _usable_image(path):
            _generate_gpt_image(_knowledge_card_image_prompt(subject, match.note, spec), path)
        assets[match.note] = path
        manifest.append(
            {
                "note": match.note,
                "title": knowledge_card_display_title(match.note),
                "status": spec["status"],
                "reason": spec["reason"],
                "asset": str(path),
                "visual_goal": spec["visual_goal"],
            }
        )
    (asset_dir / "generation-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return assets


def _asset_filename(subject: str, index: int, note: str) -> str:
    slug = safe_markdown_filename(note).removesuffix(".md")
    digest = sha1(f"{subject}:{note}".encode("utf-8")).hexdigest()[:8]
    return f"{index:02d}-{slug}-{digest}.png"


def _usable_image(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 4096


def _generate_gpt_image(prompt: str, output_path: Path) -> None:
    if not GPT_IMAGE_SCRIPT.exists():
        raise RuntimeError(f"gpt-image-2 script not found: {GPT_IMAGE_SCRIPT}")
    subprocess.run(
        [str(GPT_IMAGE_SCRIPT), prompt, str(output_path), "1536x1024"],
        check=True,
        text=True,
    )
    if not _usable_image(output_path):
        raise RuntimeError(f"gpt-image-2 output is missing or too small: {output_path}")


def _knowledge_card_diagram_spec(note: str) -> dict[str, str]:
    if not knowledge_card_needs_diagram(note):
        return {
            "status": "omit",
            "reason": "知识点以文字规则记忆为主，配图不会明显提升理解。",
            "visual_goal": "",
            "must_show": "",
            "must_not_show": "",
            "allowed_labels": "",
            "common_misconception": "",
        }
    return {
        "status": "required",
        "reason": "知识点包含结构、过程、关系、实验或变量，图解能帮助快速回忆。",
        "visual_goal": _prompt_focus(note),
        "must_show": _prompt_must_show(note),
        "must_not_show": (
            "章节节次课时专题编号；题号；原题选项；照片来源；错因诊断；"
            "装饰背景；无关卡通元素；与知识关系不符的箭头或符号"
        ),
        "allowed_labels": _prompt_labels(note),
        "common_misconception": _prompt_common_misconception(note),
    }


def _knowledge_card_image_prompt(subject: str, note: str, spec: dict[str, str]) -> str:
    title = knowledge_card_display_title(note)
    return (
        "Wide horizontal 3:2 black and white formal junior middle school "
        "knowledge-card diagram, filling most of the page width, minimal empty "
        f"margins. Subject: {subject}. Knowledge point: {title}. "
        "Create a clear, vivid, textbook-style explanatory image for this "
        "knowledge point only, not a generic poster. "
        f"Visual goal: {spec['visual_goal']} "
        f"Must show: {spec['must_show']} "
        f"Common misconception to prevent: {spec['common_misconception']} "
        f"Use only these Chinese labels if labels are needed: {spec['allowed_labels']}. "
        f"Must not show: {spec['must_not_show']}. "
        "Do not write chapter, section, lesson, textbook unit labels, or strings "
        "like 第1章, 第3节, 第2课时, 专题11 in the image. "
        "Do not include question numbers, source photo references, stickers, "
        "diagnosis words, answer options, extra explanations, watermark, or "
        "decorative background."
    )


def _prompt_focus(note: str) -> str:
    if "平行线的性质与判定" in note:
        return (
            "Show two parallel lines cut by one transversal. On the left, show "
            "the properties from parallel lines to angle relationships. On the "
            "right, show the reverse judgement from angle relationships to "
            "parallel lines. Clearly separate equality and supplementary "
            "relationships with simple arrows. For same-side interior angles, "
            "show the sum as 180 degrees or complementary; never use a not-equal "
            "symbol for that relationship."
        )
    if any(word in note for word in ("同位角", "内错角", "同旁内角")):
        return (
            "Show two parallel lines cut by one transversal, with one clean "
            "example each for corresponding angles, alternate interior angles, "
            "and same-side interior angles."
        )
    if any(word in note for word in ("原子结构", "原子的构成")):
        return (
            "Show one atom overview and one enlarged nucleus view, making the "
            "positions of protons, neutrons, and electrons easy to compare."
        )
    if any(word in note for word in ("种子", "萌发")):
        return (
            "Show a seed cutaway with embryo parts, then a simple germination "
            "sequence where radicle grows into the root and plumule grows into "
            "stem and leaves. Keep it concrete and botanical."
        )
    if any(word in note for word in ("细菌", "真菌")):
        return (
            "Show a three-column comparison of bacterium, yeast, and mold. Make "
            "cell nucleus presence and reproduction style visually clear with "
            "simple icons, not long prose."
        )
    if "密度" in note:
        return (
            "Show the mass-volume-density relationship and a water displacement "
            "setup side by side, with arrows showing how volume is obtained."
        )
    if any(word in note for word in ("化学式", "相对分子质量")):
        return (
            "Show one chemical formula flowing into element types, atom counts, "
            "relative mass calculation, and mass fraction. Use a clean relation "
            "diagram rather than decorative molecules."
        )
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return (
            "Show a hierarchy and relation map: matter is composed of elements "
            "and may be made of molecules, atoms, or ions; molecules are made "
            "of atoms; atoms can form ions by gaining or losing electrons."
        )
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return (
            "Show liquid-to-gas and gas-to-liquid arrows with a boiling beaker "
            "and a cooling surface. Include a simple temperature-time plateau "
            "to show boiling temperature stays constant."
        )
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return (
            "Show a left-right comparison: physical change or property without "
            "new substance, chemical change or property with new substance. "
            "Use concrete examples and a clear decision arrow."
        )
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return (
            "Show a controlled-variable experiment layout with only one changed "
            "condition and a small trend chart, emphasizing variable, observed "
            "phenomenon, and conclusion."
        )
    if any(word in note for word in ("根", "茎", "植物")):
        return (
            "Show root hair absorption and a stem cross-section with xylem, "
            "phloem, and cambium connected to their functions."
        )
    return "Focus on the concept structure, key relationship, and one visual cue that helps recall the method."


def _prompt_must_show(note: str) -> str:
    if "平行线的性质与判定" in note:
        return "两条平行线、一条截线、角相等关系、同旁内角和为180度、性质与判定双向箭头"
    if any(word in note for word in ("同位角", "内错角", "同旁内角")):
        return "两条直线、一条截线、三类角的位置对比"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "原子核、核外电子、质子、中子、带电状态"
    if any(word in note for word in ("种子", "萌发")):
        return "种皮、胚根、胚芽、胚轴、子叶、萌发后的根和茎叶"
    if any(word in note for word in ("细菌", "真菌")):
        return "细菌、酵母菌、霉菌、成形细胞核差异、分裂和孢子繁殖"
    if "密度" in note:
        return "质量m、体积V、密度rho、排水法得到体积"
    if any(word in note for word in ("化学式", "相对分子质量")):
        return "化学式、元素种类、原子个数、相对质量、质量分数"
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return "物质、元素、分子、原子、离子的层级和组成构成关系"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "液态到气态、气态到液态、沸腾烧杯、温度时间平台"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "物理变化或性质、化学变化或性质、新物质判断"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "控制变量实验、唯一改变条件、变量现象结论、趋势图"
    if any(word in note for word in ("根", "茎", "植物")):
        return "根毛、茎横切面、导管、筛管、形成层和功能连线"
    return "概念节点、关键关系、一个帮助回忆的视觉线索"


def _prompt_common_misconception(note: str) -> str:
    if any(word in note for word in ("种子", "萌发")):
        return "不要把子叶、胚乳、胚根和胚芽的发育结果混淆"
    if any(word in note for word in ("细菌", "真菌")):
        return "不要把酵母菌当作细菌，也不要忽略成形细胞核"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "不要把原子核画成整个原子，也不要把电子放进原子核"
    if "密度" in note:
        return "不要把容器质量、液体质量和排开体积混为一谈"
    if any(word in note for word in ("化学式", "相对分子质量")):
        return "不要把元素质量比和原子个数比直接等同"
    if any(word in note for word in ("分子", "原子", "离子", "元素")):
        return "不要混用组成物质的元素和构成物质的微粒"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "不要把汽化和液化方向写反，也不要认为沸腾时温度继续升高"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "不要用用途判断物理或化学性质，要看是否需要生成新物质"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "不要同时改变多个条件，也不要只看最终大小忽略变量"
    if any(word in note for word in ("根", "茎", "植物")):
        return "不要混淆导管和筛管，也不要把形成层位置画错"
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        return "不要没找截线就判断角关系，也不要混淆性质和判定方向"
    return "不要只画概念名，必须画出关系和使用条件"


def _prompt_labels(note: str) -> str:
    if any(word in note for word in ("同位角", "内错角", "同旁内角", "平行线")):
        if "平行线的性质与判定" in note:
            return "平行线、截线、同位角相等、内错角相等、同旁内角和为180度、判定"
        return "截线、平行线、同位角、内错角、同旁内角"
    if any(word in note for word in ("原子结构", "原子的构成")):
        return "原子核、质子、中子、电子"
    if any(word in note for word in ("种子", "萌发")):
        return "种皮、胚根、胚芽、胚轴、子叶、根、茎叶"
    if any(word in note for word in ("细菌", "真菌")):
        return "细菌、酵母菌、霉菌、成形细胞核、分裂、孢子"
    if "密度" in note:
        return "质量m、体积V、密度rho"
    if any(word in note for word in ("化学式", "相对分子质量")):
        return "元素、原子、分子、质量分数"
    if any(word in note for word in ("沸腾", "汽化", "液化")):
        return "温度、时间、沸腾、液化"
    if any(word in note for word in ("根", "茎", "植物")):
        return "根毛、导管、筛管、形成层"
    if any(word in note for word in ("变化与性质", "物质的变化")):
        return "物理性质、化学性质、新物质"
    if any(word in note for word in ("温度对物质性质", "探索物质变化", "性质的方法")):
        return "变量、现象、结论"
    return "定义、关系、方法"
