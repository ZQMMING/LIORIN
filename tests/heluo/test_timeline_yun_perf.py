"""河洛四层时间轴：性能改造回归（2026-10-06）

本文件锁定本轮四项性能改造的**行为不变量**，防止优化悄悄改算法口径：

  ① 流时卦按需化：_build_timeline 不再预展开 hours，只留 flip_index；
     guajie 命中 target_hour 时现算，结果须与旧预展开逐条一致。
  ② interpret_all_liunian 顶层浅拷贝：须返回新列表/新顶层对象，且不改原列表。
  ③ sxtwl 惰性单例：缺依赖时只解析一次，失败不反复试探 import。
  ④ 大运 _lines_to_hexagram 提出循环；流年大运段游标查找口径不变。

另锁定 guajie.to_dict() 补发三个应期卦名（修复前被静默丢弃）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical, _get_sxtwl
from tongshu.engines.heluo.timeline_yun import compute_liushi, compute_dayun_liyao
from tongshu.engines.heluo import yi_interpreter as yi
from tongshu.engines.heluo import guajie as gj

# 纪晓岚 Golden Case：甲辰 辛未 丙戌 甲午 午时 男
BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]


def _calc():
    return HeluoCanonical().calculate(BAZI, gender="male", birth_hour="午", era="zhong")


class TestLazyLiuShi(unittest.TestCase):
    """① 流时卦按需化"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.yearly = cls.res.timeline.yearly_hexagrams

    def test_days_carry_flip_index_not_hours(self):
        """日段应带 flip_index，且不再预挂 hours（80,352 条全量载荷的来源）"""
        segs = [d for y in self.yearly for m in y["months"] for d in m["days"]]
        self.assertEqual(len(segs), 6 * len([m for y in self.yearly for m in y["months"]]))
        for d in segs:
            self.assertIn("flip_index", d)
            self.assertNotIn("hours", d, "流时卦应按需现算，不得预展开")

    def test_lazy_hours_reproduces_full_12(self):
        """按 flip_index 现算，须得 12 个时辰（旧预展开的同源结果）"""
        for y in self.yearly[:5]:
            for m in y["months"][:2]:
                for d in m["days"]:
                    hours = compute_liushi(d["lines"], d["flip_index"]).hours
                    self.assertEqual(len(hours), 12, (y["year"], m["month"], d["segment"]))
                    self.assertEqual([h["hour"] for h in hours], list(range(1, 13)))

    def test_flip_index_is_single_line_diff_vs_month(self):
        """flip_index 必须是日段相对月卦唯一变动的爻，否则按需路径无从重建"""
        for y in self.yearly:
            for m in y["months"]:
                ml = m["lines"]
                for d in m["days"]:
                    diffs = [k for k in range(6)
                             if len(d["lines"]) > k and len(ml) > k and d["lines"][k] != ml[k]]
                    if len(diffs) == 1:
                        self.assertEqual(d["flip_index"], diffs[0])

    def test_guajie_on_demand_hours_matches(self):
        """guajie 按 target_hour 现算，12 时辰全部可定位"""
        out = gj.build_guajie_from_result(
            self.res, bazi=BAZI, target_year=2026, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertEqual(out["liushi_hexagram"], "井")
        self.assertEqual(out["liuri_hexagram"], "升")
        self.assertEqual(out["liuyue_hexagram"], "蛊")
        self.assertEqual(out["liunian_hexagram"], "困")

    def test_guajie_all_twelve_hours_resolve(self):
        for h in range(1, 13):
            out = gj.build_guajie_from_result(
                self.res, bazi=BAZI, target_year=2026, target_month=6,
                target_day=15, target_hour=h,
            )
            self.assertTrue(out["liushi_hexagram"], f"{h} 时未定位")
            self.assertTrue(out["liushi_yao"], f"{h} 时无动爻判词")

    def test_omitting_target_hour_yields_no_liushi(self):
        out = gj.build_guajie_from_result(
            self.res, bazi=BAZI, target_year=2026, target_month=6, target_day=15,
        )
        self.assertFalse(out["liushi_hexagram"])
        self.assertTrue(out["liuri_hexagram"], "不传时辰时流日仍应定位")


class TestGuajieToDictHexagrams(unittest.TestCase):
    """to_dict() 补发三个应期卦名（修复前只发 _yao，卦名被静默丢弃）"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.out = gj.build_guajie_from_result(
            cls.res, bazi=BAZI, target_year=2026, target_month=6,
            target_day=15, target_hour=7,
        )

    def test_all_four_hexagram_keys_present(self):
        for k in ("liunian_hexagram", "liuyue_hexagram",
                  "liuri_hexagram", "liushi_hexagram"):
            self.assertIn(k, self.out, f"{k} 未被 to_dict 发出")
            self.assertTrue(self.out[k], f"{k} 为空")

    def test_yao_keys_still_present(self):
        """既有键不得受影响"""
        for k in ("liunian_yao", "liuyue_yao", "liuri_yao", "liushi_yao"):
            self.assertIn(k, self.out)
            self.assertIsInstance(self.out[k], dict)


class TestInterpretShallowCopy(unittest.TestCase):
    """② interpret_all_liunian 顶层浅拷贝"""

    def test_returns_new_list_and_leaves_input_untouched(self):
        res = _calc()
        # 取真实条目、剥掉已回填的 yi_* 键，模拟"解释前"的输入
        probe = [{k: v for k, v in e.items() if k not in ("yi_signal", "yi_interpretation")}
                 for e in res.timeline.yearly_hexagrams]
        self.assertTrue(probe)
        before = {id(e) for e in probe}

        out = yi.interpret_all_liunian(probe, yuan_tang_index=0, yuan_tang_nature="阳")

        self.assertIsNot(out, probe, "应返回新列表")
        self.assertEqual(len(out), len(probe))
        self.assertFalse(before & {id(e) for e in out}, "顶层元素应为新对象")
        for a, b in zip(probe, out):
            self.assertNotIn("yi_signal", a, "原列表不得被写入")
            self.assertIn("yi_signal", b)
            self.assertIn("yi_interpretation", b)
            # 子树按引用共享（这正是省掉 deepcopy 的前提）
            self.assertIs(a["lines"], b["lines"])
            self.assertIs(a["months"], b["months"])


class TestSxtwlLazySingleton(unittest.TestCase):
    """③ sxtwl 惰性单例"""

    def test_missing_sxtwl_resolved_once(self):
        """缺依赖时不得反复走 import 机制（旧实现 1,116 次 ≈ 206 ms）"""
        import tongshu.engines.heluo.canonical as cn
        saved = (cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache)
        try:
            cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache = None, False, {}
            for _ in range(50):
                cn._jie_datetime_for_lunar_month(2026, 6)
            self.assertTrue(cn._SXTWL_FAILED, "缺 sxtwl 时应记住失败")
            self.assertIn(2026, cn._jie_cache, "失败后仍应写缓存，不重复试探 import")
            self.assertEqual(cn._jie_cache[2026], {})
        finally:
            cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache = saved

    def test_jie_cache_reused_across_months(self):
        """同一年 12 个月只应触发一次计算"""
        import tongshu.engines.heluo.canonical as cn
        saved = (cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache)
        calls = []
        try:
            cn._jie_cache = {2027: {}}
            real = cn._compute_year_jie

            def spy(year, sxtwl=None):
                calls.append(year)
                return real(year, sxtwl)

            cn._compute_year_jie = spy
            for m in range(1, 13):
                cn._jie_datetime_for_lunar_month(2027, m)
            self.assertEqual(calls, [], "命中缓存时不应重算")
        finally:
            cn._compute_year_jie = saved[0] and getattr(cn, "_compute_year_jie", None) or real
            cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache = saved


class TestDayunAndSegmentLookup(unittest.TestCase):
    """④ 大运换算提出循环 + 流年段游标查找口径不变"""

    def test_dayun_walk_hexagram_constant_per_segment(self):
        """爻位值运：卦不变，只走爻 → 每段 6 步同卦名"""
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual(len(d.sequence), 12)
        self.assertEqual(len({e.hexagram_name for e in d.sequence[:6]}), 1)
        self.assertEqual(len({e.hexagram_name for e in d.sequence[6:]}), 1)
        self.assertNotEqual(d.sequence[0].hexagram_name, d.sequence[6].hexagram_name)

    def test_dayun_segments_contiguous_and_ordered(self):
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual(d.sequence[0].age_start, 1)
        for a, b in zip(d.sequence, d.sequence[1:]):
            self.assertEqual(b.age_start, a.age_end + 1, "大运段应首尾相接")

    def test_dayun_line_index_walks_upward_from_yuantang(self):
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual([e.line_index for e in d.sequence[:6]], [0, 1, 2, 3, 4, 5])
        self.assertEqual([e.line_index for e in d.sequence[6:]], [2, 3, 4, 5, 0, 1])

    def test_liunian_years_match_dayun_coverage(self):
        """游标查找口径：流年应恰好覆盖大运全程，不多不少"""
        res = _calc()
        yearly = res.timeline.yearly_hexagrams
        dayun = res.timeline.qi_phase["dayun"]
        self.assertEqual([y["age"] for y in yearly],
                         list(range(dayun[0]["age_start"], dayun[-1]["age_end"] + 1)))


if __name__ == "__main__":
    unittest.main()
