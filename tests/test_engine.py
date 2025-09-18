import pytest

from reportlab_typesetting.datatypes import Font
from reportlab_typesetting.engine import LayoutEngine


def test_layout_cjk_wrapping():
    """
    CJKテキストがグリフ単位で正しく折り返されることをテストする。
    禁則処理に該当しない文字で行われる単純な折り返しを確認する。
    """
    # Arrange
    engine = LayoutEngine()

    # ReportLabに組み込まれている日本語CIDフォントを使用する。
    # word_wrap='CJK' を明示的に指定して、フォント検出ロジックに依存しないようにする。
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    # HeiseiKakuGo-W5は等幅フォントなので、各文字の幅はフォントサイズと同じ12になる。
    font_size = 12

    # 4文字（幅48）は収まるが、5文字（幅60）は収まらない幅に設定。
    block_width = 49

    text = "一二三四五六七八九十"  # 10文字のテキスト

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    # 3行に分割されることを期待する (4文字、4文字、2文字)
    assert len(layout.lines) == 3

    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == "一二三四"

    line2_text = "".join(g.text for g in layout.lines[1].glyphs)
    assert line2_text == "五六七八"

    line3_text = "".join(g.text for g in layout.lines[2].glyphs)
    assert line3_text == "九十"


@pytest.mark.parametrize(
    "char, text_before, text_after",
    [
        ("、", "一二三四", "五六七八"),  # 読点
        ("。", "一二三四", "五六七八"),  # 句点
        ("）", "一二三四", "五六七八"),  # 閉じ丸括弧
        ("」", "一二三四", "五六七八"),  # 閉じかぎ括弧
    ],
)
def test_layout_kinsoku_oikomi(char, text_before, text_after):
    """
    行頭禁則文字（追い込み）が正しく処理されることをテストする。
    句読点などが行頭に来る場合に、改行されずに前の行に押し込まれることを確認する。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # 4文字（幅48）は収まるが、5文字（幅60）は収まらない幅に設定。
    block_width = 49

    text = f"{text_before}{char}{text_after}"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    assert len(layout.lines) == 2

    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == f"{text_before}{char}"

    line2_text = "".join(g.text for g in layout.lines[1].glyphs)
    assert line2_text == text_after


@pytest.mark.parametrize(
    "char, text_before, text_after",
    [
        ("々", "一二三四", "五"),  # 繰り返し記号
        ("ー", "一二三四", "五"),  # 長音符
        ("っ", "一二三四", "五"),  # 促音
        ("ょ", "一二三四", "五"),  # 拗音
    ],
)
def test_layout_kinsoku_oidashi(char, text_before, text_after):
    """
    行頭禁則文字（追い出し）が正しく処理されることをテストする。
    繰り返し記号や促音などが行頭に来る場合に、前の文字を伴って次行に送られることを確認する。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # 4文字（幅48）は収まるが、5文字（幅60）は収まらない幅に設定。
    block_width = 49

    text = f"{text_before}{char}{text_after}"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    # 2行に分割されることを期待する
    assert len(layout.lines) == 2

    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == text_before[:-1]

    line2_text = "".join(g.text for g in layout.lines[1].glyphs)
    assert line2_text == f"{text_before[-1]}{char}{text_after}"


@pytest.mark.parametrize(
    "char, text_before, text_after",
    [
        ("「", "一二三", "四五"),  # 開きかぎ括弧
        ("（", "一二三", "四五"),  # 開き丸括弧
        ("『", "一二三", "四五"),  # 開き二重かぎ括弧
        ("【", "一二三", "四五"),  # 開き隅付き括弧
    ],
)
def test_layout_kinsoku_tail(char, text_before, text_after):
    """
    行末禁則文字が正しく処理されることをテストする。
    開き括弧などが行末に来る場合に、次行に送られることを確認する。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # 4文字（幅48）は収まるが、5文字（幅60）は収まらない幅に設定。
    block_width = 49

    text = f"{text_before}{char}{text_after}"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    assert len(layout.lines) == 2

    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == text_before

    line2_text = "".join(g.text for g in layout.lines[1].glyphs)
    assert line2_text == f"{char}{text_after}"
