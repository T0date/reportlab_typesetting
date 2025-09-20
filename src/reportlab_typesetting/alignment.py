from __future__ import annotations

import logging
from typing import Tuple, Union

from .datatypes import HAlign, TextLayout, VAlign
from .engine import LayoutEngine


class BlockAligner:
    """テキストを指定サイズの矩形内に配置するときの座標を計算するクラス"""

    def __init__(self, layout: TextLayout, width: float, height: float):
        """`BlockAligner`オブジェクトを初期化する

        Parameters
        ----------
        layout : TextLayout
            配置対象の`TextLayout`オブジェクト
        width : float
            配置先の矩形ブロックの幅
        height : float
            配置先の矩形ブロックの高さ

        """
        self.layout = layout
        self.width = width
        self.height = height

        self._halign: HAlign = HAlign.LEFT
        self._valign: VAlign = VAlign.TOP
        self._padding_top: float = 0
        self._padding_right: float = 0
        self._padding_bottom: float = 0
        self._padding_left: float = 0

    def padding(self, px: Union[float, Tuple[float, ...]]) -> BlockAligner:
        """ブロック内のパディングを設定する

        Parameters
        ----------
        px : Union[float, Tuple[float, ...]]
            パディングの値。floatまたは1, 2, 4要素のタプルで指定する。

        Examples
        --------
        CSSの `padding` プロパティのように値を指定する。

        >>> # 全ての辺に10pxのパディング
        >>> aligner.padding(10)
        >>>
        >>> # 上下に10px, 左右に20pxのパディング
        >>> aligner.padding((10, 20))
        >>>
        >>> # 上10px, 右20px, 下30px, 左40pxのパディング
        >>> aligner.padding((10, 20, 30, 40))

        Returns
        -------
        BlockAligner
            メソッドチェーンのための自分自身のインスタンス

        """
        if isinstance(px, (int, float)):
            self._padding_top = self._padding_right = self._padding_bottom = (
                self._padding_left
            ) = px
        elif isinstance(px, tuple):
            if len(px) == 1:
                self._padding_top = self._padding_right = self._padding_bottom = (
                    self._padding_left
                ) = px[0]
            elif len(px) == 2:
                self._padding_top = self._padding_bottom = px[0]
                self._padding_right = self._padding_left = px[1]
            elif len(px) == 4:
                (
                    self._padding_top,
                    self._padding_right,
                    self._padding_bottom,
                    self._padding_left,
                ) = px
            else:
                raise ValueError(
                    "Padding must be a float or a tuple of 1, 2, or 4 floats."
                )
        else:
            raise TypeError("Padding must be a float or a tuple of floats.")

        return self

    def alignment(
        self, horizontal: HAlign | None = None, vertical: VAlign | None = None
    ) -> BlockAligner:
        """水平・垂直方向の配置を設定する

        Parameters
        ----------
        horizontal : HAlign | None, optional
            水平方向の配置（LEFT, CENTER, RIGHT）
        vertical : VAlign | None, optional
            垂直方向の配置（TOP, MIDDLE, BOTTOM）

        Returns
        -------
        BlockAligner
            メソッドチェーンのための自分自身のインスタンス

        """
        if horizontal is not None:
            self._halign = horizontal
        if vertical is not None:
            self._valign = vertical
        return self

    def apply(self) -> TextLayout:
        """設定に基づいて配置を適用し、結果の`TextLayout`を返す。

        注意: このメソッドは、コンストラクタで渡された`TextLayout`オブジェクトを直接変更します。

        Returns
        -------
        TextLayout
            座標が調整された、元の`TextLayout`オブジェクト

        """
        bbox = self.layout.get_content_bbox()
        if bbox is None:
            return self.layout

        _, _, layout_width, layout_height = bbox

        drawable_width = self.width - self._padding_left - self._padding_right

        # 描画可能幅にレイアウトが収まらない場合、再レイアウトを試みる
        if layout_width > drawable_width:
            logging.info(
                "Re-layout required: (layout_width: %s, drawable_width: %s)",
                layout_width,
                drawable_width,
            )

            params = self.layout.parameters
            original_text = params.get("text")

            if not original_text:
                raise RuntimeError(
                    "Cannot re-layout: original text not found in layout parameters."
                )

            # 再レイアウト用の引数を準備
            new_kwargs = {
                "font_size": params.get("font_size"),
                "leading_ratio": params.get("leading_ratio"),
                "use_justification": params.get("use_justification"),
                "use_hyphenation": params.get("use_hyphenation"),
                "text_color": params.get("text_color"),
            }

            engine = LayoutEngine()
            engine.add_font_family(params.get("fonts"))

            # 描画可能幅で再レイアウトを実行
            self.layout = engine.layout(
                original_text, width=drawable_width, **new_kwargs
            )

            # 再レイアウト後のバウンディングボックスを再取得
            bbox = self.layout.get_content_bbox()
            if bbox is None:
                return self.layout
            _, _, layout_width, layout_height = bbox

        drawable_height = self.height - self._padding_top - self._padding_bottom

        offset_x = self._padding_left
        if layout_width < drawable_width:
            if self._halign == HAlign.CENTER:
                offset_x += (drawable_width - layout_width) / 2
            elif self._halign == HAlign.RIGHT:
                offset_x += drawable_width - layout_width

        offset_y = -self._padding_top
        if layout_height < drawable_height:
            if self._valign == VAlign.MIDDLE:
                offset_y -= (drawable_height - layout_height) / 2
            elif self._valign == VAlign.BOTTOM:
                offset_y -= drawable_height - layout_height

        for line in self.layout.lines:
            for glyph in line.glyphs:
                glyph.x += offset_x
                glyph.y += offset_y

        return self.layout
