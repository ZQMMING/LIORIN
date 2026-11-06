"""流日卦原典演例（《河洛真数·起例卷之上·起日卦例》）。

原文：
  假如正月得乾卦初爻，初一日当在三爻，变为履六三，初二日变履九四为中孚六四，
  初三日变中孚九五为损六五，初四日变损上九为临上六，初五日变临初九为师初六，
  挨次而变，不容紊也。

要点（D-015 修正的判据）：
  1. 链式累积：每段在上段结果上变下一位（非"各段以月卦独立变一位"）。
  2. 起爻：阳日寻阳位（初/三/五），阴日寻阴位（二/四/上），
     故乾初九居位、初一为阳日 → 起于三爻（index=2）。
  3. 每爻管五日，六爻俱变毕满三十日。
"""

from tongshu.engines.heluo.timeline_yun import compute_liuri

QIAN = [1, 1, 1, 1, 1, 1]  # 乾为天（阳=1/阴=0 约定）


def test_qian_chu_jiu_chain_matches_book_example():
    """乾初九居位、阳日：履 → 中孚 → 损 → 临 → 师 → 坤（逐段链式变爻）。"""
    r = compute_liuri(QIAN, 0)
    names = [d["name"] for d in r.days]
    assert names == ["天泽履", "风泽中孚", "山泽损", "地泽临", "地水师", "坤为地"]


def test_qian_chu_jiu_flip_positions_are_sequential():
    """动爻位自三爻起挨次上行：2,3,4,5,0,1（不容紊）。"""
    r = compute_liuri(QIAN, 0)
    assert [d["flip_index"] for d in r.days] == [2, 3, 4, 5, 0, 1]


def test_first_segment_starts_on_yang_position():
    """阳日起爻必落阳位（初/三/五），乾初九居位的下一位=三爻。"""
    r = compute_liuri(QIAN, 0, yang_day=True)
    first = r.days[0]
    assert first["flip_index"] in (0, 2, 4)
    assert first["flip_index"] == 2


def test_yin_day_starts_on_yin_position():
    """阴日起爻必落阴位（二/四/上）：乾初九居位 → 二爻起。"""
    r = compute_liuri(QIAN, 0, yang_day=False)
    assert [d["flip_index"] for d in r.days][0] in (1, 3, 5)
    assert [d["flip_index"] for d in r.days][0] == 1
    assert r.days[0]["name"] == "天火同人"


def test_segments_cover_five_days_each():
    """每爻管五日，六段共三十日，day_from/day_to 连续无重。"""
    r = compute_liuri(QIAN, 0)
    assert len(r.days) == 6
    for k, d in enumerate(r.days):
        assert d["day_from"] == k * 5 + 1
        assert d["day_to"] == k * 5 + 5
    assert r.days[-1]["day_to"] == 30


def test_chain_accumulates_lines_not_redraw():
    """链式判据：段k 与月卦的不同爻位数 = k+1（非恒为 1）。"""
    r = compute_liuri(QIAN, 0)
    for k, d in enumerate(r.days):
        diffs = [i for i in range(6) if d["lines"][i] != QIAN[i]]
        assert len(diffs) == k + 1
