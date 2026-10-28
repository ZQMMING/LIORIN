# -*- coding: utf-8 -*-
"""出生年份解析守卫 —— 同一出生数据，判词不得因 birth_year 传不传而变（2026-10-22）。

**缺陷**：``canonical.calculate`` 原先不解析出生年份，``birth_year=None`` 一路传到
``_build_timeline``，在那里被**硬编码成 1984（甲子年）** 作占位。

**后果**：1984 与真实出生年**不同余 60**（除非出生年恰是 1984/1924/2044…），
于是 ``compute_liunian`` 的 ``year = birth_year + age - 1`` 算出的流年干支
**整体错位一年** → 流年卦 → 流月卦 → 流日卦**整条链**的判词都错，
而**全程无任何报错或留痕**。

**实测（修复前）**：同一盘（癸亥 甲寅 丁巳 戊午 / 1983-11-03 午时 男）
  · 传 birth_year=1983 → 流日「升」九三，流年卦 泽火革
  · 不传 birth_year     → 流日「艮」九三，流年卦 乾为天

**修复**：未提供 birth_year 时**优先取 birth_date 的公历年**；再无则从 bazi
年柱干支反推（干支 60 年一循环，故取解集任一年皆得同一串流年干支）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.canonical import (
    HeluoCanonical,
    _birth_year_from_ganzhi,
)
from heluo_engine.engines.heluo import guajie as gj

_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_BIRTH_DATE = "1983-11-03"
_TARGET = dict(target_year=2026, target_month=7, target_day=15)


def _calc(**kw):
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午", era="zhong",
        birth_date=_BIRTH_DATE, **_TARGET, **kw)


def _verdict(res):
    out = gj.build_guajie_from_result(res, bazi=_BAZI, **_TARGET)
    yao = out.get("liuri_yao") or {}
    d = res.timeline.daily_hexagram or {}
    return {
        "liunian": (res.timeline.target_year_hexagram or {}).get("hexagram"),
        "liuri": out.get("liuri_hexagram"),
        "yao": yao.get("yao"),
        "base": (d.get("base_hex") or {}).get("name"),
    }


class TestBirthYearResolution(unittest.TestCase):
    """出生年份的解析。"""

    def test_explicit_birth_year_used(self):
        v = _verdict(_calc(birth_year=1983))
        self.assertEqual(v["liunian"], "泽火革")

    def test_birth_date_year_used_when_birth_year_missing(self):
        """不传 birth_year 时取 birth_date 的公历年（1983）。"""
        v = _verdict(_calc())
        self.assertEqual(v["liunian"], "泽火革",
                         "应与显式传 birth_year=1983 完全一致")

    def test_verdict_identical_with_or_without_birth_year(self):
        """★ 核心断言：传不传 birth_year，判词必须逐字一致。"""
        a = _verdict(_calc(birth_year=1983))
        b = _verdict(_calc())
        self.assertEqual(a, b,
                         f"birth_year 传不传导致判词不同：{a} vs {b}")

    def test_not_the_old_1984_placeholder(self):
        """回归：不得回落到 1984（甲子年）占位。"""
        v = _verdict(_calc())
        self.assertNotEqual(v["liunian"], "乾为天",
                            "这是 1984 占位时的流年卦，说明占位未除")

    def test_ganzhi_reverse_is_congruent_mod_60(self):
        """年柱干支反推的年份，与真实年份**同余 60**（流年干支才一致）。"""
        y = _birth_year_from_ganzhi("癸", "亥")
        self.assertEqual((y - 1983) % 60, 0,
                         "反推年份须与真实出生年同余 60")

    def test_reverse_covers_all_sixty_ganzhi(self):
        """60 甲子每一个干支都须能反推出年份。"""
        from heluo_engine.engines.heluo.timeline_yun import BRANCHES, _year_gan
        seen = set()
        for y in range(1900, 1960):
            seen.add((_year_gan(y), BRANCHES[(y - 4) % 12]))
        self.assertEqual(len(seen), 60, "一个甲子周期应覆盖 60 干支")
        for g, z in seen:
            yy = _birth_year_from_ganzhi(g, z)
            self.assertEqual((_year_gan(yy), BRANCHES[(yy - 4) % 12]), (g, z),
                             f"{g}{z} 反推失败")


class TestBirthYearPlaceholderIsFlagged(unittest.TestCase):
    """两者皆无 → 占位 1984，且**必须在判词里留痕**。"""

    def test_placeholder_is_flagged_in_evidence(self):
        """缺失输入被当成真实输入，比答错更坏 → 必须留痕。"""
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        res = HeluoCanonical().calculate(
            bazi=_BAZI, gender="male", birth_hour="午", era="zhong")
        self.assertEqual(res.birth_year_source, "placeholder")
        self.assertEqual(res.birth_year, 1984)
        out = gj.build_guajie_from_result(
            res, bazi=_BAZI, target_year=2026, target_month=7, target_day=15)
        joined = " ".join(out.get("evidence") or [])
        self.assertIn("出生年：占位", joined,
                      "占位推流年必须在 evidence 里留痕")

    def test_explicit_and_derived_are_not_flagged(self):
        """给了 birth_year 或 birth_date → 不留占位痕。"""
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        for kw, expect in (({"birth_year": 1983}, "explicit"),
                            ({}, "from_birth_date")):
            res = HeluoCanonical().calculate(
                bazi=_BAZI, gender="male", birth_hour="午", era="zhong",
                birth_date=_BIRTH_DATE, **_TARGET, **kw)
            self.assertEqual(res.birth_year_source, expect)
            out = gj.build_guajie_from_result(
                res, bazi=_BAZI, **_TARGET)
            joined = " ".join(out.get("evidence") or [])
            self.assertNotIn("出生年：占位", joined)

    def test_placeholder_keeps_legacy_timeline_window(self):
        """占位时**维持既有流年区间**（不因修复而改变既有行为）。"""
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        res = HeluoCanonical().calculate(
            bazi=_BAZI, gender="male", birth_hour="午", era="zhong")
        years = {y["year"] for y in res.timeline.yearly_hexagrams}
        self.assertIn(2026, years, "占位时 2026 仍应落在流年区间内")


if __name__ == "__main__":
    unittest.main()
