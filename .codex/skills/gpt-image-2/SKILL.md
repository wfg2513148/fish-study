---
name: gpt-image-2
description: Generate images via OpenAI gpt-image-2 through Hermes openai-codex OAuth. No OpenAI API key or Cockpit Tools required.
triggers:
  - 需要生成图片/头像/插图
  - gpt-image-2 模型调用
  - Codex OAuth 图片生成
  - 飞书机器人头像、漫画单格、创意图片
---

# gpt-image-2 Image Generation

Generate images with `gpt-image-2` through the local Hermes `openai-codex`
image provider. This route uses the existing Codex/ChatGPT OAuth login and
does not require `OPENAI_API_KEY`.

## Active Route

- **Provider**: Hermes `image_gen/openai-codex`
- **Model**: `gpt-image-2`
- **Auth**: Codex/ChatGPT OAuth read by Hermes
- **Runtime Python**: `~/.hermes/hermes-agent/venv/bin/python`
- **Output cache**: `~/.hermes/cache/images/`

Do not start or depend on Cockpit Tools. The old
`~/.antigravity_cockpit/codex_local_access.json` / `127.0.0.1:64032` route is
deprecated for this host.

## Reusable Script

```bash
~/.codex/skills/gpt-image-2/scripts/generate-image.sh \
  "formal black and white exam diagram" \
  /tmp/generated-image.png \
  1536x1024
```

The third argument accepts `1536x1024`, `1024x1024`, or `1024x1536` and maps to
Hermes aspect ratios `landscape`, `square`, or `portrait`.

## Exam Figure Rules

For worksheet, exam, textbook, or study-paper diagrams, default to wide figures
that remain readable after PDF printing:

- Use `1536x1024` unless the user explicitly requests a portrait image.
- Start prompts with `Wide horizontal 3:2 black and white formal exam diagram`.
- Add `filling most of the page width` and `minimal empty margins`.
- Prefer letter labels such as `A B C D` over long generated text inside the
  image.
- When reconstructing a figure from a source photo, do not ask the model to
  redesign the diagram. The prompt must lock the source figure's object count,
  grouping, labels, data values, axis names, relative positions, and
  experiment-control relationships.
- Do not add text that was not present in the original figure. If the original
  figure has Chinese labels, keep those labels in Chinese and do not translate
  or paraphrase them.
- Only optimize line clarity, print contrast, alignment, and A4 readability.
  Never simplify away key details, such as controlled-experiment groups,
  repeated objects, table values, scale marks, or graph series.
- Avoid portrait compositions for microscopes, plants, soil profiles, maps,
  charts, and experimental apparatus. If the subject is naturally tall, place it
  diagonally, use an inset, or spread the structure across a landscape canvas.
- After placing figures in HTML/PDF, run a rendered-width check. No routine exam
  figure should render below about 300px wide in the browser preview unless it is
  intentionally a small icon.

## Model Tier

Set `OPENAI_IMAGE_MODEL` only when a specific tier is needed:

```bash
OPENAI_IMAGE_MODEL=gpt-image-2-high \
  ~/.codex/skills/gpt-image-2/scripts/generate-image.sh "prompt" /tmp/out.png
```

Supported tiers are:

| Tier | Quality |
| --- | --- |
| `gpt-image-2-low` | Low |
| `gpt-image-2-medium` | Medium, default |
| `gpt-image-2-high` | High |

## Verification

After generation, inspect the saved file with a vision check before delivery:
confirm the requested style, core semantic elements, legibility, crop, and that
there is no unwanted text or watermark.
