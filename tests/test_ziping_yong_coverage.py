"""子平用神覆盖率锚点：原典 21 案回放（PZZQ 沈孝瞻断语为真值）。

V7.182 起，格用神按八格原典判据派生（透干十神 + 藏干计数），
用神覆盖率由 2/12 提升到 11/12；本测试把该数字固化为护栏，
并逐案锁定原典明文可裁的用神五行，防止回退。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from engines.production_entry import FrozenCanonicalBaziChart, production_entry

REPO = Path(__file__).resolve().parent.parent

CASES = [
    (["癸未", "辛酉", "甲申", "丙寅"], "火"),  # 官多同煞，以丙火制官
    (["丁卯", "丙午", "丙子", "壬辰"], "水"),  # 煞刃格以煞制刃
    (["乙酉", "甲申", "丁巳", "庚戌"], "金"),  # 以庚劈甲引丁
    (["辛酉", "丙申", "庚子", "丙戌"], "火"),  # 煞刃格合一留一
    (["丙子", "壬辰", "壬申", "乙巳"], "木"),  # 乙木余气透干泄秀
    (["戊辰", "甲寅", "丁卯", "己酉"], "金"),  # 印旺取财损印
    (["辛卯", "丁酉", "庚午", "丙子"], "火"),  # 丁火制辛
    (["癸巳", "丁巳", "丁卯", "丙午"], "水"),  # 取年上癸水抑制
    (["己卯", "丁丑", "癸丑", "乙卯"], "木"),  # 食神制煞
    (["壬寅", "戊申", "丙寅", "癸巳"], "水"),  # 合官留煞
    (["甲子", "丁卯", "己亥", "戊辰"], "火"),  # 以印化官(杨增新) V7.191 扩案
    (["戊戌", "甲子", "己巳", "戊辰"], "木"),  # 用官制劫护财 V7.191 扩案
    (["戊寅", "己未", "甲寅", "乙亥"], "土"),  # 甲用己财(日主合财) V7.191 扩案
    (["庚午", "乙酉", "甲子", "乙亥"], "金"),  # 合煞留官(高太尉) V7.191 扩案
]


def _medicine(pillars):
    pl = {pos: [p[0], p[1]] for pos, p in zip(("year", "month", "day", "hour"), pillars)}
    result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
    return ((result.get("zhenglun") or {}).get("yongyao") or {})


@pytest.mark.parametrize("pillars,expected_wuxing", CASES)
def test_yong_wuxing_matches_classic_case(pillars, expected_wuxing):
    yy = _medicine(pillars)
    pm = yy.get("primary_medicine") or {}
    assert pm.get("wuxing") == expected_wuxing


def test_qisha_jiuying_baizhongyoucheng_tan_yankai():
    """V7.199 救应篇明文(PZZQ L1210/L1212 谭延闿案亲证): 食神制煞而中隔以财,
    「财逢煞而食神制煞以生, 有救应, 即是败中有成, 为贵也」——V7.198 曾因
    tier<2 不满足 .007 成句落 NOT_EVALUABLE 断用神链路(NE 被 _usable_ge_cheng
    拒绝); 现按救应通道判 CZP, 用神=食神(木)恢复。"""
    pl = {pos: [s, b] for pos, (s, b) in zip(
        ("year", "month", "day", "hour"),
        (("己", "卯"), ("丁", "丑"), ("癸", "丑"), ("乙", "卯")))}
    result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
    gc = (result.get("engine_result") or {}).get("ge_cheng") or {}
    assert gc.get("ge") == "七煞格(败中有成)", gc
    assert gc.get("cheng_bai") == "CHENG_ZHONG_YOU_PO", gc
    assert "败中有成" in (gc.get("rule") or "")
    yy = (result.get("zhenglun") or {}).get("yongyao") or {}
    pm = yy.get("primary_medicine") or {}
    assert pm.get("wuxing") == "木", pm


def test_yong_coverage_at_least_10_of_12():
    """原典 21 案（含 6 案已知口径冲突/配合分歧）整体覆盖率护栏。"""
    spec = importlib.util.spec_from_file_location(
        "ziping_pzzq_replay", REPO / "scripts" / "ziping_pzzq_replay.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run(verbose=False) >= 15
