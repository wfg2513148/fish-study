# AI 安装配置说明

这份说明写给接手 Fish Study 的 AI 或工程协作者。目标是在另一台机器上快速装好项目、Codex skill、外部工具和本地资料目录，避免只克隆仓库但无法生成训练卷、PDF 或模拟卷。

## 0. 安装边界和成功标准

本说明面向“把 Fish Study 搬到另一台 macOS 机器，由 AI 或工程协作者恢复可运行环境”。

成功标准：

- Fish Study CLI 可运行：`study-context`、`verify`、`pytest` 通过。
- Obsidian vault 写入当前机器指定路径，不写回旧机器路径。
- `fish-study-photo-workflow`、`fish-study-exam-paper` 和 `gpt-image-2` 在 Codex 会话中可用。
- Playwright 可导出带嵌图和页脚页码的 PDF。
- 原始 ZIP、PDF、课件和扫描图只保存在本机，不提交 Git。

## 目标状态

安装完成后，另一台机器应能做到：

1. 运行 Fish Study CLI：
   - `python3 -m fish_study_wiki.cli study-context`
   - `python3 -m fish_study_wiki.cli verify`
2. 生成日常错题训练卷和周复盘材料。
3. 使用 Codex Desktop/CLI 读取当前知识库上下文。
4. 使用项目 skill 生成真实试卷式模拟卷。
5. 使用 `gpt-image-2` 生成试卷配图。
6. 使用 Playwright 导出嵌图 PDF，并检查页码、图片和移动端体积。
7. 用 Markdown 绝对路径文件链接把本地 PDF 发到 Codex 会话中。

## 机器前提

优先按 macOS 配置。当前项目路径和 Obsidian 路径已支持环境变量覆盖。

推荐环境：

| 组件 | 用途 | 验证命令 |
|---|---|---|
| Git | 拉取仓库、提交发布 | `git --version` |
| Python 3.11+ | 运行项目 CLI 和测试 | `python3 --version` |
| Node.js 20+ / npm | Playwright PDF 和视觉检查 | `node --version` / `npm --version` |
| Codex CLI/Desktop | 照片理解、AI 生成、OAuth 调 GPT | `codex --version` |
| Obsidian | 查看长期知识库 | 手动打开 vault |
| GitHub CLI | 发布版本时使用 | `gh --version` |
| `sips` / `qlmanage` | macOS 图片/PDF 预览检查 | `which sips` / `which qlmanage` |

当前 Codex 登录方式使用宿主机 OAuth，不要求额外配置 `OPENAI_API_KEY`。

## 第 1 步：克隆仓库

```bash
git clone https://github.com/wfg2513148/fish-study.git
cd fish-study
```

如果仓库已经存在：

```bash
cd /path/to/fish-study
git pull --ff-only
```

## 第 2 步：配置路径

默认路径：

```text
项目仓库：当前 git clone 目录
Obsidian vault：$HOME/Downloads/obsidian/fish-study
```

如需改路径，设置环境变量：

```bash
export FISH_STUDY_REPO_ROOT="/path/to/fish-study"
export FISH_STUDY_VAULT_ROOT="$HOME/Downloads/obsidian/fish-study"
```

建议写入 shell 配置：

```bash
cat >> ~/.zshrc <<'EOF'
export FISH_STUDY_REPO_ROOT="$HOME/fish-study"
export FISH_STUDY_VAULT_ROOT="$HOME/Downloads/obsidian/fish-study"
EOF
```

设置路径后，立即验证 Python 实际读取的路径：

```bash
python3 - <<'PY'
from fish_study_wiki import settings
print("REPO_ROOT =", settings.REPO_ROOT)
print("VAULT_ROOT =", settings.VAULT_ROOT)
PY
```

`data/sources/source-ledger.json` 中的 `local_path` 使用相对路径时，会按 `FISH_STUDY_REPO_ROOT` 解析；如果某条记录仍是旧机器绝对路径，必须改成当前机器路径，否则 `verify` 会报 source file not found。

## 第 3 步：运行安装准备和自检脚本

```bash
scripts/setup_ai_machine.sh
```

这个脚本不是纯只读检查。它会做这些事：

- 创建 `sources/raw/`、`sources/extracted/`、`outputs/` 和 Obsidian vault 目录。
- 把项目 skill 安装到 `~/.codex/skills/fish-study-exam-paper/SKILL.md`。
- 检查 `python3`、`node`、`npm`、`codex`、`git`、`curl`、`shasum`。
- 在 macOS 上检查 `sips` 和 `qlmanage`。
- 检查 Python 模块 `pypdf`。
- 检查 Node 模块 `playwright`。

如果脚本输出 `WARN`，按提示补装。

## 第 4 步：安装项目外依赖

### Codex

需要安装并登录 Codex CLI/Desktop。

```bash
codex --version
```

`codex --version` 只证明 CLI 存在，不证明 OAuth 和 skill 可用。还需要确认 Codex Desktop/CLI 已登录，并且当前会话能调用 OAuth 登录的 GPT 模型。当前工作流不要求设置 `OPENAI_API_KEY`。

### Codex skills

项目内自带并可由脚本安装：

```text
.codex/skills/fish-study-exam-paper/SKILL.md
```

还需要确认以下全局 skill 可用：

| Skill | 用途 | 位置建议 |
|---|---|---|
| `fish-study-photo-workflow` | 家长上传错题照片后一键生成知识点和训练卷 | `~/.codex/skills/fish-study-photo-workflow/` |
| `fish-study-exam-paper` | 真实试卷、PDF、配图、交付规则 | `~/.codex/skills/fish-study-exam-paper/` |
| `gpt-image-2` | 生成试卷正式配图 | `~/.codex/skills/gpt-image-2/` |
| `playwright` 或等效浏览器控制能力 | 截图、PDF、视觉验证 | `~/.codex/skills/playwright/` 或工具内置 |

如果新机器没有 `gpt-image-2` skill，需要从已有 Codex skill 库同步到：

```text
~/.codex/skills/gpt-image-2/SKILL.md
```

同步后重启 Codex 会话，让 skill 列表刷新。

验收：

```bash
ls ~/.codex/skills/fish-study-photo-workflow/SKILL.md
ls ~/.codex/skills/fish-study-exam-paper/SKILL.md
ls ~/.codex/skills/gpt-image-2/SKILL.md
```

重启 Codex 会话后，让当前会话读取或使用 `fish-study-photo-workflow` 和 `fish-study-exam-paper`，并确认它们使用当前机器的 repo 路径，而不是旧路径。

### Node Playwright

用于 HTML 截图、图片宽度检查和 PDF 导出。

如果仓库放在 `$HOME/fish-study` 这类 `$HOME` 子目录下，可以安装到 `$HOME`：

```bash
npm install --prefix "$HOME" playwright
```

如果仓库不在 `$HOME` 下，优先在仓库内安装，或明确配置 Node 模块解析路径；否则 `require.resolve("playwright")` 可能找不到 `$HOME/node_modules`。

验证：

```bash
node - <<'NODE'
console.log(require.resolve("playwright"))
NODE
```

如需安装浏览器：

```bash
npx playwright install chromium
```

### Python 可选模块

项目核心 CLI 主要使用 Python 标准库。PDF 验证建议安装 `pypdf`：

```bash
python3 -m pip install --user pypdf
python3 -m pip install --user pytest
```

验证：

```bash
python3 - <<'PY'
import pypdf
print(pypdf.__version__)
PY
```

### GitHub CLI

只有需要发布版本时才需要：

```bash
brew install gh
gh auth login
gh auth status
```

## 第 5 步：初始化 Obsidian vault

```bash
scripts/init_vault.sh
```

注意：该脚本会写入 `.obsidian/app.json`、`.obsidian/core-plugins.json`、入口页、教材索引、错题归因规则和模板文件。只建议对全新 vault 运行；如果目标 vault 已有内容，先备份或人工确认这些文件可以覆盖。

默认写入：

```text
$HOME/Downloads/obsidian/fish-study
```

如果需要其他位置，先设置：

```bash
export FISH_STUDY_VAULT_ROOT="/path/to/obsidian/fish-study"
scripts/init_vault.sh
```

## 第 6 步：下载或放入本地资料

已知三套七下资料可用脚本下载：

```bash
scripts/download_sources.sh
```

也可以手动把 ZIP 放到：

```text
sources/raw/
```

注意：

- `sources/raw/` 和 `sources/extracted/` 不提交 Git。
- 原始教材、完整课件、完整 PDF、扫描图都只保存在本机。

如果下载失败：

1. 手动把合法取得的 ZIP 放到 `sources/raw/`。
2. 确认文件名与 `data/sources/source-ledger.json` 的 `source_id` 对应。
3. 确认 ledger 的 `local_path` 是当前机器可解析的相对路径或绝对路径。
4. 运行 `python3 -m fish_study_wiki.cli inventory`。
5. 运行 `python3 -m fish_study_wiki.cli verify`，确认 SHA256 匹配。

## 第 7 步：重建索引和知识库

```bash
python3 -m fish_study_wiki.cli inventory
python3 -m fish_study_wiki.cli build
python3 -m fish_study_wiki.cli verify
```

验证报告：

```text
reports/wiki-quality.md
$FISH_STUDY_VAULT_ROOT/00-入口/wiki-quality.md
```

## 第 8 步：验收安装

安装完成后，运行：

```bash
python3 -m pytest -q
python3 -m fish_study_wiki.cli study-context
python3 -m fish_study_wiki.cli verify
```

最低通过标准：

- 测试通过。
- `study-context` 能列出当前可用资料。
- `verify` 不出现需要阻断的 `ERROR`。
- `~/.codex/skills/fish-study-exam-paper/SKILL.md` 存在。
- Codex 会话能看到或使用 `fish-study-exam-paper` 和 `gpt-image-2`。

完整验收顺序：

1. `scripts/setup_ai_machine.sh`
2. 检查 `data/sources/source-ledger.json` 的 `local_path`
3. `scripts/init_vault.sh`，仅限新 vault 或已确认覆盖
4. `scripts/download_sources.sh`，或手动放入 ZIP
5. `python3 -m pytest -q`
6. `python3 -m fish_study_wiki.cli inventory`
7. `python3 -m fish_study_wiki.cli build`
8. `python3 -m fish_study_wiki.cli study-context`
9. `python3 -m fish_study_wiki.cli verify`

## AI 生成真实试卷时的额外检查

当任务涉及模拟卷、PDF、图片或“真实试卷格式”：

1. 先使用 `fish-study-exam-paper` skill。
2. 所有绘图题使用 `gpt-image-2`。
3. 图片保存到本地 `outputs/exam-preview/assets/`。
4. 用 Playwright 截图检查 HTML。
5. 用 Playwright `page.pdf` 导出 PDF。
6. PDF 页脚使用浏览器变量生成 `当前页/总页数`。
7. 用 `pypdf` 检查页数、页码文本、图片对象。
8. 用 `qlmanage -t` 生成高分辨率预览，确认页码真的渲染出来。
9. 交付时使用 Markdown 绝对路径文件链接：

```md
[math-grade7-mock-paper.pdf](/absolute/path/to/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)
```

不要优先使用：

- 纯文本本地路径。
- `127.0.0.1` 下载地址。
- `/mnt/data`。

## 常见问题

### `study-context` 里资料是 0 套

先检查：

```bash
ls sources/raw
python3 -m fish_study_wiki.cli inventory
python3 -m fish_study_wiki.cli build
```

如果是新资料，确认 `data/sources/source-ledger.json` 有对应记录。

### Obsidian 写到旧路径

检查：

```bash
echo "$FISH_STUDY_VAULT_ROOT"
python3 - <<'PY'
from fish_study_wiki import settings
print(settings.VAULT_ROOT)
PY
```

必要时重新设置 `FISH_STUDY_VAULT_ROOT`。

### Codex 看不到新 skill

检查文件是否存在：

```bash
ls ~/.codex/skills/fish-study-exam-paper/SKILL.md
ls ~/.codex/skills/gpt-image-2/SKILL.md
```

然后重启 Codex 会话。

### PDF 能解析页码但预览看不到页码

不要手写 PDF 文本层补页码。用 Playwright PDF 页脚重新导出。

## 提交边界

可以提交：

- `README.md`
- `docs/*.md`
- `.codex/skills/**/SKILL.md`
- `scripts/*.sh`
- `fish_study_wiki/*.py`
- `tests/*.py`
- `data/sources/source-ledger.json`
- `sources/inventory/*`
- `reports/wiki-quality.md`

不要提交：

- `outputs/`
- `sources/raw/`
- `sources/extracted/`
- 完整教材、课件 ZIP、完整 PDF、完整图片扫描件。
