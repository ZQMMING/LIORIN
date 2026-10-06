"""流日层按需化回归（2026-10-06）

四层时间轴只为「命中应期的那一个月」付卦名换算代价。

改造前：``canonical._build_timeline`` 对 93 流年 × 12 月 = 1,116 个月逐月调
``compute_liuri``，每次 6 次 ``_lines_to_hexagram`` 卦名换算，合计 6,696 次。
而消费方 guajie 每次排盘只查**一个**月。

改造后：``_build_timeline`` 只产出 ``compute_liuri_stub``——保留
segment/day_from/day_to/flip_index/lines（``_flip_line`` 仅复制 6 元 list，
近乎零成本），**去掉 name/upper/lower 三个卦名字符串**。
需要卦名时由 guajie 对命中的那一个月调 ``materialize_month_days`` 现算。

本文件锁三件事：
  1. 口径不变：stub 物化后与旧 ``compute_liuri`` 逐字段完全一致
  2. flip_index 闭式公式与「逐爻 diff 求唯一差异爻」全量等价
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

    def test_each_month_still_has_six_segments(self):
        """既有契约：每月六段（《起日卦例》六爻俱变毕，则满三十日）。"""
        for y in self.yearly:
            for m in y["months"]:
                self.assertEqual(len(m["days"]), 6)

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
    """口径不变：物化结果与改造前逐字段一致。"""

    def test_materialize_matches_compute_liuri(self):
        yearly = _calc().timeline.yearly_hexagrams
        mism = []
        for y in yearly[:8]:
            for m in y["months"]:
                new = materialize_month_days(m)
                old = compute_liuri(m["lines"], m["yue_yao_index"],
                                    m.get("jie_datetime")).days
                for k in range(6):
                    o, n = dict(old[k]), dict(new[k])
                    o["flip_index"] = (m["yue_yao_index"] + 1 + k) % 6
                    for key in ("segment", "day_from", "day_to",
                                "flip_index", "name", "upper", "lower", "lines"):
                        if o.get(key) != n.get(key):
                            mism.append((y["year"], m["month"], k, key))
        self.assertEqual(mism, [], f"物化结果与旧算法不一致：{mism[:5]}")

    def test_flip_index_equals_single_line_diff(self):
        """闭式公式 ≡ 逐爻 diff 求唯一差异爻（flip_index 的原始定义）。"""
        yearly = _calc().timeline.yearly_hexagrams
        checked = 0
        for y in yearly:
            for m in y["months"]:
                ml = m["lines"]
                for d in m["days"]:
                    diffs = [i for i in range(6)
                             if len(d["lines"]) > i and len(ml) > i
                             and d["lines"][i] != ml[i]]
                    self.assertEqual(len(diffs), 1,
                                     "日段相对月卦应恰好变一爻")
                    self.assertEqual(d["flip_index"], diffs[0])
                    checked += 1
        self.assertGreater(checked, 6000, "应覆盖全部 1,116 个月 × 6 段")

    def test_stub_helper_matches_timeline_content(self):
        """compute_liuri_stub 与 _build_timeline 实际写入的 days 一致。"""
        m = _calc().timeline.yearly_hexagrams[3]["months"][7]
        self.assertEqual(compute_liuri_stub(m["lines"], m["yue_yao_index"]),
                         m["days"])


class TestGuajieStillResolvesDayAndHour(unittest.TestCase):
    """按需化后 guajie 仍须正确解出流日/流时——否则就是省错了地方。"""

    def test_day_and_hour_still_resolve(self):
        from tongshu.engines.heluo import guajie as gj
        out = gj.build_guajie_from_result(
            _calc(), bazi=_BAZI, target_year=1724, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertTrue(out["liuri_hexagram"], "流日卦未解出")
        self.assertTrue(out["liushi_hexagram"], "流时卦未解出（需物化日段六爻）")
        self.assertEqual(out["liunian_year"], 1724)


if __name__ == "__main__":
    unittest.main()