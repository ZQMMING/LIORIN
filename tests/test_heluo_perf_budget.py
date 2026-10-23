# -*- coding: utf-8 -*-
"""算力基准守卫（2026-10-22）。

**为什么要有**：本引擎曾经发生过一次严重的算力退化事故 ——
独立包曾「删测试让全绿」，实测单盘输出体积 10MB → **65MB**（6.3 倍），
原因是批次 P 的 fast-path 丢失（逐月预展开 6,696 次卦名换算回来了）。
指标全绿、测试全过，但**载荷爆了 6 倍** —— 没有任何守卫拦住它。

本类把「算力」变成可回归的断言：
  · fast path（生产路径）：单盘耗时、载荷体积
  · 全量路径（fallback）：载荷体积（防止逐月预展开复活）
  · 流日段数与卦名换算次数（按需化的核心收益）

阈值取值原则：**留足冗余**（按实测值 × 2-4 倍），只拦「数量级退化」，
不拦季节性波动 —— 计时断言在 CI 机器上容易抖，故用宽松阈值并允许
在极慢机器上以明确信息失败，而不是悄悄放过。

实测基准（本机，2026-10-22）：

    fast path（生产）：单盘 26.3 ms，载荷 18,472 字符
    full path（回退）：单盘 124.2 ms，载荷 2,109,221 字符
"""
from __future__ import annotations

import dataclasses
import time
import unittest

from heluo_engine.engines.heluo.canonical import HeluoCanonical

_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_BIRTH_YEAR = 1983
_BIRTH_DATE = "1983-11-03"
_TARGET_YEAR = 2026
_TARGET_MONTH = 7
_TARGET_DAY = 15

#: fast path 单盘耗时上限（秒）。实测约 0.03s，留 ~40 倍冗余。
_FAST_TIME_LIMIT_S = 2.0

#: fast path 载荷上限（字符）。定稿估算 ~2.8 万，留 3 倍冗余。
_FAST_PAYLOAD_LIMIT = 100_000

#: 全量路径载荷上限（字符）。**实测 2,109,221**（≈2.1MB），留近 2 倍冗余。
#: 历史事故值 65MB ≈ 65,000,000 字符 —— 本阈值比它小一个数量级还多，
#: 即：只要有人把逐月预展开（批次 P 丢失的 fast-path）放回来，立刻会红。
_FULL_PAYLOAD_LIMIT = 4_000_000


def _calc(**kw):
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午",
        birth_year=_BIRTH_YEAR, birth_date=_BIRTH_DATE, **kw,
    )


def _payload_chars(res) -> int:
    """整棵结果树的字符数（与既有 dump 工具同口径：dataclasses.asdict）。"""
    return len(str(dataclasses.asdict(res)))


class TestFastPathCost(unittest.TestCase):
    """生产路径（fast path）的算力预算。"""

    @classmethod
    def setUpClass(cls):
        cls.t0 = time.perf_counter()
        cls.res = _calc(target_year=_TARGET_YEAR,
                        target_month=_TARGET_MONTH, target_day=_TARGET_DAY)
        cls.elapsed = time.perf_counter() - cls.t0

    def test_single_chart_time_within_budget(self):
        """单盘耗时在预算内（防止批次 P 的 fast-path 再丢失）。"""
        self.assertLess(
            self.elapsed, _FAST_TIME_LIMIT_S,
            f"单盘耗时 {self.elapsed:.3f}s 超出预算 {_FAST_TIME_LIMIT_S}s")

    def test_payload_within_budget(self):
        """单盘载荷在预算内（历史事故：10MB → 65MB，6.3 倍）。"""
        n = _payload_chars(self.res)
        self.assertLess(
            n, _FAST_PAYLOAD_LIMIT,
            f"fast path 载荷 {n} 字符超出预算 {_FAST_PAYLOAD_LIMIT}")

    def test_timeline_only_payload_also_small(self):
        """只取 timeline 子树亦须小（timeline 是体积大头）。"""
        n = len(str(dataclasses.asdict(self.res.timeline)))
        self.assertLess(n, _FAST_PAYLOAD_LIMIT,
                        f"timeline 载荷 {n} 字符超出预算")


class TestFullPathPayloadBounded(unittest.TestCase):
    """全量路径（fallback）的载荷也必须有界。

    历史事故：独立包丢掉 fast-path 后，逐月预展开回来，
    单盘输出 65MB —— 全量路径正是那时的形态，故此处设硬上限。
    """

    def test_full_path_payload_bounded(self):
        res = _calc()
        n = _payload_chars(res)
        self.assertLess(
            n, _FULL_PAYLOAD_LIMIT,
            f"全量路径载荷 {n} 字符超出预算 {_FULL_PAYLOAD_LIMIT}；"
            "疑为逐月预展开复活（批次 P fast-path 丢失）")


class TestLazyComputationStillLazy(unittest.TestCase):
    """按需化的**结构性**收益：不看计时，只看结构。

    这类断言比计时稳定得多，是真正拦得住退化的那一层。
    """

    @classmethod
    def setUpClass(cls):
        cls.fast = _calc(target_year=_TARGET_YEAR,
                         target_month=_TARGET_MONTH, target_day=_TARGET_DAY)

    def test_only_target_year_has_months(self):
        """fast path：只有**目标年**有 12 个流月卦，近 3 年的另两年没有。"""
        years = {y["year"] for y in self.fast.timeline.yearly_hexagrams}
        self.assertEqual(years, {_TARGET_YEAR - 2, _TARGET_YEAR - 1, _TARGET_YEAR})
        for y in self.fast.timeline.yearly_hexagrams:
            if y["year"] == _TARGET_YEAR:
                self.assertEqual(len(y["months"]), 12)
            else:
                self.assertEqual(len(y.get("months") or []), 0,
                                 "非目标年不应算流月卦（算力裁剪）")

    def test_only_target_month_has_day_segments(self):
        """fast path：只有**目标月**有日段，其余 11 个月为空。"""
        months = self.fast.timeline.monthly_hexagrams
        self.assertEqual(len(months), 12)
        with_days = [m for m in months if m.get("days")]
        self.assertEqual(len(with_days), 1, "只有目标月该有日段")
        self.assertEqual(with_days[0]["month"], _TARGET_MONTH)

    def test_daily_hexagram_carries_one_hexagram_six_yao(self):
        """顶层流日 = 1 个本卦 + 6 日激活爻（不预展开 30 日）。"""
        d = self.fast.timeline.daily_hexagram or {}
        self.assertEqual(len(d.get("daily_yao") or []), 6)
        self.assertTrue(d.get("base_hex"))

    def test_yearly_meta_is_pure_metadata(self):
        """其余流年只存 {year, age, ganzhi} 纯元数据，不起卦。"""
        meta = self.fast.timeline.yearly_meta
        self.assertEqual(len(meta), 96, "96 条纯元数据")
        for e in meta[:5]:
            self.assertEqual(set(e.keys()), {"year", "age", "ganzhi"},
                             "yearly_meta 只能是纯元数据")


if __name__ == "__main__":
    unittest.main()
