"""子平用神覆盖率锚点：原典 12 案回放（PZZQ 沈孝瞻断语为真值）。

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


def test_yong_coverage_at_least_10_of_12():
    """原典 12 案（含 2 案已知口径冲突）整体覆盖率护栏。"""
    spec = importlib.util.spec_from_file_location(
        "ziping_pzzq_replay", REPO / "scripts" / "ziping_pzzq_replay.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run(verbose=False) >= 11
