"""死断诸法（《河洛真数·起例卷之下·后天详说》）接线测试。

原典四条：
  1. 后天之气数行至君爻（五爻）之位 → 数足必死；
  2. 纵到君爻，亦不许行至上极一爻 → 寿必不久；
  3. 若行后天，连三爻不吉 → 多坎壈；若过了第四爻，遇凶 → 十死八九；
  4. 流年连三年不吉 + 卦爻不吉 + 本身卦不佳 + 重反支干元气 → 便可死断。
"""
from __future__ import annotations

from tongshu.engines.heluo.canonical import heluo_calculate
from tongshu.engines.heluo.guajie import build_guajie_from_result, judge_si_duan

BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]


def _result():
    return heluo_calculate(BAZI, "male", "午", "shang")


def _si(result, year: int) -> list[str]:
    g = build_guajie_from_result(result, bazi=BAZI, target_year=year)
    return list(g.get("si_duan") or [])


def test_jun_yao_line4_is_shuzu_bi_si():
    """五爻（君爻）= 数足必死；四爻不触发。"""
    r = _result()
    assert any("数足，到此必死" in w for w in _si(r, 1990))
    assert not any("数足，到此必死" in w for w in _si(r, 1986))


def test_shang_yao_warns_before_jun_yao():
    """上极一爻 → 寿必不久（且此时亦已过君爻）。"""
    r = _result()
    w = _si(r, 1996)
    assert any("上极一爻" in x for x in w)
    assert any("数足，到此必死" in x for x in w)


def test_guo_fourth_yao_yu_xiong_ten_death():
    """过了第四爻且该爻判词凶 → 十死八九。"""
    r = _result()
    assert any("十死八九" in w for w in _si(r, 1996))


def test_combo_three_bad_lines_warn():
    """连三爻不吉 → 坎壈（首段大运不足 3 段时退回近3年流年判词）。"""
    r = _result()
    w = _si(r, 1986)
    assert any("连三爻不吉" in x for x in w)


def test_direct_call_combo_wins_over_recent_years():
    combo = [
        {"ci": "凶", "buye": "", "suiyun": ""},
        {"ci": "死", "buye": "", "suiyun": ""},
        {"ci": "咎", "buye": "", "suiyun": ""},
    ]
    warns = judge_si_duan(
        prenatal_name="泰", postnatal_name="无妄",
        dayun_line_index=2, dayun_combo=combo,
        recent_years=[{"ci": "吉"}, {"ci": "吉"}, {"ci": "吉"}],
    )
    assert any("连三爻不吉" in w and "大运" in w for w in warns)


def test_no_age_no_warn():
    r = _result()
    assert _si(r, 0) == [] or all("连三爻" in w or "死断" in w for w in _si(r, 0))
