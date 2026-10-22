# -*- coding: utf-8 -*-
"""流日口径统一守卫（2026-10-22）。

**本文件锁的是一条曾经坏掉的不变量：同一个问题，只能有一个答案。**

背景（实测，非推理）：
    同一出生数据（癸亥 甲寅 丁巳 戊午），问「2026 年农历七月十五的流日卦」：

        fast path（``calculate(target_year=2026, ...)``）
            → 流日卦 **升**，动爻 **九三**
        full path（``calculate()`` 不传 target_year，再把 target_year 传给 guajie）
            → 流日卦 **损**，动爻 **初九**

    两条路径产出**不同的卦名与动爻判词**。根因：fast path 走 gua6
    （一卦管 6 日、一爻一日），full path 走 hou5（《河洛真数》L390 每爻管 5 日），
    而分流靠 ``materialize_month_days`` **嗅探 payload 有无 day_no** —— 隐式契约。

处置（2026-10-22）：
    · 生产口径统一为 **gua6**（定稿口径），全量路径与 fast path 一致；
    · hou5 原典变体**保留**（``compute_liuri_stub(..., rule="hou5")``），
      由 ``tests/heluo/test_liuri_vs_original.py`` 按 L390 字面实例逐条对拍，
      **原典覆盖未被削弱**；
    · 分流改为**显式**：month 条目带 ``liuri_rule`` 标注，函数签名也收 ``rule`` 形参。

本文件断言：
    1. 两条路径对同一 (年, 月, 日) 必须给出**同一**流日卦名、动爻、六爻；
    2. 顶层 ``daily_hexagram`` 与 guajie 解出的流日卦必须同源一致；
    3. 月份条目必须**显式标注**流日口径，不得再靠形状嗅探。
"""
from __future__ import annotations

import unittest

from tongshu.engines.heluo import guajie as gj
from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.timeline_yun import materialize_month_days

_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_BIRTH_YEAR = 1983
_BIRTH_DATE = "1983-11-03"
_BIRTH_HOUR = "午"
_GENDER = "male"

_TARGET_YEAR = 2026
_TARGET_MONTH = 7
_TARGET_DAY = 15


def _build(target_year=None, target_month=None, target_day=None):
    hc = HeluoCanonical()
    return hc.calculate(
        bazi=_BAZI, gender=_GENDER, birth_hour=_BIRTH_HOUR,
        birth_year=_BIRTH_YEAR, birth_date=_BIRTH_DATE,
        target_year=target_year, target_month=target_month, target_day=target_day,
    )


def _month_of(res, year, month):
    """从 timeline 里取指定 (年, 月) 的月份条目（两条路径结构不同）。"""
    for y in res.timeline.yearly_hexagrams:
        if y.get("year") != year:
            continue
        for m in y.get("months") or []:
            if m.get("month") == month:
                return m
    for m in res.timeline.monthly_hexagrams or []:
        if m.get("month") == month:
            return m
    return None


def _pick_day(days, day):
    """从物化后的日条目里取出目标日那一条。"""
    for d in days:
        if d.get("day_from", 1) <= day <= d.get("day_to", 0):
            item = next((i for i in (d.get("day_items") or [])
                         if i.get("day") == day), None)
            return item or d
    return None


class TestLiuriRuleUnified(unittest.TestCase):
    """流日口径统一：fast path 与 full path 必须给出同一答案。"""

    @classmethod
    def setUpClass(cls):
        cls.fast = _build(target_year=_TARGET_YEAR,
                          target_month=_TARGET_MONTH, target_day=_TARGET_DAY)
        cls.full = _build()

    def test_same_day_same_hexagram_and_yao(self):
        """同一 (年,月,日) 的流日卦名、动爻位、六爻必须逐字一致。"""
        m_fast = _month_of(self.fast, _TARGET_YEAR, _TARGET_MONTH)
        m_full = _month_of(self.full, _TARGET_YEAR, _TARGET_MONTH)
        self.assertIsNotNone(m_fast)
        self.assertIsNotNone(m_full)

        d_fast = _pick_day(materialize_month_days(m_fast), _TARGET_DAY)
        d_full = _pick_day(materialize_month_days(m_full), _TARGET_DAY)
        self.assertIsNotNone(d_fast, "fast path 未物化出目标日")
        self.assertIsNotNone(d_full, "full path 未物化出目标日")

        self.assertEqual(d_fast.get("name"), d_full.get("name"),
                         "两条路径的流日卦名必须一致")
        self.assertEqual(d_fast.get("flip_index"), d_full.get("flip_index"),
                         "两条路径的流日动爻位必须一致")
        self.assertEqual(d_fast.get("lines"), d_full.get("lines"),
                         "两条路径的流日六爻必须一致")

    def test_guajie_verdict_identical_on_both_paths(self):
        """经 guajie 解出的**流日判词**必须逐字一致（这是用户真正看到的东西）。"""
        out_fast = gj.build_guajie_from_result(
            self.fast, bazi=_BAZI, target_year=_TARGET_YEAR,
            target_month=_TARGET_MONTH, target_day=_TARGET_DAY)
        out_full = gj.build_guajie_from_result(
            self.full, bazi=_BAZI, target_year=_TARGET_YEAR,
            target_month=_TARGET_MONTH, target_day=_TARGET_DAY)

        self.assertEqual(out_fast.get("liuri_hexagram"),
                         out_full.get("liuri_hexagram"),
                         "两条路径的流日卦名必须一致")
        yao_fast = out_fast.get("liuri_yao") or {}
        yao_full = out_full.get("liuri_yao") or {}
        self.assertEqual(yao_fast.get("yao"), yao_full.get("yao"),
                         "两条路径的流日动爻判词必须一致")
        self.assertEqual(yao_fast.get("ci"), yao_full.get("ci"),
                         "两条路径的流日爻辞必须一致")

    def test_top_level_daily_hexagram_matches_guajie_verdict(self):
        """顶层 daily_hexagram（定稿输出）与 guajie 解出的流日卦必须同源。"""
        d = self.fast.timeline.daily_hexagram or {}
        yao = d.get("daily_yao") or []
        self.assertTrue(yao, "daily_hexagram.daily_yao 为空")
        hit = next((x for x in yao if x.get("day_no") == _TARGET_DAY), None)
        self.assertIsNotNone(hit, "daily_yao 里找不到目标日")
        out = gj.build_guajie_from_result(
            self.fast, bazi=_BAZI, target_year=_TARGET_YEAR,
            target_month=_TARGET_MONTH, target_day=_TARGET_DAY)
        self.assertEqual(gj._short(hit.get("changed_name") or ""),
                         out.get("liuri_hexagram"),
                         "顶层 daily_hexagram 与 guajie 流日卦名应一致")

    def test_month_entries_declare_liuri_rule(self):
        """月份条目必须**显式标注**流日口径 —— 不再靠 payload 形状嗅探。"""
        m_fast = _month_of(self.fast, _TARGET_YEAR, _TARGET_MONTH)
        m_full = _month_of(self.full, _TARGET_YEAR, _TARGET_MONTH)
        self.assertEqual(m_fast.get("liuri_rule"), "gua6")
        self.assertEqual(m_full.get("liuri_rule"), "gua6")

    def test_full_path_months_use_gua6_segment_shape(self):
        """全量路径的月份日段是 gua6 形态：5 段 × 6 日，段首日 = 初爻。"""
        for y in self.full.timeline.yearly_hexagrams[:3]:
            for m in y.get("months") or []:
                self.assertEqual(len(m["days"]), 5)
                for k, seg in enumerate(m["days"]):
                    self.assertEqual(seg.get("rule"), "gua6")
                    self.assertEqual(seg.get("day_from"), k * 6 + 1)
                    self.assertEqual(seg.get("day_to"), k * 6 + 6)
                    self.assertEqual(seg.get("flip_index"), 0,
                                     "gua6 段首日 = 初爻")


if __name__ == "__main__":
    unittest.main()
