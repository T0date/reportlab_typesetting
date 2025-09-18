import pytest

from reportlab_typesetting.alignment import BlockAligner
from reportlab_typesetting.datatypes import (
    Font,
    Glyph,
    HAlign,
    LineLayout,
    TextLayout,
    VAlign,
)


@pytest.fixture
def test_font() -> Font:
    """テスト用のFontオブジェクトを返すフィクスチャ"""
    return Font("Helvetica")


@pytest.fixture
def sample_layout(test_font: Font) -> TextLayout:
    """
    テスト用のTextLayoutオブジェクトを生成する。
    このレイアウトのバウンディングボックスは (left=10, bottom=100, width=80, height=62) となる。
    """
    layout = TextLayout()
    glyph1 = Glyph(
        text="H", font=test_font, font_size=12, x=10, y=150, width=80, line=0
    )
    glyph2 = Glyph(
        text="W", font=test_font, font_size=10, x=20, y=100, width=70, line=1
    )
    layout.add_line(LineLayout(index=0, glyphs=[glyph1]))
    layout.add_line(LineLayout(index=1, glyphs=[glyph2]))
    return layout


@pytest.mark.parametrize(
    "halign, valign, expected_left, expected_bottom",
    [
        # Top alignment
        (HAlign.LEFT, VAlign.TOP, 10, 100),
        (HAlign.CENTER, VAlign.TOP, 70, 100),
        (HAlign.RIGHT, VAlign.TOP, 130, 100),
        # Middle alignment
        (HAlign.LEFT, VAlign.MIDDLE, 10, -19),
        (HAlign.CENTER, VAlign.MIDDLE, 70, -19),
        (HAlign.RIGHT, VAlign.MIDDLE, 130, -19),
        # Bottom alignment
        (HAlign.LEFT, VAlign.BOTTOM, 10, -138),
        (HAlign.CENTER, VAlign.BOTTOM, 70, -138),
        (HAlign.RIGHT, VAlign.BOTTOM, 130, -138),
    ],
)
def test_block_aligner_apply_alignment(
    sample_layout: TextLayout,
    halign: HAlign,
    valign: VAlign,
    expected_left: float,
    expected_bottom: float,
):
    """
    BlockAlignerが水平・垂直方向の配置を正しく適用することをテストする。
    """
    # Arrange
    block_width = 200
    block_height = 300

    # `sample_layout`の初期BBoxは (left=10, bottom=100, width=80, height=62)
    initial_bbox = sample_layout.get_content_bbox()
    assert initial_bbox is not None
    layout_width, layout_height = initial_bbox[2], initial_bbox[3]

    aligner = BlockAligner(sample_layout, width=block_width, height=block_height)

    # Act
    aligned_layout = aligner.alignment(horizontal=halign, vertical=valign).apply()
    final_bbox = aligned_layout.get_content_bbox()

    # Assert
    assert final_bbox is not None
    final_left, final_bottom, final_width, final_height = final_bbox

    # レイアウト自体の寸法は変わらないはず
    assert final_width == pytest.approx(layout_width)
    assert final_height == pytest.approx(layout_height)

    # 配置後の座標が期待通りであることを確認
    assert final_left == pytest.approx(expected_left)
    assert final_bottom == pytest.approx(expected_bottom)
