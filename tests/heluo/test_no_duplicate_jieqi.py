"""批次 L 守卫：河洛层对 sxtwl 的重复计算（2026-10-08）

用户口径：「不要重复计算，容易出问题和重复计算导致引擎计算增大」。

实测（count_calls.py，一次真实排盘）：
    改前  sxtwl.fromSolar 224   sxtwl.getJieQiByYear 282
    改后  sxtwl.fromSolar  40   sxtwl.getJieQiByYear 195

三处改动：
  1. canonical.py 与 guajie.py 各有一份**逐字相同**的 `_find_jie`，
     靠逐日扫整月调 sxtwl.fromSolar（一次 ~92 次），两处合计 184 次做同一件事
  2. canonical 的农历月起点**直调** sxtwl.getJieQiByYear，绕过已有缓存，
     在一条流年时间轴上打 279 次
  3. getJieQiByYear 是按年取全量节气 —— 剩的 190 次对应流年时间轴
     跨的 ~186 个不同年份，是**真实需求**不是重复

**关键回归**：改快路径时把 JD2DD 的时刻抹成 00:00。
本批守卫的重点不是「变快了」，是**没变错**。
"""
from __future__ import annotations

import io
import unittest
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"


class TestJieqiLookupIsCachedNotRescanned(unittest.TestCase):
    def test_solar_term_date_exists_and_matches_dayscan(self):
        """逐日扫描是基准；查表必须与之逐日相等（不是「抽样像对」）。"""
        from datetime import timedelta
        import sxtwl
        from tongshu.engines.heluo.jiehhou import solar_term_date

        def scan(y, m, jq):
            d0 = date(y, m, 1)
            found = d0
            while d0.month == m:
                if sxtwl.fromSolar(d0.year, d0.month, d0.day).getJieQi() == jq:
                    found = d0
                d0 += timedelta(days=1)
            return found

        bad = []
        for y in range(1900, 2101, 11):        # 19 个年份，覆盖两个世纪
            for jq, m in ((0, 12), (12, 6)):
                a, b = scan(y, m, jq), solar_term_date(y, jq)
                if a != b:
                    bad.append((y, jq, a, b))
        self.assertEqual(bad, [], "查表与逐日扫描不等价：%s" % bad[:3])

    def test_both_find_jie_sites_use_the_cached_lookup(self):
        """两处**逐字相同**的 _find_jie 都必须改，否则重复计算还在。"""
        for f in ("canonical.py", "guajie.py"):
            src = io.open(_E / f, encoding="utf-8").read()
            self.assertIn("solar_term_date", src,
                          "%s 仍在用逐日扫描" % f)
            i = src.index("def _find_jie")
            j = src.index("\ndef ", i + 10)
            self.assertNotIn("sxtwl.fromSolar(d0", src[i:j],
                             "%s 的 _find_jie 又退回逐日扫描了" % f)

    def test_no_duplicate_dayscan_implementation_left(self):
        """全 heluo 扫一遍：不该再有第二份「逐日扫整月找节」的代码。"""
        hits = []
        for f in _E.glob("*.py"):
            src = io.open(f, encoding="utf-8").read()
            if "getJieQi() == jq" in src:
                hits.append(f.name)
        self.assertEqual(hits, [],
                         "仍有文件在逐日扫节气：%s" % hits)

    def test_lunar_month_timeline_routes_through_cache(self):
        """canonical 的农历月起点必须经缓存入口，不能直调 sxtwl。"""
        src = io.open(_E / "canonical.py", encoding="utf-8").read()
        self.assertIn("jieqi_timeline(target)", src,
                      "农历月起点未走缓存表")
        self.assertIn("hh_, mm_", src, "解包缺时刻 → 节气时刻会被抹成 00:00")

    def test_timeline_keeps_time_component(self):
        """⚠ 本批真正的回归点：时刻不能丢。

        第一版改快路径时把 JD2DD 换成 (Y,M,D)，时刻被抹成 00:00，
        由 test_timeline_yun_perf::test_batch_matches_dayscan 当场逮到。
        """
        src = io.open(_E / "canonical.py", encoding="utf-8").read()
        # 解包在 for 那一行，取它前面的 80 字
        i = src.index("in jieqi_timeline(target)") + len(
            "in jieqi_timeline(target)")
        block = src[max(0, i - 90):i + 900]
        self.assertIn("hh_, mm_", block, "解包缺时刻")
        self.assertIn("{hh_:02d}:{mm_:02d}", block,
                      "输出里没有回填真实时刻")
        self.assertNotIn("00:00\")", block,
                         "农历月起点里又出现硬写的 00:00 —— 时刻被抹掉了")

    def test_jieqi_timeline_returns_time(self):
        from tongshu.engines.heluo.jiehhou import jieqi_timeline
        rows = jieqi_timeline(2026)
        self.assertTrue(rows)
        # 首行可能是**上一年**的节气（表含跨年项），故全量校验
        for y, m, d, hh, mm, jq in rows:
            self.assertTrue(0 < y <= 2200, "年份异常：%s" % y)
            self.assertTrue(1 <= m <= 12, "月异常：%s" % m)
            self.assertTrue(1 <= d <= 31, "日异常：%s" % d)
            self.assertTrue(0 <= hh <= 23, "时刻字段异常：%s" % hh)
            self.assertTrue(0 <= mm <= 59, "分钟字段异常：%s" % mm)
            self.assertTrue(0 <= jq < 24)
        # 24 个节气齐全
        self.assertEqual({r[5] for r in rows}, set(range(24)),
                         "全年 24 个节气不齐：%d 个" % len({r[5] for r in rows}))

    def test_cache_actually_caches(self):
        """同一年的两次调用必须是同一对象（真命中缓存，不是重建）。"""
        from tongshu.engines.heluo import jiehhou
        a = jiehhou.jieqi_timeline(2026)
        b = jiehhou.jieqi_timeline(2026)
        self.assertIs(a, b, "第二次调用没命中缓存")


if __name__ == "__main__":
    unittest.main()