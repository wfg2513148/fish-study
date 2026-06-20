from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


def write_pdf_from_html(html: str, pdf_path: Path | str) -> None:
    target = Path(pdf_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "source.html"
        html_path.write_text(html, encoding="utf-8")
        script = r"""
const { chromium } = require('playwright');
const [htmlPath, pdfPath] = process.argv.slice(1);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true
  });
  await browser.close();
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""
        completed = subprocess.run(
            ["node", "-e", script, str(html_path), str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"failed to export PDF {target}: {detail}")
