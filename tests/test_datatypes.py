import pytest

from reportlab_typesetting.datatypes import Font, Glyph, LineLayout, TextLayout


@pytest.fixture
def test_font():
    """テスト用のFontオブジェクトを返すフィクスチャ"""
    # ReportLabの標準フォントを使用し、ファイルI/Oを避ける
    return Font("Helvetica")


def test_text_layout_get_content_bbox(test_font):
    """複数のGlyphを持つTextLayoutのバウンディングボックスが正しく計算されることをテストする"""
    # Arrange: 複数の行とグリフを持つレイアウトを準備
    layout = TextLayout()
    # 1行目のグリフ
    glyph1 = Glyph(
        text="A", font=test_font, font_size=12, x=10, y=100, width=20, line=0
    )
    glyph2 = Glyph(
        text="B", font=test_font, font_size=12, x=40, y=100, width=30, line=0
    )
    # 2行目のグリフ
    glyph3 = Glyph(text="C", font=test_font, font_size=10, x=20, y=50, width=15, line=1)

    line1 = LineLayout(index=0, glyphs=[glyph1, glyph2])
    line2 = LineLayout(index=1, glyphs=[glyph3])

    layout.add_line(line1)
    layout.add_line(line2)

    # Act: バウンディングボックスを計算
    bbox = layout.get_content_bbox()

    # Assert: 計算結果が期待通りであることを確認
    assert bbox is not None
    left, bottom, width, height = bbox

    # 期待値の計算:
    # left   = min(g.x)                  = min(10, 40, 20) = 10
    # right  = max(g.x + g.width)        = max(30, 70, 35) = 70
    # bottom = min(g.y)                  = min(100, 100, 50) = 50
    # top    = max(g.y + g.font_size)    = max(112, 112, 60) = 112
    # width  = right - left              = 70 - 10 = 60
    # height = top - bottom              = 112 - 50 = 62
    expected_left = 10
    expected_bottom = 50
    expected_width = 60
    expected_height = 62

    assert left == pytest.approx(expected_left)
    assert bottom == pytest.approx(expected_bottom)
    assert width == pytest.approx(expected_width)
    assert height == pytest.approx(expected_height)


def test_text_layout_get_content_bbox_single_glyph(test_font):
    """単一のGlyphを持つTextLayoutのバウンディングボックスが正しく計算されることをテストする"""
    # Arrange
    layout = TextLayout()
    glyph = Glyph(text="X", font=test_font, font_size=12, x=50, y=80, width=10, line=0)
    line = LineLayout(index=0, glyphs=[glyph])
    layout.add_line(line)

    # Act
    bbox = layout.get_content_bbox()

    # Assert
    assert bbox is not None
    left, bottom, width, height = bbox

    # 期待値の計算:
    # left   = glyph.x = 50
    # bottom = glyph.y = 80
    # width  = glyph.width = 10
    # height = glyph.font_size = 12

    assert left == pytest.approx(50)
    assert bottom == pytest.approx(80)
    assert width == pytest.approx(10)
    assert height == pytest.approx(12)


def test_text_layout_get_content_bbox_empty():
    """行やグリフが全くない場合にget_content_bboxがNoneを返すことをテストする"""
    # Arrange
    layout = TextLayout()

    # Act
    bbox = layout.get_content_bbox()

    # Assert
    assert bbox is None


def test_text_layout_get_content_bbox_whitespace_only(test_font):
    """空白文字のグリフしかない場合にget_content_bboxがNoneを返すことをテストする"""
    # Arrange
    layout = TextLayout()
    glyph1 = Glyph(text=" ", font=test_font, font_size=12, x=10, y=100, width=5, line=0)
    glyph2 = Glyph(
        text="\t", font=test_font, font_size=12, x=20, y=100, width=10, line=0
    )
    line1 = LineLayout(index=0, glyphs=[glyph1, glyph2])
    layout.add_line(line1)

    # Act
    bbox = layout.get_content_bbox()

    # Assert
    assert bbox is None
