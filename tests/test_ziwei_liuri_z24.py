# -*- coding: utf-8 -*-
"""Z24: 流日论断（消费八字引擎日柱）测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.decadal import build_liuri_fortune


def _chart():
    engine = ZiweiEngine()
    return engine.full_chart((1983, 9, 29), 11, "male")


class TestLiuRi:
    def test_20260315_ganzhi(self):
        """2026-03-15 日柱戊子（消费八字引擎）"""
        r = build_liuri_fortune(_chart(), 2026, 3, 15)
        assert r["stem"] == "戊"
        assert r["branch"] == "子"

    def test_20260315_palace(self):
        """戊子日流日落官禄宫（命宫地支辰起数）"""
        r = build_liuri_fortune(_chart(), 2026, 3, 15)
        assert r["palace"] == "官禄"

    def test_20260315_sihua(self):
        """戊干四化：贪狼/太阴/右弼/天机"""
        r = build_liuri_fortune(_chart(), 2026, 3, 15)
        assert r["sihua"] == ["贪狼", "太阴", "右弼", "天机"]

    def test_20260901(self):
        """2026-09-01 戊寅日 → 福德宫"""
        r = build_liuri_fortune(_chart(), 2026, 9, 1)
        assert r["branch"] == "寅"
        assert r["palace"] == "福德"

    def test_20260105(self):
        """2026-01-05 己卯日 → 父母宫（己干四化武曲/贪狼/天梁/文曲）"""
        r = build_liuri_fortune(_chart(), 2026, 1, 5)
        assert r["stem"] == "己"
        assert r["branch"] == "卯"
        assert r["palace"] == "父母"
        assert r["sihua"][0] == "武曲"

    def test_assertions(self):
        """流日断言非空"""
        r = build_liuri_fortune(_chart(), 2026, 3, 15)
        assert len(r["assertions"]) >= 1
