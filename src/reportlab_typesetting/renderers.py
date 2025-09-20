from abc import ABC, abstractmethod
from typing import Union

from reportlab.lib import colors
from reportlab.pdfgen import canvas

from .datatypes import TextLayout


class BaseRenderer(ABC):
    """
    レイアウトされたテキストを描画/表示するための基底クラス
    """

    @abstractmethod
    def render(self, layout: TextLayout, x: float = 0, y: float = 0):
        """レイアウトされたテキストを描画/表示する

        Parameters
        ----------
        layout : TextLayout
            描画対象の`TextLayout`オブジェクト
        x : float, optional
            描画を開始するブロックの左上のx座標
        y : float, optional
            描画を開始するブロックの左上のy座標

        """
        raise NotImplementedError


class CanvasRenderer(BaseRenderer):
    """
    レイアウト結果をCanvasに出力するレンダラ
    """

    def __init__(self, canvas: canvas.Canvas):
        """`CanvasRenderer`オブジェクトを初期化する

        Parameters
        ----------
        canvas : canvas.Canvas
            描画対象のReportLab Canvasオブジェクト
        """
        self.canvas = canvas

    def render(self, layout: TextLayout, x: float = 0, y: float = 0):
        """レイアウトされたテキストをCanvasに描画する

        Parameters
        ----------
        layout : TextLayout
            描画対象の`TextLayout`オブジェクト
        x : float, optional
            描画を開始するブロックの左上のx座標
        y : float, optional
            描画を開始するブロックの左上のy座標

        """
        for line in layout.lines:
            for glyph in line.glyphs:
                self.canvas.setFillColor(glyph.text_color)
                self.canvas.setFont(glyph.font.name, glyph.font_size)
                self.canvas.drawString(x + glyph.x, y + glyph.y, glyph.text)

    def draw_layout_guides(
        self,
        layout: TextLayout,
        x: float,
        y: float,
        color: Union[str, colors.Color] = colors.lightgrey,
    ):
        """レイアウトされたテキストのバウンディングボックスを描画する

        Parameters
        ----------
        layout : TextLayout
            描画対象の`TextLayout`オブジェクト
        x : float
            テキストが配置されるブロックの左上のx座標
        y : float
            テキストが配置されるブロックの左上のy座標
        color : Union[str, colors.Color], optional
            ガイド線の色

        """
        bbox = layout.get_content_bbox()
        if not bbox:
            return

        # バウンディングボックスの相対座標を計算
        left_rel, bottom_rel, width, height = bbox

        # canvasに描画するための絶対座標を計算
        abs_left = x + left_rel
        abs_bottom = y + bottom_rel

        self.canvas.saveState()
        self.canvas.setStrokeColor(color)
        self.canvas.rect(abs_left, abs_bottom, width, height)
        self.canvas.restoreState()

    def draw_block_guides(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        h_color: Union[str, colors.Color] = colors.red,
        v_color: Union[str, colors.Color] = colors.blue,
    ):
        """指定された矩形領域のガイド線を描画する

        Parameters
        ----------
        x : float
            矩形の左上のx座標
        y : float
            矩形の左上のy座標
        width : float
            矩形の幅
        height : float
            矩形の高さ
        h_color : Union[str, colors.Color], optional
            水平線の色
        v_color : Union[str, colors.Color], optional
            垂直線の色

        """
        self.canvas.saveState()

        self.canvas.setStrokeColor(h_color)
        self.canvas.line(x, y, x + width, y)  # Top
        self.canvas.line(x, y - height, x + width, y - height)  # Bottom

        self.canvas.setStrokeColor(v_color)
        self.canvas.line(x, y, x, y - height)  # Left
        self.canvas.line(x + width, y, x + width, y - height)  # Right

        self.canvas.restoreState()


class PrintRenderer(BaseRenderer):
    """
    レイアウト結果をコンソールに出力するデバッグ用レンダラ
    """

    def render(self, layout: TextLayout, *args, **kwargs):
        for line in layout.lines:
            print("-----------------------------------------")
            print(f"Line {line.index}: width {line.width}")
            print("-----------------------------------------")
            for glyph in line.glyphs:
                print(glyph.text, glyph.x, glyph.y, glyph.width, glyph.font.name)
