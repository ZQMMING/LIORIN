"""Heluo 时间序列算力裁剪 fast-path 守卫（2026-10-10 批次 P 第二步）。

防止裁剪回归：
    · 97 段必须有 months 子树缺口（防"为了过时间复测把 months 全展开"）
    · 97 段必须没有 yi_signal / yi_interpretation（dead-write 钉死不可复活）
    · 目标/上一年 2 段必须嵌满 12 月 + 6 日（防"只嵌目标年、忘上一年对比动爻"）
    · 顶层 monthly_hexagrams 必须 12 项
    · 顶层 daily_hexagram 必须有 6 段且 segment/day_from/day_to/flip_index 齐
    · target_year=None 必须退回全量（旧契约冻结保留）
    · 总体积 < 50k chars（1983-11-03 12:00 男 / target=2026/7）—— 锁住
      25 倍压缩成果

只断言调用方的**可见契约**（yearly/monthly_hexagrams/daily_hexagram 形状
与字段集合），不绑实现细节（不测 `_build_timeline` 内部、不测哈希）。
"""

from __future__ import annotations

import dataclasses
import json
import unittest
from datetime import date

from tongshu.engines.heluo.canonical import HeluoCanonical


_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_BIRTH_YEAR = 1983
_BIRTH_DATE = "1983-11-03"
_TARGET_YEAR = 2026
_TARGET_MONTH = 7  # 农历七月（黄历权威值，目标流月与日段链式累变）
_BIRTH_HOUR = "午"
_GENDER = "male"


def _full_to_dict(res) -> dict:
    """把 HeluoResult 序列化为 dict（与现有 dump 工具同口径）。"""
    return dataclasses.asdict(res)


def _timeline_to_dict(res) -> dict:
    """只取 timeline 子树，避免 hua_gong / seasonal / structure 等抖动干扰。"""
    return dataclasses.asdict(res.timeline)


def _build(target_year=None, target_month=None):
    """单次 build（与 production path 一致：canonical.calculate 直调）。"""
    hc = HeluoCanonical()
    return hc.calculate(
        bazi=_BAZI,
        gender=_GENDER,
        birth_hour=_BIRTH_HOUR,
        birth_year=_BIRTH_YEAR,
        birth_date=_BIRTH_DATE,
        target_year=target_year,
        target_month=target_month,
    )


class TestFastPathSkeleton(unittest.TestCase):
    """fast-path 骨架 / 体积 / 月日顶层契约。"""

    def test_yearly_skeleton_preserved(self):
        """99 流年骨架完整保留——大运段判定、年份定位都依赖它。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        yearly = res.timeline.yearly_hexagrams
        self.assertEqual(len(yearly), 99,
                         "流年骨架必须保留 99 段")
        # 每年 entry 必含 10 个元数据字段；目标/上一年 2 段额外含 months
        for e in yearly:
            keys = set(e.keys())
            for k in EXPECTED_META_KEYS:
                self.assertIn(k, keys, f"流年 entry 缺 {k}")
            # 元数据 97 段：必不含 months / yi_* / days
            if not e.get("months"):
                self.assertNotIn("yi_signal", keys)
                self.assertNotIn("yi_interpretation", keys)
                self.assertNotIn("days", keys)
                self.assertNotIn("hours", keys)
            else:
                # 全量段：可以含 months（11 字段），yi_* 必须不在
                self.assertNotIn("yi_signal", keys,
                                 f"年份 {e['year']} 全量段含 yi_signal（dead-write）")
                self.assertNotIn("yi_interpretation", keys,
                                 f"年份 {e['year']} 全量段含 yi_interpretation")

    def test_only_target_and_prev_year_have_months(self):
        """仅目标年 + 上一年 2 段嵌 months 子树；其余 97 段必须只有元数据。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        yearly = res.timeline.yearly_hexagrams
        full = [e for e in yearly if e.get("months")]
        meta = [e for e in yearly if not e.get("months")]
        self.assertEqual(len(full), 2,
                         f"应 2 段全量（目标+上一年），实测 {len(full)}")
        self.assertEqual(len(meta), 97,
                         f"应 97 段只元数据，实测 {len(meta)}")
        self.assertEqual({_TARGET_YEAR, _TARGET_YEAR - 1},
                         {e["year"] for e in full})

    def test_metadata_segments_have_no_yield_or_yi(self):
        """97 段元数据禁止包含 yi_signal / yi_interpretation / months / days
        ——这些是 dead-write（仓内零消费方），必须钉死不可复活。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        for e in res.timeline.yearly_hexagrams:
            if e.get("months"):
                continue
            self.assertNotIn("yi_signal", e,
                             f"年份 {e['year']} 元数据竟含 yi_signal，"
                             f"这是 dead-write 不得复活")
            self.assertNotIn("yi_interpretation", e,
                             f"年份 {e['year']} 元数据竟含 yi_interpretation")
            self.assertNotIn("days", e,
                             f"年份 {e['year']} 元数据竟含 days")
            self.assertNotIn("hours", e,
                             f"年份 {e['year']} 元数据竟含 hours")

    def test_target_year_has_12_months_each_with_6_days(self):
        """目标年段 12 月 × 每月 6 日段（廉价字段，不换卦名）。

        日段必含 segment/day_from/day_to/flip_index 四件套 + 可选 lines/positions。
        不钉 schema 全集——避免与下游 materialize_month_days 联动字段绑死。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        target_yr = next(e for e in res.timeline.yearly_hexagrams
                         if e["year"] == _TARGET_YEAR)
        months = target_yr["months"]
        self.assertEqual(len(months), 12)
        for i, m in enumerate(months, start=1):
            self.assertEqual(m["month"], i)
            self.assertEqual(len(m["days"]), 6,
                             f"第 {i} 月理应有 6 日段")
            for d in m["days"]:
                for k in ("segment", "day_from", "day_to", "flip_index"):
                    self.assertIn(k, d, f"日段缺 {k}：{d}")

    def test_top_level_monthly_hexagrams_filled(self):
        """顶层 monthly_hexagrams 是目标年 12 月（扁平路径）。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        m = res.timeline.monthly_hexagrams
        self.assertEqual(len(m), 12)
        for i, x in enumerate(m, start=1):
            self.assertEqual(x["month"], i)

    def test_top_level_daily_hexagram_filled(self):
        """顶层 daily_hexagram 含 6 段 + 年/月锚。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        d = res.timeline.daily_hexagram
        self.assertEqual(d.get("year"), _TARGET_YEAR)
        self.assertEqual(d.get("month"), _TARGET_MONTH)
        segs = d.get("segments")
        self.assertIsInstance(segs, list)
        self.assertEqual(len(segs), 6)
        for s in segs:
            self.assertIn("segment", s)
            self.assertIn("day_from", s)
            self.assertIn("day_to", s)
            self.assertIn("flip_index", s)

    def test_daily_hexagram_empty_when_target_month_unspecified(self):
        """target_month 未传 → 顶层 daily_hexagram 保持空（guajie 由 yearly 现取）。"""
        res = _build(target_year=_TARGET_YEAR, target_month=None)
        d = res.timeline.daily_hexagram
        self.assertEqual(d, {})

    def test_total_size_within_budget(self):
        """timeline 子树 < 100k chars（基线 2.0M），锁住 20× 压缩成果。

        1983-11-03 12:00 男 / target=2026/7 这盘实测 ~85k；留一倍冗余到 100k
        防小波动。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        tl_dict = _timeline_to_dict(res)
        s = json.dumps(tl_dict, ensure_ascii=False, default=str)
        self.assertLess(len(s), 100_000,
                        f"timeline 体积 {len(s)} ≥ 100k（基线 2.14M）")


class TestFastPathDisabled(unittest.TestCase):
    """target_year=None 退回全量（旧契约冻结保留）。"""

    def test_no_target_year_means_full_payload(self):
        """target_year 未传 → 全部 99 段都嵌 months + yi_* —— 锁旧契约。
        防止有人"为了减少差异化"把 None 路径也走轻量。"""
        res = _build(target_year=None, target_month=None)
        yearly = res.timeline.yearly_hexagrams
        # 全量路径：每段都嵌 12 月
        none_with_months = [e for e in yearly if not e.get("months")]
        self.assertEqual(len(none_with_months), 0,
                         "全量路径下所有流年段都必须有 months")
        # 全量路径：仍调 interpret_all_liunian → 每段都带 yi_signal
        none_with_yi = [e for e in yearly if "yi_signal" not in e]
        self.assertEqual(len(none_with_yi), 0,
                         "全量路径下所有流年段都必须有 yi_signal（interpret_all_liunian）")
        # 顶层 monthly_hexagrams 必须保持 []（旧契约：注释自承"占位恒空"）
        self.assertEqual(res.timeline.monthly_hexagrams, [])
        # 顶层 daily_hexagram 必须 {}（旧契约）
        self.assertEqual(res.timeline.daily_hexagram, {})

    def test_full_path_payload_is_baseline(self):
        """全量路径排盘结果 baseline 不变 —— 这条是关键回归保险，
        防 fast-path 改造无意识地污染了全量路径的实现。
        基线：1983-11-03 12:00 男 → ~2.0M chars。"""
        res = _build(target_year=None, target_month=None)
        full = _full_to_dict(res)
        s = json.dumps(full, ensure_ascii=False, default=str)
        # 期望落在旧基线 2.0M 区间：允许 ±20% 抖动（其他改动可能扩/缩）
        self.assertGreater(len(s), 1_500_000,
                           f"全量路径体积 {len(s)} 跌破旧基线 1.5M（疑似被 fast-path 污染）")
        self.assertLess(len(s), 3_000_000,
                        f"全量路径体积 {len(s)} ≥ 3M（疑似引入了额外冗余）")


EXPECTED_META_KEYS = {
    "age", "year", "ganzhi", "yang_year", "hexagram",
    "upper", "lower", "lines",
    "yuantang_index", "yuantang_nature",
}


if __name__ == "__main__":
    unittest.main()
