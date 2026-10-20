# -*- coding: utf-8 -*-
"""原局喜忌层 oracle 测试 (卷七论五行一 L1254-1270).

验收点:
  1. 大海水专条 (L309): 土由忌转喜(堤流); 金由喜转忌(金沉水底/助波澜)
  2. 火命金多: 忌金(火金交战/金多火熄), 缺木印待运补
  3. 土多泄极: 我生>=3 → 忌土(泄气极而本源竭, L1513)
  4. 大运喜忌双判: 纳音为主 + 支正五行中和 → 甲寅大溪水(纳音水忌+支寅木喜)=吉凶交杂转克为生
"""
import pytest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.luming.engine import from_bazi_chart


@pytest.fixture(scope="module")
def be():
    return BaziEngine()


def _xj(be, y, m, d, h, gender="female"):
    chart = be.compute((y, m, d, h), gender=gender)
    return from_bazi_chart(chart).xi_ji


class TestDaHaiShui1983:
    """1983.11.3 癸亥大海水 壬午时: 喜木泄秀/土堤流/火暖局; 忌水助波澜/金沉水底"""

    def test_130_dahai_xi_earth_not_ji(self, be):
        xj = _xj(be, 1983, 11, 3, 11)
        assert xj["year_element"] == "WATER"
        xi_els = {x["el"] for x in xj["xi"]}
        ji_els = {x["el"] for x in xj["ji"]}
        # L309 专条: 土转喜(堤流) 但为条件喜 (不忌他土, 死绝则吉, 生旺则泛滥)
        assert "EARTH" in xi_els
        assert "EARTH" not in ji_els
        earth = next(x for x in xj["xi"] if x["el"] == "EARTH")
        assert earth.get("conditional"), "大海水土应为条件喜(可堤不可过)"
        assert "死绝则吉" in earth["reason"]
        # 大海水专条命中时 xi 内火仅一条 (L340/L343 合并去重)
        fire = [x for x in xj["xi"] if x["el"] == "FIRE"]
        assert len(fire) == 1
        # 金由喜转忌 (金沉水底)
        assert "METAL" in ji_els
        assert "METAL" not in xi_els
        # 喜木泄秀/火暖局
        assert "WOOD" in xi_els and "FIRE" in xi_els
        # 忌水助波澜
        assert "WATER" in ji_els

    def test_131_dahai_luck_response_gold_ji(self, be):
        xj = _xj(be, 1983, 11, 3, 11)
        by_pillar = {r["pillar"]: r for r in xj["luck_response"]}
        assert by_pillar["JIAZI"]["resp"] == "犯忌"     # 甲子海中金 → 金沉水底
        assert by_pillar["BINGYIN"]["resp"] == "应喜"  # 丙寅炉中火 → 火暖局


class TestHuoming1987:
    """1987.10.28 丁卯炉中火 庚辰时: 三金环伺金多火熄, 需木运生扶"""

    def test_132_fire_ji_metal_xi_wood(self, be):
        xj = _xj(be, 1987, 10, 28, 7)
        assert xj["year_element"] == "FIRE"
        assert xj["counts"].get("METAL", 0) == 3
        xi_els = {x["el"] for x in xj["xi"]}
        ji_els = {x["el"] for x in xj["ji"]}
        assert "WOOD" in xi_els           # 木为火源 (巽地)
        # 逐柱专条: 丁卯炉中火喜巽地及秋冬 → 无静态忌金;
        # 金3位 → 太过判定"我克(财)过多力不能任" → 金入忌 (金多火熄)
        assert "METAL" in ji_els
        assert any("财" in x["reason"] for x in xj["ji"] if x["el"] == "METAL")
        miss = {m["el"] for m in xj["missing"]}
        assert "WOOD" in miss             # 印缺待木运补

    def test_133_fire_luck_transformed(self, be):
        xj = _xj(be, 1987, 10, 28, 7)
        by_pillar = {r["pillar"]: r for r in xj["luck_response"]}
        # 甲寅大溪水: 丁卯炉中火喜秋冬(水) + 支寅木(巽地) → 应喜 (转克为生, 批文大吉方向)
        assert by_pillar["JIAYIN"]["tone"] == "吉"
        # 丙辰沙中土: 沙中土非丁卯之喜忌 → 平
        assert by_pillar["BINGCHEN"]["tone"] == "平"


class TestShantouhuo1994:
    """1994.7.13 甲戌山头火 丁亥时: 三土泄火太过, 须借外运木火以补"""

    def test_134_earth_excess_ji(self, be):
        xj = _xj(be, 1994, 7, 13, 21)
        assert xj["counts"].get("EARTH", 0) == 3
        ji_earth = [x for x in xj["ji"] if x["el"] == "EARTH"]
        assert ji_earth
        # 泄极理由强化 (L1513: 火生土土旺而火痊)
        assert any("泄" in x["reason"] for x in ji_earth)
        xi_els = {x["el"] for x in xj["xi"]}
        assert "WOOD" in xi_els and "FIRE" in xi_els   # 木火补

    def test_135_shantou_luck_gengwu_mixed(self, be):
        xj = _xj(be, 1994, 7, 13, 21)
        by_pillar = {r["pillar"]: r for r in xj["luck_response"]}
        # 甲戌山头火专条: 喜春及夏(木火)/喜土及夏(乙亥) → 庚午路旁土=土属喜, 支午火属喜
        # → 应吉 (大运一路木火补山头火之不足, 批文"先苦后甜")
        assert by_pillar["GENGWU"]["tone"] == "吉"
        # 己巳大林木: 纳音木喜 → 应喜
        assert by_pillar["JISI"]["tone"] == "吉"
