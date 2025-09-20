from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

import reportlab.pdfbase._fontdata as fontdata
from reportlab.lib import colors
from reportlab.pdfbase import cidfonts, pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont


class HAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VAlign(Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class Font:
    """組版に使用するフォントを表すクラス"""

    def __init__(
        self, name: str, path: Optional[str] = None, word_wrap: Optional[str] = None
    ):
        """`Font`オブジェクトを初期化する

        ReportLabへのフォント登録や、ワードラップの挙動（`'CJK'`または`'LTR'`）の決定を扱う。

        Parameters
        ----------
        name : str
            フォント名。ReportLab内でフォントを識別するために使用される。
        path : Optional[str], optional
            TTFフォントファイルへのパス。指定されない場合、ReportLabの標準フォント（例: `Helvetica`）とみなす。
        word_wrap : Optional[str], optional
            ワードラップの挙動を `'CJK'` または `'LTR'` で指定する。
            指定されない場合、フォントの内容や`path`の有無に基づいて自動的に決定する。

        """
        self.name = name
        self.path = path

        # フォントの種類によって、登録処理が違う
        base14_fonts = list(fontdata.standardFontAttributes.keys())
        cid_fonts = list(cidfonts.defaultUnicodeEncodings.keys())

        if name in base14_fonts:
            pass

        elif name in cid_fonts and name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont(name))

        elif name and path and name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, path))

        # 指定があれば従い、なければ判定する
        if word_wrap:
            self.word_wrap = word_wrap
        else:
            self.word_wrap = self._determine_word_wrap()

    def _determine_word_wrap(self) -> str:
        """フォントの種類を判別し、`word_wrap`を自動的に決定する"""
        # 日本語で使われる文字のUnicode範囲
        jp_ranges = [
            (0x3040, 0x309F),  # ひらがな (Hiragana)
            (0x30A0, 0x30FF),  # カタカナ (Katakana)
            (0x4E00, 0x9FFF),  # CJK統合漢字 (CJK Unified Ideographs)
            (0xFF00, 0xFFEF),  # 全角記号など (Full-width forms)
        ]

        try:
            f = pdfmetrics.getFont(self.name)

            # TTFontの場合
            if isinstance(f, TTFont) and hasattr(f, "face"):
                char_codes = f.face.charWidths.keys()
                for code in char_codes:
                    for start, end in jp_ranges:
                        if start <= code <= end:
                            return "CJK"

            # UnicodeCIDFontの場合
            if isinstance(f, UnicodeCIDFont) and hasattr(f, "stringWidth"):
                for start, end in jp_ranges:
                    for codepoint in range(start, end + 1):
                        ch = chr(codepoint)
                        try:
                            _ = f.stringWidth(ch, 12)
                            return "CJK"
                        except Exception:
                            continue

            # その他のフォント（HelveticaなどBase14フォント）は欧文フォントとみなす
            return "LTR"
        except Exception as e:
            logging.warning(
                f"Could not determine word wrap for {self.path or self.name} due to an error. Defaulting to 'LTR'. Error: {e}"
            )
            return "LTR"


@dataclass
class Glyph:
    """描画されるテキストの最小単位（文字や単語など）を描画するための情報を扱うクラス"""

    text: str
    """グリフが表す文字（列）"""

    font: Font
    """グリフを描画するためのフォント"""

    font_size: float
    """フォントサイズ"""

    x: float
    """ブロック内で原点からみたときのx座標"""

    y: float
    """ブロック内で原点からみたときのy座標"""

    width: float
    """グリフの幅"""

    line: int
    """このグリフが属する行のインデックス"""

    text_color: Optional[Union[str, colors.Color]] = colors.black
    """グリフを描画するための文字色"""


class LineLayout:
    """レイアウトされたテキストの1行を表すクラス"""

    def __init__(self, index: int, glyphs: List[Glyph]):
        """`LineLayout`オブジェクトを初期化する

        Parameters
        ----------
        index : int
            テキストブロック内での行のインデックス
        glyphs : List[Glyph]
            この行に含まれるグリフのリスト

        """
        self.index: int = index
        """テキストブロック内での行のインデックス"""

        self.glyphs: List[Glyph] = glyphs
        """この行に含まれるグリフのリスト"""

    def add_glyph(self, glyph: Glyph):
        """行にグリフを追加する

        Parameters
        ----------
        glyph : Glyph
            追加する`Glyph`オブジェクト

        """
        self.glyphs.append(glyph)

    @property
    def width(self):
        """行の計算された幅"""
        if not self.glyphs:
            return 0

        left = min(g.x for g in self.glyphs)
        right = max(g.x + g.width for g in self.glyphs)

        return right - left


class TextLayout:
    """レイアウトされたテキストブロック全体を表すクラス"""

    def __init__(self):
        """`TextLayout`オブジェクトを初期化する"""

        self.lines: List[LineLayout] = []
        """構成する行オブジェクトのリスト"""

        self.parameters: dict = {}

    def add_line(self, line: LineLayout):
        """テキストブロックに行を追加する"""
        self.lines.append(line)

    def get_content_bbox(self) -> tuple[float, float, float, float] | None:
        """表示範囲の正確なバウンディングボックスを計算する

        Returns
        -------
        tuple[float, float, float, float] | `None`
            表示範囲の `(left, bottom, width, height)` を含むタプル。
            表示するテキストがない場合は`None`を返す。

        """
        content_glyphs = [
            g for line in self.lines for g in line.glyphs if g.text.strip()
        ]
        if not content_glyphs:
            return None

        left = min(g.x for g in content_glyphs)
        right = max(g.x + g.width for g in content_glyphs)
        top = max(g.y + g.font_size for g in content_glyphs)
        bottom = min(g.y for g in content_glyphs)

        width = right - left
        height = top - bottom

        return (left, bottom, width, height)
