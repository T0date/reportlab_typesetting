import logging
import re
from typing import List, Optional, Union

import pyphen
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

from .datatypes import Font, Glyph, LineLayout, TextLayout


class LayoutEngine:
    """テキストの組版を行い、レイアウト情報を生成するエンジンクラス

    日本語の禁則処理、欧文ハイフネーション、均等割り付けなどの機能を提供する。
    """

    KINSHI_HEAD_OIKOMI = set("、。，．)]}）〉》」』】〙〗〟’”")
    """行頭禁則文字（追い込み）: 句読点、閉じ括弧など"""

    KINSHI_HEAD_OIDASHI = set("ゝゞ々ーぁぃぅぇぉっゃゅょァィゥェォッャュョ")
    """行頭禁則文字（追い出し）: 促音、拗音など"""

    KINSHI_TAIL = set("([｛（〔［〈《「『【〘〖〝")
    """行末禁則文字"""

    def __init__(self):
        """`LayoutEngine`オブジェクトを初期化する"""
        # 英語のハイフネーション辞書を準備
        self.__hyphen_dic = pyphen.Pyphen(lang="en_us")
        self.__font_family: List[Font] = []

    def add_font(self, font: Font):
        """レイアウトエンジンにフォントを1つ追加する

        Parameters
        ----------
        font : Font
            追加する`Font`オブジェクト

        """
        self.__font_family.append(font)
        logging.info(
            "Font added: %s (path: %s, wrap: %s)", font.name, font.path, font.word_wrap
        )

    def add_font_family(self, fonts: List[Font]):
        """レイアウトエンジンにフォントのリストを追加する

        Parameters
        ----------
        fonts : List[Font]
            追加する`Font`オブジェクトのリスト

        """
        for font in fonts:
            self.add_font(font)

    def layout(
        self,
        text: str,
        width: float,
        text_color: Optional[Union[str, colors.Color]] = colors.black,
        font_size: float = 12,
        leading_ratio: float = 1.2,
        use_justification: bool = False,
        use_hyphenation: bool = False,
    ) -> TextLayout:
        """テキストを組版し、レイアウト結果を返す

        テキストは文字ごとに適切なフォントが割り当てられ、同じフォントが連続するチャンクに分割される。
        フォントの検索は `add_font` または `add_font_family` で登録された順序で行われる。
        その後、指定された幅に合わせて行分割、禁則処理、ハイフネーション、均等割り付けなどを行い、最終的なレイアウトを生成する。

        Parameters
        ----------
        text : str
            レイアウトするテキスト
        width : float
            テキストブロックの幅
        text_color : Optional[Union[str, colors.Color]], optional
            テキストの色
        font_size : float, optional
            フォントサイズ
        leading_ratio : float, optional
            行送りの比率（フォントサイズに対する倍率）
        use_justification : bool, optional
            均等割り付けを有効にするか
        use_hyphenation : bool, optional
            欧文のハイフネーションを有効にするか

        Returns
        -------
        TextLayout
            レイアウト結果を表す`TextLayout`オブジェクト

        """

        text_layout = TextLayout()

        chunks = self.__chunk_text_with_newlines(text)

        cursor_y = -font_size
        line_index = 0
        line_height = font_size * leading_ratio

        while chunks:
            glyphs, chunks = self.__layout_line(
                chunks,
                cursor_y,
                font_size,
                width,
                line_index,
                use_justification,
                use_hyphenation,
                text_color,
            )

            line_layout = LineLayout(line_index, glyphs)
            text_layout.add_line(line_layout)

            line_index += 1
            cursor_y -= line_height

        text_layout.parameters = {
            "text": text,
            "width": width,
            "font_size": font_size,
            "leading_ratio": leading_ratio,
            "use_justification": use_justification,
            "use_hyphenation": use_hyphenation,
            "fonts": self.__font_family,
            "text_color": text_color,
        }

        return text_layout

    def __layout_line(
        self,
        chunks: List[tuple[str, Font]],
        y: float,
        font_size: float,
        max_width: float,
        line_index: int,
        need_justify: bool = False,
        use_hyphenation: bool = False,
        text_color: Optional[Union[str, colors.Color]] = colors.black,
    ) -> tuple[List[Glyph], List[tuple[str, Font]]]:
        cursor_x = 0

        glyphs: List[Glyph] = []
        remaining_chunks: List[tuple[str, Font]] = []

        for idx, (text, font) in enumerate(chunks):
            if text == "\n":
                remaining_chunks.extend(chunks[idx + 1 :])
                return glyphs, remaining_chunks

            if font.word_wrap == "CJK":
                # CJKテキストを、数字の連続・英字の連続・それ以外の単一文字に分割する
                cjk_words = re.findall(
                    r"-?\d+(?:[.,]\d+)*|[a-zA-Z]+(?:'[a-zA-Z]+)*|.", text
                )
                i = 0
                while i < len(cjk_words):
                    word = cjk_words[i]
                    word_width = pdfmetrics.stringWidth(word, font.name, font_size)

                    if cursor_x + word_width > max_width:
                        # 単語が収まらない場合
                        is_numeric_chunk = re.fullmatch(r"-?\d+(?:[.,]\d+)*", word)
                        is_alpha_chunk = re.fullmatch(r"[a-zA-Z]+(?:'[a-zA-Z]+)*", word)

                        # ================================================================
                        # Case 1: 行が空なのに単語が長すぎて収まらない場合
                        # ================================================================

                        # 無限ループを避けるため、この単語を配置して強制的に改行する
                        if not glyphs:
                            glyphs.append(
                                Glyph(
                                    word,
                                    font,
                                    font_size,
                                    cursor_x,
                                    y,
                                    word_width,
                                    line_index,
                                    text_color,
                                )
                            )
                            # この単語を消費して、残りを次の行に回す
                            remaining_text = "".join(cjk_words[i + 1 :])
                            if remaining_text:
                                remaining_chunks.append((remaining_text, font))
                            remaining_chunks.extend(chunks[idx + 1 :])
                            return glyphs, remaining_chunks

                        # ================================================================
                        # Case 2: 行が空ではないので、通常の改行処理を行う
                        # ================================================================

                        # 数字の連続は分割せず、常に一つの単位として扱う
                        elif is_numeric_chunk:
                            # 前のグリフの最後の文字が行末禁則かチェック
                            last_glyph_last_char = glyphs[-1].text[-1] if glyphs else ""
                            if last_glyph_last_char in self.KINSHI_TAIL:
                                # 前のグリフも次行に送る
                                last_glyph = glyphs.pop()
                                remaining_text = last_glyph.text + "".join(
                                    cjk_words[i:]
                                )
                            else:
                                # 数字/アルファベットのまとまりはそのまま次行へ
                                remaining_text = "".join(cjk_words[i:])

                        # アルファベットの連続は分割も考慮に入れて処理する
                        elif is_alpha_chunk:
                            # ハイフネーションが有効な場合は試みる
                            if use_hyphenation and self.__hyphen_dic:
                                possible_splits = list(self.__hyphen_dic.iterate(word))
                                best_split = None
                                for part1, part2 in reversed(possible_splits):
                                    hyphenated_part = part1 + "-"
                                    part_width = pdfmetrics.stringWidth(
                                        hyphenated_part, font.name, font_size
                                    )
                                    if cursor_x + part_width <= max_width:
                                        best_split = (
                                            hyphenated_part,
                                            part_width,
                                            part2,
                                        )
                                        break

                                if best_split:
                                    hyphenated_part, part_width, remaining_part = (
                                        best_split
                                    )
                                    glyphs.append(
                                        Glyph(
                                            hyphenated_part,
                                            font,
                                            font_size,
                                            cursor_x,
                                            y,
                                            part_width,
                                            line_index,
                                            text_color,
                                        )
                                    )
                                    remaining_text = remaining_part + "".join(
                                        cjk_words[i + 1 :]
                                    )
                                    # ハイフネーションしたので、ここで改行処理を完了
                                    if need_justify:
                                        self.__justification(glyphs, max_width)
                                    if remaining_text:
                                        remaining_chunks.append((remaining_text, font))
                                    remaining_chunks.extend(chunks[idx + 1 :])
                                    return glyphs, remaining_chunks

                            # ハイフネーションしない/できない場合は、単語全体を次行へ
                            remaining_text = "".join(cjk_words[i:])

                        # ================================================================
                        # Case 3: 数字以外の単一文字の場合、詳細な禁則処理を適用
                        # ================================================================

                        else:
                            ch = word
                            can_check_prev = bool(glyphs)
                            last_glyph_last_char = (
                                glyphs[-1].text[-1] if can_check_prev else ""
                            )

                            is_prev_tail = last_glyph_last_char in self.KINSHI_TAIL
                            is_current_head_oidashi = ch in self.KINSHI_HEAD_OIDASHI
                            is_current_head_oikomi = ch in self.KINSHI_HEAD_OIKOMI
                            is_prev_head_kinsoku = (
                                last_glyph_last_char in self.KINSHI_HEAD_OIKOMI
                                or last_glyph_last_char in self.KINSHI_HEAD_OIDASHI
                            )

                            remaining_words = []
                            perform_oikomi = False

                            # 追い出し or 行末禁則
                            if is_prev_tail or (
                                is_current_head_oidashi and not is_prev_head_kinsoku
                            ):
                                last_glyph = glyphs.pop()
                                remaining_words = [last_glyph.text, ch] + cjk_words[
                                    i + 1 :
                                ]

                            # 追い込み
                            elif is_current_head_oikomi or (
                                is_current_head_oidashi and is_prev_head_kinsoku
                            ):
                                perform_oikomi = True
                                remaining_words = cjk_words[i + 1 :]

                            else:
                                # 通常の改行
                                remaining_words = cjk_words[i:]

                            if perform_oikomi:
                                glyphs.append(
                                    Glyph(
                                        ch,
                                        font,
                                        font_size,
                                        cursor_x,
                                        y,
                                        word_width,
                                        line_index,
                                        text_color,
                                    )
                                )
                                cursor_x += word_width

                            remaining_text = "".join(remaining_words)

                        # ================================================================
                        # 後処理
                        # ================================================================

                        # 均等割り付け
                        if need_justify:
                            self.__justification(glyphs, max_width)

                        # 行頭スペース削除
                        remaining_text = remaining_text.lstrip(" ")

                        if remaining_text:
                            remaining_chunks.append((remaining_text, font))

                        remaining_chunks.extend(chunks[idx + 1 :])
                        return glyphs, remaining_chunks

                    glyphs.append(
                        Glyph(
                            word,
                            font,
                            font_size,
                            cursor_x,
                            y,
                            word_width,
                            line_index,
                            text_color,
                        )
                    )

                    cursor_x += word_width
                    i += 1

            else:
                words = re.split(r"(\s+)", text)

                i = 0
                while i < len(words):
                    word = words[i]
                    word_width = pdfmetrics.stringWidth(word, font.name, font_size)

                    # 改行判定（行頭からはみ出す場合は改行）
                    if cursor_x + word_width > max_width:
                        # ハイフネーション処理
                        # wordが空白文字でなく、ハイフネーション辞書があり、ハイフネーションが有効な場合
                        if use_hyphenation and word.strip() and self.__hyphen_dic:
                            possible_splits = list(self.__hyphen_dic.iterate(word))

                            best_split = None
                            # 行に収まる最長の分割を探すため、後ろから試す
                            for part1, part2 in reversed(possible_splits):
                                hyphenated_part = part1 + "-"
                                part_width = pdfmetrics.stringWidth(
                                    hyphenated_part, font.name, font_size
                                )

                                # 最長の適合する部分が見つかった
                                if cursor_x + part_width <= max_width:
                                    best_split = (hyphenated_part, part_width, part2)
                                    break

                            if best_split:
                                hyphenated_part, part_width, remaining_part = best_split

                                # ハイフネーションした前半を現在の行に追加
                                glyphs.append(
                                    Glyph(
                                        hyphenated_part,
                                        font,
                                        font_size,
                                        cursor_x,
                                        y,
                                        part_width,
                                        line_index,
                                        text_color,
                                    )
                                )

                                # 単語の後半と残りの単語を次行に回す
                                remaining_text = remaining_part + "".join(
                                    words[i + 1 :]
                                )
                                if remaining_text:
                                    remaining_chunks.append((remaining_text, font))
                                remaining_chunks.extend(chunks[idx + 1 :])

                                # 現在の行を均等割り付け
                                if need_justify:
                                    self.__justification(glyphs, max_width)

                                return glyphs, remaining_chunks

                        # ハイフネーションしなかった/できなかった場合のフォールバック
                        remaining_text = "".join(words[i:]).lstrip()
                        if remaining_text:
                            remaining_chunks.append((remaining_text, font))
                        remaining_chunks.extend(chunks[idx + 1 :])

                        # 均等割り付け
                        if need_justify:
                            self.__justification(glyphs, max_width)

                        return glyphs, remaining_chunks

                    glyphs.append(
                        Glyph(
                            word,
                            font,
                            font_size,
                            cursor_x,
                            y,
                            word_width,
                            line_index,
                            text_color,
                        )
                    )
                    cursor_x += word_width
                    i += 1

        return glyphs, []

    def __justification(self, glyphs: List[Glyph], width: float):
        if not glyphs:
            return

        # 現在の行の実際の幅を計算
        current_line_width = glyphs[-1].x + glyphs[-1].width

        # 不足している幅（正の値）または余っている幅（負の値）を計算
        gap_width = width - current_line_width

        # グリフ間のスペースの数
        num_gaps = len(glyphs) - 1

        if num_gaps <= 0:
            return

        # 文字を詰める場合 (行幅を超えている場合)
        if gap_width < 0:
            # 詰めるべき総量 (正の値)
            amount_to_shrink = -gap_width

            # 詰める優先順位が高い文字（句読点や始め括弧など）
            PRIORITY_SHRINK_CHARS = set("、。，．")

            # 各グリフ間の調整量を保持する配列
            adjustments = [0.0] * num_gaps

            # 優先的に詰める対象となるグリフ間（ギャップ）のインデックスを収集
            priority_indices = [
                i
                for i, glyph in enumerate(glyphs[:-1])
                if glyph.text in PRIORITY_SHRINK_CHARS
            ]

            if priority_indices:
                # 1つの優先文字あたりで詰められる最大量をフォントサイズの半分と仮定
                max_shrink_per_char = glyphs[0].font_size * 0.5
                total_priority_shrinkable = len(priority_indices) * max_shrink_per_char

                # 実際に優先文字で詰める量を計算
                priority_shrink_amount = min(
                    amount_to_shrink, total_priority_shrinkable
                )

                if priority_shrink_amount > 0:
                    # 優先文字1つあたりで詰める量を計算し、優先ギャップに割り当てる
                    shrink_per_priority_char = priority_shrink_amount / len(
                        priority_indices
                    )
                    for i in priority_indices:
                        adjustments[i] = -shrink_per_priority_char
                    # 残りの詰める量を更新
                    amount_to_shrink -= priority_shrink_amount

            # それでもまだ詰める必要がある場合、残りをすべてのギャップに均等に分配
            if amount_to_shrink > 0:
                remaining_shrink_per_gap = amount_to_shrink / num_gaps
                for i in range(num_gaps):
                    adjustments[i] -= remaining_shrink_per_gap

            # 計算した調整量を累積しながら、各グリフのx座標を更新
            accumulated_adjustment = 0
            for i in range(num_gaps):
                accumulated_adjustment += adjustments[i]
                glyphs[i + 1].x += accumulated_adjustment

        # スペースを広げる場合 (行幅に満たない場合)
        else:
            # すべてのギャップに均等にスペースを分配
            spacing = gap_width / num_gaps
            for j in range(1, len(glyphs)):
                glyphs[j].x += j * spacing

    def __get_font(self, ch: str):
        codepoint = ord(ch)

        for font in self.__font_family:
            f = pdfmetrics.getFont(font.name)

            # TTF fonts (TTFont で登録したフォント)
            if isinstance(f, TTFont) and hasattr(f, "face"):
                if codepoint in f.face.charWidths:
                    return font

            # Unicode CID Fonts (e.g., HeiseiKakuGo-W5...)
            elif isinstance(f, UnicodeCIDFont) and hasattr(f, "stringWidth"):
                width = f.stringWidth(ch, 12)

                # 幅が0でなければ利用可能
                if width:
                    return font

            # Base14 fonts (e.g., Helvetica...)
            elif hasattr(f, "widths"):
                if 0 <= codepoint < len(f.widths):
                    width = f.widths[codepoint]

                    # 幅が0でなければ利用可能
                    if width:
                        return font

        raise ValueError(
            f"No suitable font found for character '{ch}' (U+{ord(ch):04X}). "
            "Please register a font that supports this character."
        )

    def __chunk_text_with_newlines(self, text: str) -> List[tuple[str, Font]]:
        parts = re.split(r"(\n)", text)
        chunks = []

        for part in parts:
            if part == "\n":
                chunks.append(("\n", None))
            elif part:
                chunks.extend(self.__chunk_text_by_font(part))

        return chunks

    def __chunk_text_by_font(self, text: str) -> List[tuple[str, Font]]:
        chunks = []
        buffer = ""
        current_font = None

        for ch in text:
            font = self.__get_font(ch)

            if current_font is None:
                current_font = font

            if font.name != current_font.name:
                chunks.append((buffer, current_font))
                buffer = ""
                current_font = font

            buffer += ch

        if buffer:
            chunks.append((buffer, current_font))

        return chunks
