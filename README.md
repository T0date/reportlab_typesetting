# ReportLab Typesetting

A Python library to simplify common typesetting tasks with ReportLab.

## Installation

```bash
pip install reportlab_typesetting
```

## Usage

Here is a simple example of how to use the library:

```python
import logging
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from reportlab_typesetting import (
    BlockAligner,
    CanvasRenderer,
    Font,
    HAlign,
    LayoutEngine,
    VAlign,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_DIR = "output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

PDF_PATH = os.path.join(OUTPUT_DIR, "example.pdf")

# 1. ReportLabのCanvasを準備
c = canvas.Canvas(PDF_PATH, pagesize=letter)
page_width, page_height = letter

# 2. フォントを準備（TTFフォントを前提）
font_family = [
    Font(name="avenir-next", path="/path/to/fonts/avenir-next-regular.ttf"),
    Font(name="SourceHanSansJP", path="/path/to/fonts/SourceHanSansJP-Regular.ttf"),
]

# 3. レイアウトエンジンを初期化
engine = LayoutEngine()
engine.add_font_family(font_family)

# 4. レイアウトしたいテキスト
text_content = (
    "これは reportlab_typesetting ライブラリです。"
    "日本語とEnglishが混在した文章の禁則処理や、"
    "自動的なフォント切り替えを提供します。"
    "This is a test of the reportlab_typesetting library. "
)

# 5. テキストをレイアウト
block_width, block_height = 400, 200

x_pos = 50
y_pos = page_height - 50

text_layout = engine.layout(
    text_content,
    width=block_width,
    font_size=16,
    leading_ratio=1.6,
    use_justification=True,
    use_hyphenation=False,
)

# 6. ブロックの中央に配置する例
aligned_layout = (
    BlockAligner(text_layout, width=block_width, height=block_height)
    .alignment(horizontal=HAlign.CENTER, vertical=VAlign.MIDDLE)
    .apply()
)

# 7. 描画
renderer = CanvasRenderer(canvas=c)
renderer.draw_block_guides(x_pos, y_pos, block_width, block_height)
renderer.draw_layout_guides(aligned_layout, x_pos, y_pos)
renderer.render(aligned_layout, x_pos, y_pos)

# 8. 保存
c.save()
```