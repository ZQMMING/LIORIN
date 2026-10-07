"""H11 节候卦覆盖修复回归（2026-10-06）

锁定 `get_current_jieqi_info` 的接通断点。

原状：函数 docstring 声称「使用 sxtwl 查找最近一个已过节气」，实现却是

    d = sxtwl.fromSolar(year, month, day)
    jq_idx = d.getJieQi()
    if jq_idx < 0 or jq_idx > 23:
        return None

而 ``Day.getJieQi()`` **只在交节当天返回索引**，其余日期一律返回哨兵 255。
于是节候卦一年只有约 24 天可取、354 天直接判 None——生产上
``HeluoResult.seasonal_hexagram`` 绝大多数时候是 ``None``，H11 整层形同虚设。

实测修复效果（见各断言）：
  覆盖率 24/366 天 → 366/366 天；24 个交节当日本身结果逐字不变。

本文件只加新用例，**不改 test_h11_jiehhou.py 既有任何断言**。
"""
from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

try:
    import sxtwl  # noqa: F401
    _HAS_SXTWL = True
except ImportError:  # pragma: no cover
    _HAS_SXTWL = False

from tongshu.engines.heluo.jiehhou import (
    SOLAR_TERMS,
    _JQ_NO_JIEQI_SENTINEL,
    _JIEQI_TIMELINE,
    _JIEQI_TIMELINE_MAX,
    SeasonalHexagram,
    get_current_jieqi_info,
)


def _days_of(year: int):
    d = date(year, 1, 1)
    end = date(year, 12, 31)
    while d <= end:
        yield d
        d += timedelta(days=1)


@unittest.skipUnless(_HAS_SXTWL, "需要 sxtwl")
class TestJiehouFullYearCoverage(unittest.TestCase):
    """核心断点：节候卦必须全年可取，而非仅交节当日。"""

    def test_every_day_of_year_has_jieqi(self):
        """1984 全年 366 天都必须拿到节候卦——修复前只有 24 天能拿到。"""
        missing = [str(d) for d in _days_of(1984)
                   if get_current_jieqi_info(d.year, d.month, d.day) is None]
        self.assertEqual(missing, [], f"{len(missing)} 天拿不到节候卦")

    def test_leap_year_coverage(self):
        missing = [str(d) for d in _days_of(2024)
                   if get_current_jieqi_info(d.year, d.month, d.day) is None]
        self.assertEqual(missing, [])

    def test_coverage_across_decades(self):
        """跨年代也要全覆盖，不能只在某些年份成立。"""
        for y in (1901, 1955, 1976, 2000, 2026, 2050):
            missing = [str(d) for d in _days_of(y)
                       if get_current_jieqi_info(d.year, d.month, d.day) is None]
            self.assertEqual(missing, [], f"{y} 年有 {len(missing)} 天缺口")


@unittest.skipUnless(_HAS_SXTWL, "需要 sxtwl")
class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容：交节当日本身的结果不得改变。"""

    def test_jieqi_day_matches_raw_sxtwl(self):
        """24 个交节当日：旧 getJieQi() 结果 == 新函数结果，逐日比对。"""
        same, mismatch = 0, []
        for d in _days_of(2026):
            raw = sxtwl.fromSolar(d.year, d.month, d.day).getJieQi()
            if not (0 <= raw <= 23):
                continue
            info = get_current_jieqi_info(d.year, d.month, d.day)
            if info is not None and info.jq_index == raw:
                same += 1
            else:
                mismatch.append((str(d), raw, getattr(info, "jq_index", None)))
        self.assertEqual(same, 24, f"应恰好 24 个交节日，实得 {same}")
        self.assertEqual(mismatch, [], "交节当日结果被改动了")

    def test_jq_names_come_from_canonical_table(self):
        """节候卦名必须出自 SOLAR_TERMS，不得自造。"""
        for d in _days_of(2026):
            info = get_current_jieqi_info(d.year, d.month, d.day)
            self.assertIn(info.jq_name, SOLAR_TERMS)
            self.assertEqual(info.jq_name, SOLAR_TERMS[info.jq_index])


@unittest.skipUnless(_HAS_SXTWL, "需要 sxtwl")
class TestCrossYearBoundary(unittest.TestCase):
    """跨年：1 月初仍属上一年的节气，且 getJieQiByYear 窗口需合并两年。"""

    def test_early_january_uses_previous_year_term(self):
        # 2026-01-05 小寒；2026-01-01 仍属 2025-12-22 起的冬至
        self.assertEqual(get_current_jieqi_info(2026, 1, 5).jq_name, "小寒")
        self.assertEqual(get_current_jieqi_info(2026, 1, 1).jq_name, "冬至")

    def test_january_terms_are_reachable(self):
        """1 月的节气必须查得到（单年 getJieQiByYear 窗口不覆盖 1 月）。"""
        names = {get_current_jieqi_info(2026, 1, d).jq_name for d in range(1, 32)}
        self.assertIn("小寒", names)
        self.assertIn("大寒", names)

    def test_terms_change_on_the_jieqi_day(self):
        """交节日当天即切换到新节气。"""
        prev = get_current_jieqi_info(2026, 2, 3).jq_index   # 立春前一天
        cur = get_current_jieqi_info(2026, 2, 4).jq_index    # 立春当日
        self.assertNotEqual(prev, cur)


@unittest.skipUnless(_HAS_SXTWL, "需要 sxtwl")
class TestSentinelContract(unittest.TestCase):
    """哨兵 255 是本修复的分派依据，契约不得漂移。"""

    def test_sentinel_value(self):
        self.assertEqual(_JQ_NO_JIEQI_SENTINEL, 255)

    def test_raw_getjieqi_only_returns_255_outside_range(self):
        """实证：0..23 之外的取值有且只有 255。"""
        outside = set()
        for d in _days_of(2030):
            v = sxtwl.fromSolar(d.year, d.month, d.day).getJieQi()
            if not (0 <= v <= 23):
                outside.add(v)
        self.assertEqual(outside, {255},
                         "若 sxtwl 改了哨兵，本修复的 255 分派即失效")


@unittest.skipUnless(_HAS_SXTWL, "需要 sxtwl")
class TestEndToEndSeasonalHexagram(unittest.TestCase):
    """端到端：HeluoResult.seasonal_hexagram 必须真的有值。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.canonical import HeluoCanonical
        cls.canonical = HeluoCanonical()
        cls.pillars = [("庚", "午"), ("辛", "巳"), ("庚", "辰"), ("壬", "申")]

    def _calc(self, birth_date: str):
        return self.canonical.calculate(
            bazi=self.pillars, gender="male", birth_hour="申", era="zhong",
            birth_year=int(birth_date[:4]), birth_date=birth_date,
        )

    def test_seasonal_hexagram_present_for_non_jieqi_birthdays(self):
        """选的都是**非交节日**：修复前这些出生日一律拿不到节候卦。"""
        for bd in ("1990-05-20", "1984-12-25", "2000-01-01", "1976-08-15"):
            r = self._calc(bd)
            self.assertIsNotNone(
                r.seasonal_hexagram,
                f"{bd} 拿不到节候卦——修复前 354/366 天都是这种情况")
            for key in ("jq_index", "jq_name", "main_gua",
                        "moving_line", "result_gua", "evidence"):
                self.assertIn(key, r.seasonal_hexagram)

    def test_seasonal_hexagram_agrees_with_layer(self):
        """HeluoResult 的节候卦须与 get_current_jieqi_info 同源同值。"""
        r = self._calc("1990-05-20")
        direct = get_current_jieqi_info(1990, 5, 20)
        self.assertEqual(r.seasonal_hexagram["jq_index"], direct.jq_index)
        self.assertEqual(r.seasonal_hexagram["main_gua"], direct.main_gua)

    def test_winter_solstice_hexiagram_matches_classic(self):
        """原典 L1492：「节卦坎初六起冬至……每卦总管九十日，
        自下而上，每一爻各直十五日。」

        旧本守卫引的「冬至一索得中男，颐六四爻动，为地雷复卦」经原著
        全库检索**零命中**，不是《河洛真数》原句，已于 2026-10-07 订正。
        """
        r = self._calc("1984-12-25")     # 1984 冬至为 12-22，此日仍属冬至
        sh = r.seasonal_hexagram
        self.assertEqual(sh["jq_name"], "冬至")
        self.assertEqual(sh["main_gua"], "坎")
        self.assertEqual(sh["result_gua"], "初六")
        self.assertEqual(sh["moving_line"], 0)


class TestCacheIsBounded(unittest.TestCase):
    """缓存不得无界增长（长期服务会缓慢涨内存）。"""

    def test_timeline_cache_has_cap(self):
        self.assertLessEqual(_JIEQI_TIMELINE_MAX, 256)

    def test_canonical_jie_cache_has_cap(self):
        import tongshu.engines.heluo.canonical as cn
        self.assertLessEqual(cn._JIE_CACHE_MAX, 1024)

    def test_canonical_jie_cache_evicts_when_over_cap(self):
        """塞满超过上限的年份，最旧的应被淘汰，总量不失控。"""
        import tongshu.engines.heluo.canonical as cn
        saved_cache, saved_compute = cn._jie_cache, cn._compute_year_jie
        try:
            cn._jie_cache = {}
            cn._compute_year_jie = lambda year, sxtwl=None: {}
            for year in range(1900, 1900 + cn._JIE_CACHE_MAX + 50):
                cn._jie_datetime_for_lunar_month(year, 6)
            self.assertLessEqual(len(cn._jie_cache), cn._JIE_CACHE_MAX)
            self.assertIn(1949 + cn._JIE_CACHE_MAX, cn._jie_cache,
                          "最新的年份应留在缓存里")
            self.assertNotIn(1900, cn._jie_cache, "最旧的年份应被淘汰")
        finally:
            cn._jie_cache, cn._compute_year_jie = saved_cache, saved_compute


if __name__ == "__main__":
    unittest.main()