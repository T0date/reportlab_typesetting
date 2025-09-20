import logging
import os

from reportlab.lib import colors
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

# 2. フォントを準備
font_family = [
    Font(name="HeiseiKakuGo-W5"),
]

# 3. レイアウトエンジンを初期化
engine = LayoutEngine()
engine.add_font_family(font_family)

# 4. レイアウトしたいテキスト
text_content = (
    "これはreportlabを使用して、自動的に折り返される長い「日本語」の文章のサンプルです。"
    "指定された幅を超えるとテキストは自動的に次の行に折り返されます。"
    "padding込みで計算すると開き括弧が行末にきますが、次行に移っているのが確認できます。"
)

# 5. テキストをレイアウト
block_width, block_height = 400, 150

x_pos = 50
y_pos = page_height - 50

text_layout = engine.layout(
    text_content,
    width=block_width,
    font_size=14,
    leading_ratio=1.6,
    use_justification=True,
)

# 6. 配置
aligned_layout_no_padding = (
    BlockAligner(text_layout, width=block_width, height=block_height)
    .alignment(horizontal=HAlign.CENTER, vertical=VAlign.TOP)
    .apply()
)

aligned_layout_with_padding = (
    BlockAligner(text_layout, width=block_width, height=block_height)
    .alignment(horizontal=HAlign.CENTER, vertical=VAlign.TOP)
    .padding(10)
    .apply()
)

# 7. 描画
c.setFillColor(colors.antiquewhite)
c.rect(x_pos, y_pos - block_height, block_width, block_height, fill=True, stroke=False)

renderer = CanvasRenderer(canvas=c)
renderer.render(aligned_layout_no_padding, x_pos, y_pos)

y_pos -= block_height + 20
c.setFillColor(colors.antiquewhite)
c.rect(x_pos, y_pos - block_height, block_width, block_height, fill=True, stroke=False)

renderer = CanvasRenderer(canvas=c)
renderer.render(aligned_layout_with_padding, x_pos, y_pos)

# 8. 保存
c.save()
