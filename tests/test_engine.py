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


@pytest.mark.parametrize(
    "numeric_string",
    [
        "12345",  # プレーンな数字
        "12,345",  # カンマ区切り
        "12.345",  # 小数点
        "-1234",  # 前置マイナス
        "-12.34",  # 前置マイナスと小数点
        "-1,234",  # 前置マイナスとカンマ
    ],
    ids=[
        "plain_number",
        "comma_separated",
        "decimal_point",
        "leading_minus_integer",
        "leading_minus_float",
        "leading_minus_comma",
    ],
)
def test_layout_cjk_numeric_chunk_no_wrapping(numeric_string):
    """
    CJKテキスト内の様々な形式の数字が、折り返しなしの場合に1つのグリフとして扱われることをテストする。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    block_width = float("inf")

    text = f"あいうえ{numeric_string}かきくけ"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    assert len(layout.lines) == 1

    assert len(layout.lines[0].glyphs) == 9
    assert layout.lines[0].glyphs[4].text == numeric_string

    line_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line_text == text


@pytest.mark.parametrize(
    "numeric_string",
    [
        "12345",  # プレーンな数字
        "12,345",  # カンマ区切り
        "12.345",  # 小数点
        "-1234",  # 前置マイナス
        "-12.34",  # 前置マイナスと小数点
        "-1,234",  # 前置マイナスとカンマ
    ],
    ids=[
        "plain_number",
        "comma_separated",
        "decimal_point",
        "leading_minus_integer",
        "leading_minus_float",
        "leading_minus_comma",
    ],
)
def test_layout_cjk_numeric_chunk_wrapping(numeric_string):
    """
    CJKテキスト内の数字のまとまりが行頭に来る場合に、分割されずに次行に送られることをテストする。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # "あいうえ" (幅48) は収まるが、次の数字のまとまりは収まらない幅に設定。
    block_width = 49

    text = f"あいうえ{numeric_string}かきくけ"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == "あいうえ"

    # 2行目が数字のまとまり全体で始まっていることを確認する
    # (block_widthが狭いため、その後ろでさらに改行される可能性がある)
    assert len(layout.lines) > 1
    assert layout.lines[1].glyphs[0].text == numeric_string


@pytest.mark.parametrize(
    "alpha_string",
    [
        "English",
        "word",
        "alphabet",
        "abc's",
        "don't",
    ],
    ids=["long_word", "short_word", "medium_word", "possessive", "contraction"],
)
def test_layout_cjk_alpha_chunk_no_wrapping(alpha_string):
    """
    CJKテキスト内のアルファベットのまとまりが、折り返しなしの場合に1つのグリフとして扱われることをテストする。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    block_width = float("inf")

    text = f"あいうえ{alpha_string}かきくけ"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    assert len(layout.lines) == 1
    assert len(layout.lines[0].glyphs) == 9
    assert layout.lines[0].glyphs[4].text == alpha_string
    line_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line_text == text


@pytest.mark.parametrize(
    "alpha_string",
    [
        "English",
        "word",
        "alphabet",
        "abc's",
        "don't",
    ],
    ids=["long_word", "short_word", "medium_word", "possessive", "contraction"],
)
def test_layout_cjk_alpha_chunk_wrapping(alpha_string):
    """
    CJKテキスト内のアルファベットのまとまりが行頭に来る場合に、分割されずに次行に送られることをテストする。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # "あいうえ" (幅48) は収まるが、次のEnglishの単語は収まらない幅に設定。
    block_width = 50

    text = f"あいうえ{alpha_string}かきくけ"

    # Act
    layout = engine.layout(text, width=block_width, font_size=font_size)

    # Assert
    line1_text = "".join(g.text for g in layout.lines[0].glyphs)
    assert line1_text == "あいうえ"

    # 2行目がアルファベットのまとまり全体で始まっていることを確認する
    assert len(layout.lines) > 1
    assert layout.lines[1].glyphs[0].text == alpha_string


@pytest.mark.parametrize(
    "alpha_string",
    [
        "English",
    ],
    ids=["long_word"],
)
def test_layout_cjk_alpha_chunk_wrapping_with_pyphenation(alpha_string):
    """
    CJKテキスト内のアルファベットのまとまりが行頭に来る場合に、分割されずに次行に送られることをテストする。
    """
    # Arrange
    engine = LayoutEngine()
    font = Font(name="HeiseiKakuGo-W5", word_wrap="CJK")
    engine.add_font(font)

    font_size = 12
    # "あいうえ" (幅48) は収まるが、次のEnglishの単語は収まらない幅に設定。
    block_width = 85

    text = f"あいうえ{alpha_string}かきくけ"

    # Act
    layout = engine.layout(
        text, width=block_width, font_size=font_size, use_hyphenation=True
    )

    # Assert
    # 単語の途中で分割されていることを確認する
    assert layout.lines[0].glyphs[-1].text == "Eng-"
    assert layout.lines[1].glyphs[0].text == "lish"
