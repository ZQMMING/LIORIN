"""流年卦（小象行年卦气）逐岁变卦序列——原典演例逐岁核对。

《河洛真数·起例卷之上·小象行年卦气》给出三个完整演例，均以「天火同人」为先天卦：

1. 同人九三（阳爻, 阳年段首, 九年）：
   1岁同人九三 → 2岁革上六 → 3岁随六三 → 4岁屯六四 → 5岁复六五 →
   6岁颐上九 → 7岁剥初六 → 8岁蒙九二 → 9岁蛊九三
2. 同人九三（阳爻, 阴年段首, 九年）：
   1岁无妄六三 → 2岁随上六 → 3岁革九三 → 4岁既济六四 → 5岁明夷六五 →
   6岁贲上九 → 7岁艮初六 → 8岁蛊九二 → 9岁蒙六三
3. 同人六二（阴爻, 六年）：
   1岁乾九二 → 2岁履六三 → 3岁中孚六四 → 4岁损六五 → 5岁临上六 → 6岁师初六

其中第 3 例原文「不必取应，亦无阴阳之分」，故与段首年份无关。
"""
from __future__ import annotations

from tongshu.engines.heluo.guajie import hexagram_to_lines
from tongshu.engines.heluo.timeline_yun import compute_liunian

TONG_REN = hexagram_to_lines("同人")  # 下离上乾


def _seq(yt: int, birth_year: int, ages: int) -> list[str]:
    r = compute_liunian(TONG_REN, yt, TONG_REN, yt, birth_year, 1, ages)
    return [e.hexagram_name for e in r.years]


def test_sequence_yang_line_yang_year():
    # 2000 庚辰 阳年
    assert _seq(2, 2000, 9) == [
        "天火同人", "泽火革", "泽雷随", "水雷屯", "地雷复",
        "山雷颐", "山地剥", "山水蒙", "山风蛊",
    ]


def test_sequence_yang_line_yin_year():
    # 2001 辛巳 阴年
    assert _seq(2, 2001, 9) == [
        "天雷无妄", "泽雷随", "泽火革", "水火既济", "地火明夷",
        "山火贲", "艮为山", "山风蛊", "山水蒙",
    ]


def test_sequence_yin_line_six_years():
    # 阴爻段（六二）不取应、不分阴阳年
    assert _seq(1, 2000, 6) == [
        "乾为天", "天泽履", "风泽中孚", "山泽损", "地泽临", "地水师",
    ]
    assert _seq(1, 2001, 6) == _seq(1, 2000, 6)


def test_flip_line_handles_zero_convention():
    """0/1 爻值约定下翻转不能静默失败（D-014）。"""
    from tongshu.engines.heluo.timeline_yun import _flip_line

    zero_conv = [1, 0, 1, 1, 1, 1]
    out = _flip_line(zero_conv, 1)
    assert out[1] == 1  # 阴（0）翻为阳，不得静默保持 0
