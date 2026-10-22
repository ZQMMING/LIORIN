"""流日层按需化回归（2026-10-06 起；2026-10-22 口径统一后改写）

四层时间轴只为「命中应期的那一个月」付卦名换算代价。

改造前：``canonical._build_timeline`` 对 93 流年 × 12 月 = 1,116 个月逐月调
``compute_liuri``，每次 6 次 ``_lines_to_hexagram`` 卦名换算，合计 6,696 次。
而消费方 guajie 每次排盘只查**一个**月。

改造后：``_build_timeline`` 只产出 ``compute_liuri_stub`` —— 保留
segment/day_from/day_to/flip_index/lines（``_flip_line`` 仅复制 6 元 list，
近乎零成本），**去掉 name/upper/lower 三个卦名字符串**。
需要卦名时由 guajie 对命中的那一个月调 ``materialize_month_days`` 现算。

2026-10-22 口径统一：stub 默认改为 **gua6**（定稿口径 —— 一卦管 6 日、
一爻一日、首日从初爻起 → 每月 **5 段 × 6 日**）。此前默认 hou5（《河洛真数》
L390 原典变体 → 6 段 × 5 日），导致全量路径与 fast path 对同一 (年,月,日)
给出**不同的流日卦名与动爻**（实测 升/九三 vs 损/初九），即「同一个问题、
两种答案」。hou5 原典对拍**未被削弱**，改由 ``test_liuri_vs_original.py``
以 ``rule="hou5"`` 显式对拍。

本文件锁三件事：
  1. 口径一致：stub 物化后与**生产路径**（fast path 预置）逐字段一致
  2. gua6 的 flip_index / day_positions 语义（段内日序，首日从初爻）
  3. stub 确实省掉了卦名字段
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.timeline_yun import (
    compute_liuri,
    compute_liuri_stub,
    materialize_month_days,
)

_BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]


def _calc(**kw):
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午",
        era="zhong", birth_year=1724, **kw,
    )


class TestStubShape(unittest.TestCase):
    """stub 该有什么、不该有什么。"""

    @classmethod
    def setUpClass(cls):
        cls.yearly = _calc().timeline.yearly_hexagrams

    def test_each_month_has_five_gua6_segments(self):
        """每月**五段**（定稿口径：一卦管 6 日 → 5 段 × 6 日 = 30 日）。

        2026-10-22 口径统一前是六段（hou5：6 段 × 5 日）。统一后全量路径与
        fast path 的流日口径一致，见 ``TestMaterializeEquivalence``。
        """
        for y in self.yearly:
            for m in y["months"]:
                self.assertEqual(len(m["days"]), 5)
                self.assertEqual(m.get("liuri_rule"), "gua6",
                                 "月份须显式标注流日口径")

    def test_stub_omits_hexagram_name_lookup(self):
        """省掉的正是卦名换算产物。"""
        d = self.yearly[0]["months"][0]["days"][0]
        for dropped in ("name", "upper", "lower"):
            self.assertNotIn(dropped, d, f"{dropped} 应由命中时才物化")

    def test_stub_keeps_cheap_fields(self):
        d = self.yearly[0]["months"][0]["days"][0]
        for kept in ("segment", "day_from", "day_to", "flip_index", "lines"):
            self.assertIn(kept, d)
        self.assertEqual(len(d["lines"]), 6)


class TestMaterializeEquivalence(unittest.TestCase):
    """口径不变：物化结果与**生产路径**逐字一致。"""

    def test_materialize_matches_fast_path_precomputed(self):
        """全量路径物化出来的流日卦，必须与 fast path 预置的结果**逐字一致**。

        这是 2026-10-22 口径统一的核心不变式。此前两条路径分走 hou5/gua6，
        同一 (年,月,日) 给出**不同的流日卦名与动爻**（实测 升/九三 vs 损/初九），
        即「同一个问题、两种答案」。统一后本断言钉死。
        """
        full = _calc()
        fast = HeluoCanonical().calculate(
            bazi=_BAZI, gender="male", birth_hour="午",
            era="zhong", birth_year=1724,
            target_year=1724, target_month=6, target_day=15,
        )
        m_full = next(m for y in full.timeline.yearly_hexagrams
                      if y["year"] == 1724 for m in y["months"] if m["month"] == 6)
        m_fast = next(m for m in fast.timeline.monthly_hexagrams if m["month"] == 6)

        d_full = materialize_month_days(m_full)
        d_fast = materialize_month_days(m_fast)
        self.assertTrue(d_full, "全量路径物化出流日条目")
        self.assertTrue(d_fast, "fast path 物化出流日条目")

        def pick(days, day):
            for d in days:
                if d.get("day_from", 1) <= day <= d.get("day_to", 0):
                    it = next((i for i in (d.get("day_items") or [])
                               if i.get("day") == day), None)
                    return it or d
            return None

        a = pick(d_full, 15)
        b = pick(d_fast, 15)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertEqual(a.get("name"), b.get("name"), "同一日流日卦名应一致")
        self.assertEqual(a.get("flip_index"), b.get("flip_index"), "同一日变爻位应一致")
        self.assertEqual(a.get("lines"), b.get("lines"), "同一日六爻应一致")

    def test_gua6_flip_index_is_segment_day_order(self):
        """gua6 的 flip_index = **段内日序**（0-5，首日从初爻起）。

        2026-10-22 口径统一前，本断言用的是 hou5 的「阳日寻阳位/阴日寻阴位」
        序列（``liuri_day_positions``）；gua6 不使用该规则（见
        ``compute_daily_base_hex`` 落码说明）。
        """
        yearly = _calc().timeline.yearly_hexagrams
        checked = 0
        for y in yearly:
            for m in y["months"]:
                for k, d in enumerate(m["days"]):
                    self.assertEqual(d["flip_index"], 0,
                                     f"第{k + 1}段首日应为初爻（flip_index=0）")
                    self.assertEqual(d["day_positions"], [0, 1, 2, 3, 4, 5],
                                     f"第{k + 1}段段内爻位序列应为初→上")
                    self.assertEqual(len(d["day_lines"]), 6,
                                     f"第{k + 1}段应有 6 日六爻")
                    checked += 1
        self.assertGreater(checked, 5000, "应覆盖全部 1,116 个月 × 5 段")

    def test_stub_helper_matches_timeline_content(self):
        """compute_liuri_stub 与 _build_timeline 实际写入的 days 一致。"""
        m = _calc().timeline.yearly_hexagrams[3]["months"][7]
        self.assertEqual(compute_liuri_stub(m["lines"], m["yue_yao_index"]),
                         m["days"])


class TestGuajieStillResolvesDayAndHour(unittest.TestCase):
    """流日须正确解出；流时已于 2026-10-06 剥离，只断言剥离行为本身。"""

    def test_day_still_resolves(self):
        from tongshu.engines.heluo import guajie as gj
        out = gj.build_guajie_from_result(
            _calc(), bazi=_BAZI, target_year=1724, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertTrue(out["liuri_hexagram"], "流日卦未解出")
        self.assertIsNotNone(out["liuri_yao"], "流日动爻判词未解出")

    def test_hour_layer_is_stripped(self):
        """流时层已剥离：不产卦名、不产爻辞。"""
        from tongshu.engines.heluo import guajie as gj
        out = gj.build_guajie_from_result(
            _calc(), bazi=_BAZI, target_year=1724, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertEqual(out["liushi_hexagram"], "")
        self.assertIsNone(out["liushi_yao"])

    def test_passing_hour_leaves_visible_trace(self):
        """传了 target_hour 必须留痕——不得静默忽略。"""
        from tongshu.engines.heluo import guajie as gj
        out = gj.build_guajie_from_result(
            _calc(), bazi=_BAZI, target_year=1724, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertTrue(any("流时：已剥离" in e for e in out["evidence"]),
                        "传入 target_hour 必须在 evidence 留痕")

    def test_hour_layer_stripped_even_without_hour_arg(self):
        from tongshu.engines.heluo import guajie as gj
        out = gj.build_guajie_from_result(
            _calc(), bazi=_BAZI, target_year=1724, target_month=6, target_day=15)
        self.assertEqual(out["liushi_hexagram"], "")
        self.assertFalse(any("流时：已剥离" in e for e in out["evidence"]),
                         "未传 target_hour 时无需留痕")

    def test_compute_liushi_capability_preserved(self):
        """compute_liushi 本体保留在 timeline_yun，未来恢复不必重写。"""
        from tongshu.engines.heluo.timeline_yun import compute_liushi
        r = compute_liushi([1, -1, 1, -1, 1, 1], 3)
        self.assertEqual(len(r.hours), 12)
        self.assertEqual([h["hour"] for h in r.hours], list(range(1, 13)))


if __name__ == "__main__":
    unittest.main()